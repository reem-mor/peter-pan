"""PETER PAN OS — the operations console for the AI system itself.

Monitors what the *agents* are doing: token usage and cost per agent,
recent runs, and heuristic improvement tips. The same idea as an APM
dashboard, pointed at the LLM layer instead of the app layer.
"""

from __future__ import annotations

from typing import Literal

from fastapi import FastAPI, Query

from peterpan.config import Settings
from peterpan.usage import aggregate, budget_status, load_usage, tips, window

app = FastAPI(title="peter-pan-os")
settings = Settings()


@app.get("/healthz")
def healthz() -> dict[str, str]:
    return {"service": "peter-pan-os", "status": "ok", "env": settings.env.value}


@app.get("/os/usage")
def usage_route(
    hours: float | None = Query(default=None, gt=0),
    by: Literal["agent", "model", "service"] = "agent",
) -> dict[str, dict[str, float]]:
    return aggregate(window(load_usage(settings.usage_log_path), hours), by=by)


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
