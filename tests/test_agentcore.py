"""AgentCore adapter — success path + honest local-fallback labeling."""

from __future__ import annotations

from datetime import UTC, datetime

import pytest

from peterpan.agentcore import AgentCoreError
from peterpan.config import Settings
from peterpan.schemas import Alert, IncidentStory, ProviderReport, Severity
from peterpan.services.agent import build_story


def _alert() -> Alert:
    return Alert(
        id="ac-1",
        source="grafana",
        title="checkout OOMKilled",
        description="pod restarted twice",
        severity=Severity.P1,
        received_at=datetime.now(UTC),
    )


def test_agentcore_success_labels_agent_provider(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import peterpan.agentcore as ac
    import peterpan.services.agent as agent_mod

    remote = IncidentStory(
        alert=_alert(),
        what_changed="remote",
        probable_cause="resource_exhaustion",
        confidence=0.7,
        evidence=[],
        repair_options=["roll pods"],
        providers=ProviderReport(llm="bedrock", agent_provider="agentcore"),
    )

    monkeypatch.setattr(ac, "invoke_story", lambda *_a, **_k: remote)
    monkeypatch.setattr(
        agent_mod,
        "settings",
        Settings(
            agent_provider="agentcore",
            agentcore_runtime_arn="arn:aws:bedrock-agentcore:us-east-1:123:runtime/demo",
        ),
    )
    story = build_story(_alert())
    assert story.providers.agent_provider == "agentcore"
    assert story.probable_cause == "resource_exhaustion"


def test_agentcore_failure_falls_back_local_labeled(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import peterpan.agentcore as ac
    import peterpan.services.agent as agent_mod

    def boom(*_a: object, **_k: object) -> IncidentStory:
        raise AgentCoreError("simulated timeout")

    monkeypatch.setattr(ac, "invoke_story", boom)
    monkeypatch.setattr(
        agent_mod,
        "settings",
        Settings(
            agent_provider="agentcore",
            agentcore_runtime_arn="arn:aws:bedrock-agentcore:us-east-1:123:runtime/demo",
            llm="off",
        ),
    )
    story = build_story(_alert())
    assert story.providers.agent_provider == "local-fallback"
    assert story.providers.llm in {"off", "deterministic-fallback"}
    assert story.confidence < 1.0


def test_invoke_story_requires_arn() -> None:
    from peterpan.agentcore import invoke_story

    with pytest.raises(AgentCoreError, match="RUNTIME_ARN"):
        invoke_story(_alert(), Settings(agent_provider="agentcore"))
