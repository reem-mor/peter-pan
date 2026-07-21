"""Bedrock provider path — all mocked, no boto3/network required.

Same invariants as the anthropic path: metered via log_usage, validated
draft, confidence clamped, ANY failure -> LlmSynthesisError so callers fall
back to the deterministic story.
"""

from __future__ import annotations

import json
import sys
import types
from datetime import UTC, datetime

import pytest

from peterpan.config import Settings
from peterpan.llm import LlmSynthesisError, resolve_model, synthesize
from peterpan.schemas import Alert, Prediction, RagResult, Severity
from peterpan.usage import load_usage


def make_alert() -> Alert:
    return Alert(
        id="br-1",
        source="grafana",
        title="checkout OOMKilled",
        severity=Severity.P2,
        received_at=datetime.now(UTC),
    )


def make_prediction() -> Prediction:
    return Prediction(incident_class="resource_exhaustion", severity=Severity.P1, confidence=0.75)


def make_rag() -> RagResult:
    return RagResult(query="q", matches=[], insight="no matches")


def valid_draft_json() -> str:
    return json.dumps(
        {
            "what_changed": "OOM kills on checkout pods",
            "probable_cause": "resource_exhaustion",
            "confidence": 0.95,  # gets clamped to 0.9 downstream
            "evidence": [
                {
                    "kind": "metric",
                    "summary": "classified as resource_exhaustion at P1",
                    "source": "predictor:/predict",
                    "confidence": 0.7,
                }
            ],
            "repair_options": ["raise memory limit"],
        }
    )


def install_fake_boto3(monkeypatch: pytest.MonkeyPatch, converse: object) -> dict[str, object]:
    """Fake boto3 whose bedrock-runtime client uses `converse`; records calls."""
    seen: dict[str, object] = {}

    class _Client:
        def __init__(self, service: str, region_name: str | None = None) -> None:
            seen["service"] = service
            seen["region"] = region_name

        def converse(self, **kwargs: object) -> object:
            seen["kwargs"] = kwargs
            return converse(**kwargs) if callable(converse) else converse

    fake = types.ModuleType("boto3")
    fake.client = _Client  # type: ignore[attr-defined]
    monkeypatch.setitem(sys.modules, "boto3", fake)
    return seen


def bedrock_response(text: str) -> dict[str, object]:
    return {
        "output": {"message": {"content": [{"text": text}]}},
        "usage": {"inputTokens": 42, "outputTokens": 17},
    }


def test_resolve_model_switches_on_provider() -> None:
    bedrock = Settings(llm="bedrock")
    assert resolve_model(bedrock) == bedrock.bedrock_model_id
    anthropic = Settings(llm="anthropic")
    assert resolve_model(anthropic) == anthropic.anthropic_model


def test_bedrock_synthesize_returns_story_and_meters(
    monkeypatch: pytest.MonkeyPatch, tmp_path: object
) -> None:
    import peterpan.cache as cache_mod

    seen = install_fake_boto3(monkeypatch, bedrock_response(valid_draft_json()))
    usage_log = tmp_path / "usage.jsonl"  # type: ignore[operator]
    prompt_log = tmp_path / "prompt_log.jsonl"  # type: ignore[operator]
    settings = Settings(
        llm="bedrock",
        usage_log_path=str(usage_log),
        prompt_log_path=str(prompt_log),
    )

    story = synthesize(make_alert(), make_prediction(), make_rag(), settings)

    assert story.probable_cause == "resource_exhaustion"
    assert story.confidence <= 0.9  # never certainty, clamped from 0.95
    assert seen["service"] == "bedrock-runtime"
    assert seen["kwargs"]["modelId"] == settings.bedrock_model_id  # type: ignore[index]

    events = load_usage(str(usage_log))
    assert len(events) == 1
    assert events[0].model == settings.bedrock_model_id
    assert events[0].input_tokens == 42
    assert events[0].cost_usd > 0

    cache_mod.reset_backend()


def test_bedrock_api_failure_becomes_synthesis_error(
    monkeypatch: pytest.MonkeyPatch, tmp_path: object
) -> None:
    def boom(**kwargs: object) -> object:
        raise ConnectionError("bedrock down")

    install_fake_boto3(monkeypatch, boom)
    settings = Settings(llm="bedrock", usage_log_path=str(tmp_path) + "/u.jsonl")  # type: ignore[operator]
    with pytest.raises(LlmSynthesisError, match="bedrock API failure"):
        synthesize(make_alert(), make_prediction(), make_rag(), settings)


def test_bedrock_without_boto3_becomes_synthesis_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setitem(sys.modules, "boto3", None)
    settings = Settings(llm="bedrock")
    with pytest.raises(LlmSynthesisError, match="boto3 not installed"):
        synthesize(make_alert(), make_prediction(), make_rag(), settings)


def test_build_story_bedrock_failure_falls_back_deterministic(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """PP_LLM=bedrock + failing LLM path -> deterministic story, no crash —
    the same fail-safe contract the anthropic path has."""
    import peterpan.llm as llm_mod
    import peterpan.services.agent as agent_mod
    from peterpan.services.agent import build_story

    def boom(*args: object, **kwargs: object) -> object:
        raise LlmSynthesisError("simulated bedrock failure")

    monkeypatch.setattr(llm_mod, "synthesize", boom)
    monkeypatch.setattr(agent_mod, "settings", Settings(llm="bedrock"))
    story = build_story(make_alert())
    assert story.probable_cause  # deterministic path produced a story
    assert story.confidence < 1.0
