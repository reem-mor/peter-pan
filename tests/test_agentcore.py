"""AgentCore adapter — success path + honest local-fallback labeling."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from types import SimpleNamespace

import pytest

from peterpan.agentcore import (
    AgentCoreError,
    _parse_story,
    _payload,
    _session_id,
    invoke_story,
)
from peterpan.config import Settings
from peterpan.schemas import Alert, Evidence, IncidentStory, ProviderReport, Severity
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


def _story_dict(alert: Alert | None = None) -> dict:
    a = alert or _alert()
    return {
        "alert": a.model_dump(mode="json"),
        "what_changed": "remote",
        "probable_cause": "resource_exhaustion",
        "confidence": 0.7,
        "evidence": [
            {
                "kind": "metric",
                "summary": "classified",
                "source": "predictor:/predict",
                "confidence": 0.7,
            }
        ],
        "repair_options": ["roll pods"],
        "providers": {
            "llm": "bedrock",
            "llm_fallback": False,
            "rag_backend": "lexical",
            "rag_fallback": False,
            "rag_fallback_reason": "",
            "predictor": "floor",
            "predictor_model_version": "",
            "agent_provider": "local",
        },
    }


def test_session_id_meets_agentcore_minimum() -> None:
    sid = _session_id(_alert())
    assert len(sid) >= 33
    assert len(sid) <= 64
    assert sid.startswith("pp-ac-1-")


def test_payload_embeds_alert_json() -> None:
    raw = json.loads(_payload(_alert()).decode("utf-8"))
    assert "Investigate alert ac-1" in raw["input"]["prompt"]
    assert raw["input"]["alert"]["id"] == "ac-1"


def test_parse_story_flat_and_wrappers() -> None:
    alert = _alert()
    flat = _parse_story(json.dumps(_story_dict(alert)), alert)
    assert flat.providers.agent_provider == "agentcore"
    assert flat.probable_cause == "resource_exhaustion"

    wrapped = _parse_story(
        json.dumps({"story": _story_dict(alert)}).encode("utf-8"),
        alert,
    )
    assert wrapped.providers.agent_provider == "agentcore"

    nested_msg = {
        "output": {"message": json.dumps(_story_dict(alert))},
    }
    from_msg = _parse_story(json.dumps(nested_msg), alert)
    assert from_msg.alert.id == "ac-1"

    # Missing alert key is filled from the request alert.
    body = _story_dict(alert)
    del body["alert"]
    filled = _parse_story(json.dumps({"result": body}), alert)
    assert filled.alert.id == alert.id
    # Remote "off" llm is rewritten to bedrock for AgentCore path.
    body2 = _story_dict(alert)
    body2["providers"]["llm"] = "off"
    rewritten = _parse_story(json.dumps(body2), alert)
    assert rewritten.providers.llm == "bedrock"


def test_invoke_story_requires_arn() -> None:
    with pytest.raises(AgentCoreError, match="RUNTIME_ARN"):
        invoke_story(_alert(), Settings(agent_provider="agentcore"))


def test_invoke_story_without_boto3(monkeypatch: pytest.MonkeyPatch) -> None:
    import builtins

    real_import = builtins.__import__

    def fake_import(name: str, *args: object, **kwargs: object):  # type: ignore[no-untyped-def]
        if name == "boto3":
            raise ImportError("simulated missing boto3")
        return real_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", fake_import)
    with pytest.raises(AgentCoreError, match="boto3 not installed"):
        invoke_story(
            _alert(),
            Settings(
                agent_provider="agentcore",
                agentcore_runtime_arn="arn:aws:bedrock-agentcore:us-east-1:123:runtime/demo",
            ),
        )


def test_invoke_story_success_and_sdk_failures(monkeypatch: pytest.MonkeyPatch) -> None:
    alert = _alert()
    body = json.dumps(_story_dict(alert)).encode("utf-8")

    class _Stream:
        def __init__(self, data: bytes) -> None:
            self._data = data

        def read(self) -> bytes:
            return self._data

    class _ClientOk:
        def invoke_agent_runtime(self, **_kwargs: object) -> dict:
            return {"response": _Stream(body)}

    class _ClientMissing:
        def invoke_agent_runtime(self, **_kwargs: object) -> dict:
            return {}

    class _ClientBoom:
        def invoke_agent_runtime(self, **_kwargs: object) -> dict:
            raise RuntimeError("timeout")

    fake_boto3 = SimpleNamespace(client=lambda *_a, **_k: _ClientOk())
    monkeypatch.setitem(__import__("sys").modules, "boto3", fake_boto3)
    story = invoke_story(
        alert,
        Settings(
            agent_provider="agentcore",
            agentcore_runtime_arn="arn:aws:bedrock-agentcore:us-east-1:123:runtime/demo",
        ),
    )
    assert story.providers.agent_provider == "agentcore"
    assert story.evidence and isinstance(story.evidence[0], Evidence)

    fake_boto3.client = lambda *_a, **_k: _ClientMissing()
    with pytest.raises(AgentCoreError, match="missing body"):
        invoke_story(
            alert,
            Settings(
                agent_provider="agentcore",
                agentcore_runtime_arn="arn:aws:bedrock-agentcore:us-east-1:123:runtime/demo",
            ),
        )

    fake_boto3.client = lambda *_a, **_k: _ClientBoom()
    with pytest.raises(AgentCoreError, match="invoke failed"):
        invoke_story(
            alert,
            Settings(
                agent_provider="agentcore",
                agentcore_runtime_arn="arn:aws:bedrock-agentcore:us-east-1:123:runtime/demo",
            ),
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
