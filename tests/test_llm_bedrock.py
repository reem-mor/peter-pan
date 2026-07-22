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


@pytest.mark.parametrize(
    "response",
    [
        {},  # output missing entirely
        {"output": {"message": {"content": [{"text": "{}"}]}}},  # usage missing
        {
            "output": {"message": {"content": [{"text": "{}"}]}},
            "usage": {"inputTokens": "not-a-number", "outputTokens": 1},
        },
        {
            "output": {"message": {"content": [42]}},  # non-dict content block
            "usage": {"inputTokens": 1, "outputTokens": 1},
        },
    ],
    ids=["output-missing", "usage-missing", "non-numeric-tokens", "non-dict-block"],
)
def test_bedrock_malformed_response_becomes_synthesis_error(
    monkeypatch: pytest.MonkeyPatch, tmp_path: object, response: dict[str, object]
) -> None:
    """A Converse response with a surprising shape must fail the LLM path as
    LlmSynthesisError (deterministic fallback), never escape as a raw
    KeyError/TypeError/ValueError that 500s past build_story's except."""
    import peterpan.cache as cache_mod

    monkeypatch.delenv("PP_REDIS_URL", raising=False)
    cache_mod.reset_backend()
    install_fake_boto3(monkeypatch, response)
    settings = Settings(llm="bedrock", usage_log_path=str(tmp_path) + "/u.jsonl")  # type: ignore[operator]
    with pytest.raises(LlmSynthesisError, match="bedrock response parse failure"):
        synthesize(make_alert(), make_prediction(), make_rag(), settings)
    cache_mod.reset_backend()


def test_synthesize_with_llm_off_never_touches_a_provider(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """PP_LLM=off is rejected by explicit dispatch before any SDK import —
    a direct caller with an ambient key must not trigger a priced call."""
    import peterpan.cache as cache_mod

    monkeypatch.delenv("PP_REDIS_URL", raising=False)
    cache_mod.reset_backend()
    monkeypatch.setitem(sys.modules, "boto3", None)
    monkeypatch.setitem(sys.modules, "anthropic", None)
    settings = Settings(llm="off", PP_ANTHROPIC_API_KEY="ambient-key-not-real")
    with pytest.raises(LlmSynthesisError, match="does not enable LLM synthesis"):
        synthesize(make_alert(), make_prediction(), make_rag(), settings)
    cache_mod.reset_backend()


def test_metering_failure_discards_story(monkeypatch: pytest.MonkeyPatch, tmp_path: object) -> None:
    """Invariant 6: metering is load-bearing. A completion whose usage row
    cannot be written is discarded via LlmSynthesisError (caller falls back),
    not shipped unmetered."""
    import peterpan.cache as cache_mod
    import peterpan.llm as llm_mod

    monkeypatch.delenv("PP_REDIS_URL", raising=False)
    cache_mod.reset_backend()
    install_fake_boto3(monkeypatch, bedrock_response(valid_draft_json()))

    def boom(*args: object, **kwargs: object) -> None:
        raise OSError("usage volume unwritable")

    monkeypatch.setattr(llm_mod, "log_usage", boom)
    settings = Settings(
        llm="bedrock",
        usage_log_path=str(tmp_path) + "/u.jsonl",  # type: ignore[operator]
        prompt_log_path=str(tmp_path) + "/p.jsonl",  # type: ignore[operator]
    )
    with pytest.raises(LlmSynthesisError, match="usage metering failed"):
        synthesize(make_alert(), make_prediction(), make_rag(), settings)

    # §6.6: the prompt-log row is recorded before the metering guard, so the
    # completed call keeps its trace trail even though the story is discarded.
    from pathlib import Path

    prompt_rows = Path(str(tmp_path) + "/p.jsonl").read_text(encoding="utf-8").splitlines()
    assert len(prompt_rows) == 1
    cache_mod.reset_backend()


def test_invalid_completion_is_not_cached(
    monkeypatch: pytest.MonkeyPatch, tmp_path: object
) -> None:
    """A completion that fails floor validation must fail on every call —
    never be replayed from the 24h cache (llm.py caches validated-only)."""
    import peterpan.cache as cache_mod

    monkeypatch.delenv("PP_REDIS_URL", raising=False)
    cache_mod.reset_backend()

    fabricated = json.dumps(
        {
            "what_changed": "OOM kills on checkout pods",
            "probable_cause": "resource_exhaustion",
            "confidence": 0.8,
            "evidence": [
                {
                    "kind": "runbook",
                    "summary": "x",
                    "source": "knowledge/made-up.md",  # not in the allowlist
                    "confidence": 0.5,
                }
            ],
            "repair_options": ["raise memory limit"],
        }
    )
    calls = {"n": 0}

    def conv(**kwargs: object) -> object:
        calls["n"] += 1
        return bedrock_response(fabricated)

    install_fake_boto3(monkeypatch, conv)
    settings = Settings(
        llm="bedrock",
        usage_log_path=str(tmp_path) + "/u.jsonl",  # type: ignore[operator]
        prompt_log_path=str(tmp_path) + "/p.jsonl",  # type: ignore[operator]
    )
    for _ in range(2):
        with pytest.raises(LlmSynthesisError, match="fabricated"):
            synthesize(make_alert(), make_prediction(), make_rag(), settings)
    assert calls["n"] == 2  # second call hit the API again, not the cache
    cache_mod.reset_backend()


def test_extract_json_payload_strips_markdown_fence() -> None:
    from peterpan.llm import _extract_json_payload

    inner = '{"what_changed":"x","probable_cause":"resource_exhaustion"}'
    assert _extract_json_payload(f"```json\n{inner}\n```") == inner
    assert _extract_json_payload(f"Here you go:\n{inner}\nThanks") == inner


def test_evidence_confidence_one_is_clamped_not_rejected(
    monkeypatch: pytest.MonkeyPatch, tmp_path: object
) -> None:
    """Models often emit evidence.confidence=1.0; clamp instead of full fallback."""
    import peterpan.cache as cache_mod

    monkeypatch.delenv("PP_REDIS_URL", raising=False)
    cache_mod.reset_backend()
    draft = json.dumps(
        {
            "what_changed": "OOM kills on checkout pods",
            "probable_cause": "resource_exhaustion",
            "confidence": 0.8,
            "evidence": [
                {
                    "kind": "metric",
                    "summary": "classified as resource_exhaustion at P1",
                    "source": "predictor:/predict",
                    "confidence": 1.0,
                },
                {
                    "kind": "alert",
                    "summary": "checkout OOMKilled",
                    "source": "alert:grafana",
                    "confidence": 0.6,
                },
            ],
            "repair_options": ["raise memory limit"],
        }
    )
    install_fake_boto3(monkeypatch, bedrock_response(draft))
    settings = Settings(
        llm="bedrock",
        usage_log_path=str(tmp_path) + "/u.jsonl",  # type: ignore[operator]
        prompt_log_path=str(tmp_path) + "/p.jsonl",  # type: ignore[operator]
    )
    story = synthesize(make_alert(), make_prediction(), make_rag(), settings)
    assert all(e.confidence < 1.0 for e in story.evidence)
    assert max(e.confidence for e in story.evidence) == 0.99
    cache_mod.reset_backend()


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
