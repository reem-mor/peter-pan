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
from fastapi import FastAPI, Query
from fastapi.responses import HTMLResponse, JSONResponse
from pydantic import BaseModel, Field

from peterpan.config import Settings
from peterpan.usage import aggregate, budget_status, load_usage, timeseries, tips, window

logger = logging.getLogger(__name__)

app = FastAPI(title="peter-pan-os")
settings = Settings()

# Self-contained dashboard page, kept next to the Streamlit UI. Resolved
# relative to CWD like `usage_log_path`, so it works from the repo root and
# inside the container image.
DASHBOARD_PATH = Path("ui/os_dashboard.html")

_HEALTH_TIMEOUT_S = 1.5


@app.get("/healthz")
def healthz() -> dict[str, str]:
    return {"service": "peter-pan-os", "status": "ok", "env": settings.env.value}


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
    return {
        "service": settings.service_name,
        "env": settings.env.value,
        "llm": settings.llm.value,
        "model": settings.anthropic_model,
        "rag_backend": settings.rag_backend.value,
        "predictor": settings.predictor.value,
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


@app.get("/os/dashboard", response_model=None)
def dashboard_route() -> HTMLResponse | JSONResponse:
    """Serve the self-contained monitoring dashboard."""
    if not DASHBOARD_PATH.exists():
        return JSONResponse(
            status_code=404,
            content={"error": f"dashboard file not found at {DASHBOARD_PATH}"},
        )
    return HTMLResponse(DASHBOARD_PATH.read_text(encoding="utf-8"))
