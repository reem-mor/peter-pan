"""LLM synthesis guard-rails — all mocked, no network in tests."""

from __future__ import annotations

from datetime import UTC, datetime

import pytest

from peterpan.config import Settings
from peterpan.llm import LlmSynthesisError, _LlmStoryDraft, _validate_draft, load_system_prompt
from peterpan.schemas import Alert, Evidence, Prediction, Severity
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
