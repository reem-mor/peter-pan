"""Agent service — builds the IncidentStory and proposes gated actions.

MVP: a deterministic planner→evidence→synthesis pipeline with a bounded step
budget, shaped exactly like the LangGraph graph that replaces it (planner
node → tool node → synthesiser node). The ActionPreview gate is the product's
core safety property: HIGH-risk actions are proposed, never executed, until a
human approves.
"""

from __future__ import annotations

import asyncio
import json
from collections.abc import AsyncIterator
from datetime import UTC, datetime
from typing import Literal

from fastapi import FastAPI
from fastapi.responses import JSONResponse, StreamingResponse
from pydantic import BaseModel

from peterpan.config import LlmProvider, Settings
from peterpan.schemas import (
    ActionPreview,
    ActionRisk,
    Alert,
    DashboardSpec,
    Evidence,
    IncidentStory,
    Severity,
)
from peterpan.services.predictor import predict
from peterpan.services.rag import search

app = FastAPI(title="peter-pan-agent")
settings = Settings()

MAX_STEPS = 6  # bounded loop — the agent can never run away

# Synthetic delay between SSE frames so the demo "thinking" pace is visible
# without any live LLM latency to wait on (CONTRACTS.md §5).
_STREAM_STEP_DELAY_S = 0.05

# Fixture-first alert catalog the SSE demo endpoint resolves `alert_id`
# against. No live alert store exists yet (WS9 owns that); this is enough
# surface for the demo app to drive the stream deterministically. Timestamp
# is fixed so responses stay byte-for-byte reproducible across runs.
_DEMO_RECEIVED_AT = datetime(2026, 1, 1, tzinfo=UTC)

DEMO_ALERTS: dict[str, Alert] = {
    "demo-oom": Alert(
        id="demo-oom",
        source="grafana",
        title="checkout OOMKilled",
        description="pod restarted twice, memory at limit",
        severity=Severity.P1,
        received_at=_DEMO_RECEIVED_AT,
    ),
    "demo-latency": Alert(
        id="demo-latency",
        source="pager",
        title="timeout on payments API",
        description="p99 latency breached SLO after the 14:00 deploy",
        severity=Severity.P2,
        received_at=_DEMO_RECEIVED_AT,
    ),
    "demo-5xx": Alert(
        id="demo-5xx",
        source="grafana",
        title="checkout returning 5xx",
        description="error rate spike correlates with the canary rollout",
        severity=Severity.P2,
        received_at=_DEMO_RECEIVED_AT,
    ),
}


def search_query(alert: Alert) -> str:
    """Build the RAG query from an alert. search() rejects blank queries, and
    title/description are attacker-controllable and may be empty/whitespace —
    fall back to id+source (always present) so the pipeline never 500s."""
    query = f"{alert.title} {alert.description}".strip()
    return query if query else f"{alert.id} {alert.source}"


def build_story(alert: Alert) -> IncidentStory:
    """Planner → tools → synthesis. Deterministic by default; PP_LLM=anthropic
    upgrades the synthesis step to Claude, guarded by peterpan.llm's invariant
    checks and falling back here on ANY failure (fixture-first rule)."""
    steps = 0

    # Step 1: classify (deterministic floor — its verdict is final).
    prediction = predict(alert)
    steps += 1

    # Step 2: retrieve context (runbooks, past incidents).
    rag = search(search_query(alert), top_k=3)
    steps += 1

    # Step 3: synthesize — LLM if opted in, deterministic otherwise/on failure.
    if settings.llm is LlmProvider.ANTHROPIC:
        from peterpan.llm import LlmSynthesisError, synthesize

        steps += 1
        try:
            story = synthesize(alert, prediction, rag, settings)
            if steps > MAX_STEPS:
                raise RuntimeError("loop budget invariant violated")
            return story
        except LlmSynthesisError:
            pass  # fall through to the deterministic synthesis below

    evidence: list[Evidence] = [
        Evidence(
            kind="metric",
            summary=f"classified as {prediction.incident_class} at {prediction.severity}",
            source="predictor:/predict",
            confidence=prediction.confidence,
        ),
        *[m for m in rag.matches if m.confidence > 0],
    ]

    if steps > MAX_STEPS:  # loop budget invariant
        raise RuntimeError("loop budget invariant violated")

    return IncidentStory(
        alert=alert,
        what_changed=f"Signal '{alert.title}' from {alert.source}",
        probable_cause=prediction.incident_class,
        confidence=min(prediction.confidence, 0.9),  # never claim certainty
        evidence=evidence,
        repair_options=_repair_options(prediction.incident_class),
    )


def _repair_options(incident_class: str) -> list[str]:
    options = {
        "resource_exhaustion": ["raise memory/disk limits", "roll affected pods", "hunt the leak"],
        "connectivity": ["check network policy / DNS", "verify upstream health"],
        "latency": ["check connection pools", "review recent deploys", "scale horizontally"],
        "availability": ["roll back last deploy", "shift traffic off bad canary"],
        "security": ["rotate certificate", "verify chain with openssl"],
        "change_related": ["diff the deploy", "roll back", "feature-flag off"],
    }
    return options.get(incident_class, ["escalate to on-call with collected evidence"])


def propose_action(action: str, risk: ActionRisk) -> ActionPreview:
    """Every mutating action goes through here. In production, HIGH risk always
    requires human approval regardless of any model's confidence."""
    requires = (
        risk is ActionRisk.HIGH or not settings.actions_allowed and risk is not ActionRisk.READ_ONLY
    )
    return ActionPreview(
        action=action,
        risk=risk,
        rationale=f"proposed in env={settings.env.value}",
        requires_approval=requires,
    )


def approve(preview: ActionPreview, approver: str) -> ActionPreview:
    if not approver.strip():
        raise ValueError("approver must be identified")
    return preview.model_copy(update={"approved_by": approver, "approved_at": datetime.now(UTC)})


@app.get("/healthz")
def healthz() -> dict[str, str]:
    return {"service": "agent", "status": "ok", "env": settings.env.value}


@app.post("/story")
def story_route(alert: Alert) -> IncidentStory:
    return build_story(alert)


class DrawRequest(BaseModel):
    problem: str
    alert: Alert


@app.post("/dashboard")
def dashboard_route(body: DrawRequest) -> DashboardSpec:
    """'Draw me the problem': story pipeline + dashboard spec generation."""
    from peterpan.dashboard import build_dashboard

    story = build_story(body.alert)
    return build_dashboard(body.problem, story, settings)


class StepEvent(BaseModel):
    """One reasoning-step notification — CONTRACTS.md §5 `step` event shape."""

    name: str
    detail: str
    ts: str


class SseEvent(BaseModel):
    """Typed SSE frame envelope: one `event:`/`data:` pair (CONTRACTS.md §5).
    `data` is the already-serialized JSON payload for the named event type
    (StepEvent | Evidence | IncidentStory | the terminal done marker) — the
    envelope only shapes the wire frame, it never re-validates the payload
    (that already happened when the payload model was built)."""

    event: Literal["step", "evidence", "story", "done"]
    data: str

    def encode(self) -> str:
        return f"event: {self.event}\ndata: {self.data}\n\n"


async def _stream_story(alert: Alert) -> AsyncIterator[str]:
    """Narrate build_story()'s existing pipeline as CONTRACTS.md §5 SSE
    frames: step+ -> evidence+ -> story -> done. Calls build_story() exactly
    once — this never re-implements the classify/retrieve/synthesize logic,
    it only describes it, so PP_LLM=anthropic streams the same shape around
    the real LLM call (metered by peterpan.llm/usage as it already is)."""
    plan = [
        ("classify", "Classifying the alert against the deterministic floor."),
        ("retrieve", "Retrieving runbooks and past incidents."),
        (
            "synthesize",
            "Synthesizing the incident story via Claude."
            if settings.llm is LlmProvider.ANTHROPIC
            else "Synthesizing the incident story (deterministic).",
        ),
    ]
    for name, detail in plan:
        step = StepEvent(name=name, detail=detail, ts=datetime.now(UTC).isoformat())
        yield SseEvent(event="step", data=step.model_dump_json()).encode()
        await asyncio.sleep(_STREAM_STEP_DELAY_S)

    story = build_story(alert)

    for evidence in story.evidence:
        yield SseEvent(event="evidence", data=evidence.model_dump_json()).encode()
        await asyncio.sleep(_STREAM_STEP_DELAY_S)

    yield SseEvent(event="story", data=story.model_dump_json()).encode()
    await asyncio.sleep(_STREAM_STEP_DELAY_S)
    yield SseEvent(event="done", data=json.dumps({"status": "done"})).encode()


@app.get("/agent/stream", response_model=None)
def stream_route(alert_id: str) -> StreamingResponse | JSONResponse:
    """SSE incident-story stream (CONTRACTS.md §5) for the live demo app.
    Fixture-first: resolves against the deterministic demo catalog, so the
    default path needs zero external accounts or a live LLM."""
    alert = DEMO_ALERTS.get(alert_id)
    if alert is None:
        return JSONResponse(status_code=404, content={"error": f"unknown alert_id: {alert_id!r}"})
    return StreamingResponse(_stream_story(alert), media_type="text/event-stream")
