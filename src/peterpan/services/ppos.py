"""PETER PAN OS — the operations console for the AI system itself.

Monitors what the *agents* are doing: token usage and cost per agent,
recent runs, and heuristic improvement tips. The same idea as an APM
dashboard, pointed at the LLM layer instead of the app layer.
"""

from __future__ import annotations

from fastapi import FastAPI

from peterpan.config import Settings
from peterpan.usage import aggregate, load_usage, tips

app = FastAPI(title="peter-pan-os")
settings = Settings()


@app.get("/healthz")
def healthz() -> dict[str, str]:
    return {"service": "peter-pan-os", "status": "ok", "env": settings.env.value}


@app.get("/os/usage")
def usage_route() -> dict[str, dict[str, float]]:
    return aggregate(load_usage(settings.usage_log_path))


@app.get("/os/tips")
def tips_route() -> dict[str, list[str]]:
    return {"tips": tips(load_usage(settings.usage_log_path))}


@app.get("/os/agents")
def agents_route() -> dict[str, list[str]]:
    """Known agents this deployment runs. Extend as agents are added."""
    return {"agents": ["predictor", "rag", "guardrails", "incident-agent"]}
