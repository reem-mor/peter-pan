"""PETER PAN OS — the operations console for the AI system itself.

Monitors what the *agents* are doing: token usage and cost per agent,
recent runs, and heuristic improvement tips. The same idea as an APM
dashboard, pointed at the LLM layer instead of the app layer.
"""

from __future__ import annotations

import time
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Literal

from fastapi import FastAPI, Query, Request
from fastapi.responses import HTMLResponse, JSONResponse
from pydantic import ValidationError

from peterpan import feedback_store, scoring
from peterpan.config import Settings
from peterpan.schemas import Feedback
from peterpan.usage import aggregate, budget_status, load_usage, timeseries, tips, window

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


@app.get("/os/dashboard", response_model=None)
def dashboard_route() -> HTMLResponse | JSONResponse:
    """Serve the self-contained monitoring dashboard."""
    if not DASHBOARD_PATH.exists():
        return JSONResponse(
            status_code=404,
            content={"error": f"dashboard file not found at {DASHBOARD_PATH}"},
        )
    return HTMLResponse(DASHBOARD_PATH.read_text(encoding="utf-8"))


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
