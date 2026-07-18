"""LLM synthesis guard-rails — all mocked, no network in tests."""

from __future__ import annotations

from datetime import UTC, datetime

import pytest

from peterpan.config import Settings
from peterpan.llm import LlmSynthesisError, _LlmStoryDraft, _validate_draft, load_system_prompt
from peterpan.schemas import Alert, Evidence, Prediction, RagResult, Severity
from peterpan.services.agent import build_story
from peterpan.services.predictor import predict


def make_prediction() -> Prediction:
    return Prediction(incident_class="resource_exhaustion", severity=Severity.P1, confidence=0.75)


def make_draft(**overrides: object) -> _LlmStoryDraft:
    base: dict = {
        "what_changed": "OOM kills on checkout pods",
        "probable_cause": "resource_exhaustion",
        "confidence": 0.8,
        "evidence": [
            Evidence(
                kind="runbook",
                summary="raise limits",
                source="knowledge/runbooks/checkout-oom.md",
                confidence=0.4,
            )
        ],
        "repair_options": ["raise memory limit"],
    }
    base.update(overrides)
    return _LlmStoryDraft.model_validate(base)


ALLOWED = {"predictor:/predict", "knowledge/runbooks/checkout-oom.md"}


def test_versioned_system_prompt_loads_and_forbids_certainty() -> None:
    prompt = load_system_prompt()
    assert "never certain" in prompt and "forbidden" in prompt
    assert "cites its source" in prompt


def test_valid_draft_passes() -> None:
    _validate_draft(make_draft(), make_prediction(), ALLOWED)


def test_fabricated_citation_rejected() -> None:
    draft = make_draft(
        evidence=[
            Evidence(kind="runbook", summary="x", source="knowledge/made-up.md", confidence=0.5)
        ]
    )
    with pytest.raises(LlmSynthesisError, match="fabricated"):
        _validate_draft(draft, make_prediction(), ALLOWED)


def test_llm_contradicting_deterministic_class_rejected() -> None:
    draft = make_draft(probable_cause="cosmic_rays")
    with pytest.raises(LlmSynthesisError, match="contradicted"):
        _validate_draft(draft, make_prediction(), ALLOWED)


def test_story_without_evidence_rejected() -> None:
    draft = make_draft(evidence=[])
    with pytest.raises(LlmSynthesisError, match="without evidence"):
        _validate_draft(draft, make_prediction(), ALLOWED)


def test_llm_off_by_default_keeps_deterministic_path() -> None:
    assert Settings().llm.value == "off"


def test_synthesize_caches_response_and_skips_second_llm_call(
    monkeypatch: pytest.MonkeyPatch, tmp_path: object
) -> None:
    """ADR-0001 response cache wired into the one real log_usage call: a
    cache hit must skip both the anthropic API call AND the usage-log
    entry, while still returning the same validated story."""
    import json
    import sys
    import types

    import peterpan.cache as cache_mod
    from peterpan.usage import load_usage

    monkeypatch.delenv("PP_REDIS_URL", raising=False)
    cache_mod.reset_backend()

    calls = {"n": 0}
    draft_json = json.dumps(
        {
            "what_changed": "OOM kills on checkout pods",
            "probable_cause": "resource_exhaustion",
            "confidence": 0.7,
            "evidence": [
                {
                    "kind": "metric",
                    "summary": "classified as resource_exhaustion",
                    "source": "predictor:/predict",
                    "confidence": 0.5,
                }
            ],
            "repair_options": ["raise memory limit"],
        }
    )

    class _FakeBlock:
        type = "text"
        text = draft_json

    class _FakeUsage:
        input_tokens = 10
        output_tokens = 5

    class _FakeResponse:
        content = [_FakeBlock()]
        usage = _FakeUsage()

    class _FakeMessages:
        def create(self, **kwargs: object) -> _FakeResponse:
            calls["n"] += 1
            return _FakeResponse()

    class _FakeClient:
        def __init__(self, api_key: str) -> None:
            self.messages = _FakeMessages()

    fake_anthropic = types.SimpleNamespace(Anthropic=_FakeClient)
    monkeypatch.setitem(sys.modules, "anthropic", fake_anthropic)

    usage_log = tmp_path / "usage.jsonl"  # type: ignore[operator]
    # anthropic_api_key has a validation_alias (env var name), so it must be
    # set via that alias — a plain `anthropic_api_key=` kwarg is silently
    # ignored by pydantic-settings without populate_by_name=True.
    settings = Settings(
        llm="anthropic", PP_ANTHROPIC_API_KEY="test-not-real", usage_log_path=str(usage_log)
    )
    alert = Alert(
        id="cache-1",
        source="grafana",
        title="checkout OOMKilled",
        severity=Severity.P2,
        received_at=datetime.now(UTC),
    )
    prediction = make_prediction()
    rag = RagResult(query="q", matches=[], insight="no matches")

    from peterpan.llm import synthesize

    story1 = synthesize(alert, prediction, rag, settings)
    story2 = synthesize(alert, prediction, rag, settings)

    assert calls["n"] == 1  # second call was a cache hit, no API call
    assert story1 == story2
    assert len(load_usage(str(usage_log))) == 1  # cache hit logged no cost entry
    assert cache_mod.cache_stats() == {"hits": 1, "misses": 1}

    cache_mod.reset_backend()


def test_build_story_falls_back_when_llm_fails(monkeypatch: pytest.MonkeyPatch) -> None:
    """PP_LLM=anthropic but the LLM path raises -> deterministic story, no crash."""
    import peterpan.llm as llm_mod
    import peterpan.services.agent as agent_mod

    def boom(*args: object, **kwargs: object) -> object:
        raise LlmSynthesisError("simulated API failure")

    monkeypatch.setattr(llm_mod, "synthesize", boom)
    monkeypatch.setattr(
        agent_mod, "settings", Settings(llm="anthropic", anthropic_api_key="test-not-real")
    )
    alert = Alert(
        id="fb-1",
        source="grafana",
        title="checkout OOMKilled",
        severity=Severity.P2,
        received_at=datetime.now(UTC),
    )
    story = build_story(alert)
    assert story.probable_cause == predict(alert).incident_class
    assert story.confidence < 1.0
