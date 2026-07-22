"""PETER PAN OS — the operations console for the AI system itself.

Monitors what the *agents* are doing: token usage and cost per agent,
recent runs, and heuristic improvement tips. The same idea as an APM
dashboard, pointed at the LLM layer instead of the app layer.
"""

from __future__ import annotations

import json
import logging
import time
import urllib.request
import uuid
from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, datetime
from pathlib import Path
from typing import Literal

import httpx
from fastapi import FastAPI, Query, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field, ValidationError

from peterpan import feedback_store, scoring
from peterpan.auth import install_api_auth
from peterpan.config import Settings
from peterpan.schemas import Feedback
from peterpan.usage import aggregate, budget_status, load_usage, timeseries, tips, window

logger = logging.getLogger(__name__)

app = FastAPI(title="peter-pan-os")
settings = Settings()
install_api_auth(app, settings)

_HEALTH_TIMEOUT_S = 1.5


@app.get("/healthz")
def healthz() -> dict[str, object]:
    return {
        "service": "peter-pan-os",
        "status": "ok",
        "env": settings.env.value,
        "auth_required": settings.api_token is not None,
    }


# One year. Unbounded floats (1e300, inf) overflow timedelta into a 500.
_MAX_WINDOW_HOURS = 8760


@app.get("/os/usage")
def usage_route(
    hours: float | None = Query(default=None, gt=0, le=_MAX_WINDOW_HOURS),
    by: Literal["agent", "model", "service"] = "agent",
) -> dict[str, dict[str, float]]:
    return aggregate(window(load_usage(settings.usage_log_path), hours), by=by)


@app.get("/os/usage/series")
def usage_series_route(
    hours: float = Query(default=24, gt=0, le=_MAX_WINDOW_HOURS),
    buckets: int = Query(default=48, gt=0, le=500),
) -> dict[str, object]:
    """Bucketed cost/token time series — feeds the OS dashboard charts."""
    return timeseries(load_usage(settings.usage_log_path), hours=hours, buckets=buckets)


@app.get("/os/budget")
def budget_route() -> dict[str, object]:
    """Last-24h spend vs the PP_DAILY_BUDGET_USD budget. Report-only guard."""
    return budget_status(load_usage(settings.usage_log_path), settings.daily_budget_usd)


@app.get("/os/tips")
def tips_route() -> dict[str, list[str]]:
    return {"tips": tips(load_usage(settings.usage_log_path))}


@app.get("/os/agents")
def agents_route() -> dict[str, list[str]]:
    """Known agents this deployment runs. Extend as agents are added."""
    return {"agents": ["predictor", "rag", "guardrails", "incident-agent"]}


@app.get("/os/info")
def info_route() -> dict[str, object]:
    """Deployment identity for the dashboard header — env, backends, budget.

    Config only, never secrets: values here render in a browser.
    """
    model = (
        settings.bedrock_model_id
        if settings.llm.value == "bedrock"
        else settings.anthropic_model
        if settings.llm.value == "anthropic"
        else "none"
    )
    return {
        "service": settings.service_name,
        "env": settings.env.value,
        "llm": settings.llm.value,
        "model": model,
        "rag_backend": settings.rag_backend.value,
        "rag_provider_label": (
            "standalone-pinecone" if settings.rag_backend.value == "pinecone" else "local-lexical"
        ),
        "predictor": settings.predictor.value,
        "agent_provider": "local",
        "auth_required": settings.api_token is not None,
        "daily_budget_usd": settings.daily_budget_usd,
        "repo": "https://github.com/reem-mor/peter-pan",
    }


def _probe(name: str, base_url: str) -> dict[str, object]:
    """One healthz ping. Failures are data, not exceptions — the dashboard
    renders a down service the same way an APM would. Catch everything: a
    malformed mesh URL or a garbage responder must not 500 the whole sweep.
    """
    url = f"{base_url.rstrip('/')}/healthz"
    started = time.perf_counter()
    try:
        with urllib.request.urlopen(url, timeout=_HEALTH_TIMEOUT_S) as resp:  # noqa: S310
            ok = resp.status == 200
    except Exception:  # noqa: BLE001 — failures are data here, by contract
        ok = False
    latency_ms = round((time.perf_counter() - started) * 1000, 1)
    return {
        "name": name,
        "url": base_url,
        "status": "up" if ok else "down",
        "latency_ms": latency_ms,
    }


@app.get("/os/services")
def services_route() -> dict[str, list[dict[str, object]]]:
    """Server-side health sweep of the mesh (browsers can't cross-origin poll it).

    Probes run concurrently so the sweep's wall time is one slow probe, not
    the sum — sequential probes could starve the sync-route threadpool while
    the dashboard polls every 30s.
    """
    mesh = list(settings.mesh.items())
    if not mesh:
        return {"services": []}
    with ThreadPoolExecutor(max_workers=min(8, len(mesh))) as pool:
        services = list(pool.map(lambda kv: _probe(kv[0], kv[1]), mesh))
    return {"services": services}


# --- Landing-page lead capture -------------------------------------------
# Marketing data, deliberately local to this service — not an incident-domain
# contract, so it stays out of schemas.py. Leads append to a JSONL file
# (resolved relative to CWD, like `usage_log_path`).
LEADS_PATH = Path("data/leads.jsonl")

# Deliberately simple shape check (something@domain.tld) — deterministic and
# dependency-free. Real verification belongs to the follow-up email, not here.
_LEAD_EMAIL_PATTERN = r"^[^@\s]+@[^@\s]+\.[^@\s]+$"
_LEAD_WEBHOOK_TIMEOUT_S = 2.0


class LeadRequest(BaseModel):
    """A demo request submitted from the landing page. Free-text fields are
    visitor-controlled input: stored as data, never interpreted."""

    name: str = Field(min_length=1, max_length=120)
    email: str = Field(min_length=6, max_length=254, pattern=_LEAD_EMAIL_PATTERN)
    company: str = Field(min_length=1, max_length=200)
    message: str = Field(default="", max_length=2000)


def _notify_lead_webhook(record: dict[str, object]) -> None:
    """Best-effort n8n notification, only when PP_N8N_LEAD_WEBHOOK is set.

    The lead is already on disk by the time this runs — a webhook failure is
    logged and swallowed, never surfaced to the visitor.
    """
    url = settings.n8n_lead_webhook
    if not url:
        return
    try:
        httpx.post(url, json=record, timeout=_LEAD_WEBHOOK_TIMEOUT_S)
    except Exception as exc:  # noqa: BLE001 — notification is best-effort by contract
        # Type name only — httpx exception reprs can embed the webhook URL,
        # and n8n webhook paths are secret-bearing.
        logger.warning("lead webhook notification failed: %s", type(exc).__name__)


@app.post("/leads", status_code=201)
def create_lead(lead: LeadRequest) -> dict[str, str]:
    """Store a landing-page demo request, then (optionally) notify n8n."""
    record: dict[str, object] = {
        "id": uuid.uuid4().hex,
        "received_at": datetime.now(tz=UTC).isoformat(),
        **lead.model_dump(),
    }
    LEADS_PATH.parent.mkdir(parents=True, exist_ok=True)
    with LEADS_PATH.open("a", encoding="utf-8") as f:
        f.write(json.dumps(record) + "\n")
    _notify_lead_webhook(record)
    return {"status": "stored", "id": str(record["id"])}


# --- feedback: closing the learning loop -------------------------------------

# Bounded last-N for the summary endpoint — same rationale as usage/series
# buckets: a caller can never force an unbounded response.
_MAX_SUMMARY_ENTRIES = 200


@app.post("/feedback", response_model=None, status_code=201)
async def feedback_route(request: Request) -> JSONResponse:
    """Record one operator verdict on an agent output.

    Reads the raw body first so an oversized payload (feedback text is
    attacker-controllable, same as alert text) is rejected before it's ever
    parsed into a model. `submitted_by` non-blank is enforced here, not in
    the shared Feedback schema, so this stays a route-level policy.
    """
    # Early reject on declared size — before buffering the body at all.
    declared = request.headers.get("content-length")
    if declared and declared.isdigit() and int(declared) > feedback_store.MAX_FEEDBACK_BYTES:
        return JSONResponse(
            status_code=413,
            content={
                "error": f"feedback payload exceeds {feedback_store.MAX_FEEDBACK_BYTES} bytes"
            },
        )
    raw = await request.body()
    if len(raw) > feedback_store.MAX_FEEDBACK_BYTES:
        return JSONResponse(
            status_code=413,
            content={
                "error": f"feedback payload exceeds {feedback_store.MAX_FEEDBACK_BYTES} bytes"
            },
        )
    try:
        feedback = Feedback.model_validate_json(raw)
    except ValidationError as exc:
        return JSONResponse(
            status_code=422,
            content={"error": "invalid feedback", "detail": exc.errors(include_url=False)},
        )
    if not feedback.submitted_by.strip():
        return JSONResponse(
            status_code=422,
            content={"error": "submitted_by must be non-empty"},
        )
    count = feedback_store.append_feedback(feedback, settings.feedback_log_path)
    return JSONResponse(status_code=201, content={"stored": True, "count": count})


@app.get("/feedback/summary")
def feedback_summary_route(
    limit: int = Query(default=20, gt=0, le=_MAX_SUMMARY_ENTRIES),
    trace_id: str | None = Query(default=None),
) -> dict[str, object]:
    """Counts by verdict, a bounded tail of recent entries, and a deterministic
    accuracy score (peterpan.scoring). ?trace_id= narrows to one trace's
    feedback history (e.g. every verdict recorded against one incident run)."""
    records = feedback_store.load_feedback(settings.feedback_log_path)
    if trace_id is not None:
        records = [r for r in records if r.trace_id == trace_id]
    recent = records[-limit:]
    return {
        "counts": scoring.verdict_counts(records),
        "total": len(records),
        "accuracy": round(scoring.accuracy(records), 4),
        "entries": [r.model_dump(mode="json") for r in recent],
    }
