"""Contract-level enforcement of the confidence < 1.0 invariant.

Every producer already caps at 0.9 (predictor floor values, torch cap,
min(confidence, 0.9) at story construction) — these tests pin the invariant
at the schema layer, so a future producer bug that emits certainty fails
validation instead of shipping a story that claims it.

peterpan.llm._LlmStoryDraft deliberately stays le=1.0: it is the model's
RAW draft, and a draft claiming 1.0 is clamped (min(confidence, 0.9)), not
rejected into a fallback.
"""

from __future__ import annotations

from datetime import UTC, datetime

import pytest
from pydantic import ValidationError

from peterpan.schemas import Alert, Evidence, IncidentStory, Prediction, Severity


def make_alert() -> Alert:
    return Alert(
        id="cb-1",
        source="grafana",
        title="checkout OOMKilled",
        severity=Severity.P2,
        received_at=datetime.now(UTC),
    )


def make_evidence(confidence: float) -> Evidence:
    return Evidence(
        kind="metric",
        summary="mem usage 98%",
        source="grafana:panel/42",
        confidence=confidence,
    )


def test_evidence_rejects_certainty() -> None:
    with pytest.raises(ValidationError):
        make_evidence(1.0)
    assert make_evidence(0.99).confidence == 0.99


def test_prediction_rejects_certainty() -> None:
    with pytest.raises(ValidationError):
        Prediction(incident_class="latency", severity=Severity.P3, confidence=1.0)
    ok = Prediction(incident_class="latency", severity=Severity.P3, confidence=0.9)
    assert ok.confidence == 0.9


def test_incident_story_rejects_certainty() -> None:
    kwargs = {
        "alert": make_alert(),
        "what_changed": "deploy v2.3.1 rolled out",
        "probable_cause": "resource_exhaustion",
        "evidence": [make_evidence(0.8)],
        "repair_options": ["rollback v2.3.1"],
    }
    with pytest.raises(ValidationError):
        IncidentStory(confidence=1.0, **kwargs)
    assert IncidentStory(confidence=0.9, **kwargs).confidence == 0.9
