"""Provider truthfulness — never mislabel fallback as live cloud/LLM."""

from __future__ import annotations

import json
from datetime import UTC, datetime

import pytest
from fastapi.testclient import TestClient

from peterpan.config import Settings
from peterpan.schemas import Alert, Severity
from peterpan.services.agent import app as agent_app
from peterpan.services.agent import build_story
from peterpan.services.predictor import predict, predict_full
from peterpan.services.rag import search


def _alert(title: str = "checkout OOMKilled") -> Alert:
    return Alert(
        id="truth-1",
        source="grafana",
        title=title,
        description="pod restarted twice",
        severity=Severity.P2,
        received_at=datetime.now(UTC),
    )


def test_lexical_rag_reports_backend_not_fallback() -> None:
    result = search("checkout out of memory")
    assert result.backend == "lexical"
    assert result.fallback is False
    assert result.fallback_reason == ""


def test_pinecone_failure_labels_fallback_not_pinecone(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import peterpan.services.rag as rag_mod

    monkeypatch.setattr(rag_mod, "settings", Settings(rag_backend="pinecone"))

    def boom(*_a: object, **_k: object) -> list[object]:
        raise RuntimeError("simulated pinecone outage")

    monkeypatch.setattr(rag_mod, "_search_pinecone", boom)
    result = search("checkout out of memory")
    assert result.backend == "fallback"
    assert result.fallback is True
    assert "pinecone_unavailable" in result.fallback_reason
    assert "lexical-fallback" in result.insight
    # Must not claim a successful pinecone retrieval in the insight label.
    assert "(pinecone)" not in result.insight


def test_build_story_llm_failure_sets_deterministic_fallback(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import peterpan.llm as llm_mod
    import peterpan.services.agent as agent_mod
    from peterpan.llm import LlmSynthesisError

    def boom(*_a: object, **_k: object) -> object:
        raise LlmSynthesisError("simulated API failure")

    monkeypatch.setattr(llm_mod, "synthesize", boom)
    monkeypatch.setattr(
        agent_mod,
        "settings",
        Settings(llm="anthropic", anthropic_api_key="test-not-real"),
    )
    story = build_story(_alert())
    assert story.providers.llm == "deterministic-fallback"
    assert story.providers.llm_fallback is True
    assert story.providers.agent_provider == "local"


def test_sse_synthesize_step_does_not_claim_claude_on_fallback(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import peterpan.llm as llm_mod
    import peterpan.services.agent as agent_mod
    from peterpan.llm import LlmSynthesisError

    def boom(*_a: object, **_k: object) -> object:
        raise LlmSynthesisError("simulated API failure")

    monkeypatch.setattr(llm_mod, "synthesize", boom)
    monkeypatch.setattr(
        agent_mod,
        "settings",
        Settings(llm="anthropic", anthropic_api_key="test-not-real"),
    )
    client = TestClient(agent_app)
    with client.stream("GET", "/agent/stream", params={"alert_id": "demo-oom"}) as resp:
        raw = resp.read().decode("utf-8")
    assert "via Claude" not in raw
    assert "deterministic-fallback" in raw
    done = [line for line in raw.splitlines() if line.startswith("data: {") and "providers" in line]
    assert done
    payload = json.loads(done[-1].removeprefix("data: ").strip())
    assert payload["providers"]["llm_fallback"] is True


def test_predictor_floor_mode_and_healthz() -> None:
    pred = predict(_alert())
    assert pred.mode == "floor"
    assert pred.model_version == ""
    from peterpan.services.predictor import app

    body = TestClient(app).get("/healthz").json()
    assert body["backend"] == "floor"
    assert "artifacts_present" in body


def test_predict_full_torch_fallback_mode(monkeypatch: pytest.MonkeyPatch) -> None:
    import peterpan.ml as ml_mod
    import peterpan.services.predictor as pred_mod

    def boom(*_a: object, **_k: object) -> object:
        raise ml_mod.MlPredictError("no torch")

    monkeypatch.setattr(ml_mod, "model_predict", boom)
    result = predict_full(_alert(), Settings(predictor="torch"))
    assert result.mode == "floor-fallback"
    assert result.model_version == ""
    assert pred_mod.predict(_alert()).incident_class == result.incident_class
