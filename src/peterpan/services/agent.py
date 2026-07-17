"""Agent service — builds the IncidentStory and proposes gated actions.

MVP: a deterministic planner→evidence→synthesis pipeline with a bounded step
budget, shaped exactly like the LangGraph graph that replaces it (planner
node → tool node → synthesiser node). The ActionPreview gate is the product's
core safety property: HIGH-risk actions are proposed, never executed, until a
human approves.
"""

from __future__ import annotations

from datetime import UTC, datetime

from fastapi import FastAPI

from peterpan.config import LlmProvider, Settings
from peterpan.schemas import (
    ActionPreview,
    ActionRisk,
    Alert,
    Evidence,
    IncidentStory,
)
from peterpan.services.predictor import predict
from peterpan.services.rag import search

app = FastAPI(title="peter-pan-agent")
settings = Settings()

MAX_STEPS = 6  # bounded loop — the agent can never run away


def build_story(alert: Alert) -> IncidentStory:
    """Planner → tools → synthesis. Deterministic by default; PP_LLM=anthropic
    upgrades the synthesis step to Claude, guarded by peterpan.llm's invariant
    checks and falling back here on ANY failure (fixture-first rule)."""
    steps = 0

    # Step 1: classify (deterministic floor — its verdict is final).
    prediction = predict(alert)
    steps += 1

    # Step 2: retrieve context (runbooks, past incidents).
    rag = search(f"{alert.title} {alert.description}", top_k=3)
    steps += 1

    # Step 3: synthesize — LLM if opted in, deterministic otherwise/on failure.
    if settings.llm is LlmProvider.ANTHROPIC:
        from peterpan.llm import LlmSynthesisError, synthesize

        steps += 1
        try:
            story = synthesize(alert, prediction, rag, settings)
            assert steps <= MAX_STEPS
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

    assert steps <= MAX_STEPS  # loop budget invariant

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
