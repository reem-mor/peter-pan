"""ML predictor: the model refines, the deterministic floor always wins.

Guard logic is pure code tested without torch (fake-model seam); the real
torch path is covered behind importorskip, same pattern as the langgraph
tests — CI without the `ml` extra still exercises every invariant.
"""

from __future__ import annotations

from datetime import UTC, datetime

import pytest

from peterpan.config import PredictorBackend, Settings
from peterpan.ml import MlPredictError, MlPrediction, apply_floor_guardrails
from peterpan.schemas import Alert, Prediction, Severity
from peterpan.services.predictor import predict, predict_full


def make_alert(title: str, severity: Severity = Severity.P3) -> Alert:
    return Alert(
        id="a1", source="grafana", title=title, severity=severity, received_at=datetime.now(UTC)
    )


# --- guardrails: pure, no torch required -----------------------------------


def test_model_may_classify_only_when_floor_is_unclassified() -> None:
    floor = Prediction(incident_class="connectivity", severity=Severity.P2, confidence=0.75)
    model = MlPrediction(incident_class="latency", severity=Severity.P2, confidence=0.85)
    merged = apply_floor_guardrails(floor, model)
    assert merged.incident_class == "connectivity"  # floor's class is final


def test_model_refines_unclassified_floor() -> None:
    floor = Prediction(incident_class="unclassified", severity=Severity.P3, confidence=0.3)
    model = MlPrediction(incident_class="availability", severity=Severity.P3, confidence=0.8)
    merged = apply_floor_guardrails(floor, model)
    assert merged.incident_class == "availability"
    assert merged.confidence == 0.8


def test_model_may_raise_severity_never_lower() -> None:
    floor = Prediction(incident_class="unclassified", severity=Severity.P2, confidence=0.3)
    raised = apply_floor_guardrails(
        floor, MlPrediction(incident_class="availability", severity=Severity.P1, confidence=0.8)
    )
    assert raised.severity == Severity.P1
    lowered = apply_floor_guardrails(
        floor, MlPrediction(incident_class="availability", severity=Severity.P4, confidence=0.8)
    )
    assert lowered.severity == Severity.P2  # floor severity kept


def test_model_confidence_is_capped_below_certainty() -> None:
    floor = Prediction(incident_class="unclassified", severity=Severity.P3, confidence=0.3)
    merged = apply_floor_guardrails(
        floor, MlPrediction(incident_class="latency", severity=Severity.P3, confidence=1.0)
    )
    assert merged.confidence <= 0.9


def test_low_confidence_model_output_is_discarded() -> None:
    floor = Prediction(incident_class="unclassified", severity=Severity.P3, confidence=0.3)
    merged = apply_floor_guardrails(
        floor, MlPrediction(incident_class="latency", severity=Severity.P1, confidence=0.2)
    )
    assert merged == floor  # too uncertain to refine anything, even severity


# --- predict_full wiring ----------------------------------------------------


def test_floor_backend_never_touches_the_model(monkeypatch: pytest.MonkeyPatch) -> None:
    def boom(*args: object, **kwargs: object) -> MlPrediction:
        raise AssertionError("model must not be invoked for PP_PREDICTOR=floor")

    monkeypatch.setattr("peterpan.ml.model_predict", boom)
    settings = Settings(predictor=PredictorBackend.FLOOR)
    alert = make_alert("mysterious blip")
    assert predict_full(alert, settings) == predict(alert)


def test_torch_backend_falls_back_to_floor_on_any_model_failure(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def boom(*args: object, **kwargs: object) -> MlPrediction:
        # model_predict's contract: every failure mode surfaces as MlPredictError
        raise MlPredictError("weights missing / torch not installed")

    monkeypatch.setattr("peterpan.ml.model_predict", boom)
    settings = Settings(predictor=PredictorBackend.TORCH)
    alert = make_alert("mysterious blip")
    floor = predict(alert)
    full = predict_full(alert, settings)
    # Classification matches the floor; mode honestly reports the torch miss.
    assert full.incident_class == floor.incident_class
    assert full.severity == floor.severity
    assert full.confidence == floor.confidence
    assert full.mode == "floor-fallback"
    assert full.model_version == ""


def test_torch_backend_applies_guardrails_to_model_output(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fake(*args: object, **kwargs: object) -> MlPrediction:
        return MlPrediction(incident_class="availability", severity=Severity.P4, confidence=0.8)

    monkeypatch.setattr("peterpan.ml.model_predict", fake)
    settings = Settings(predictor=PredictorBackend.TORCH)
    p = predict_full(make_alert("mysterious blip", Severity.P2), settings)
    assert p.incident_class == "availability"  # floor was unclassified
    assert p.severity == Severity.P2  # model tried to lower — floor won


# --- real torch path (skipped when the ml extra isn't installed) ------------


def test_trained_model_classifies_paraphrase_without_floor_keywords() -> None:
    pytest.importorskip("torch")
    from peterpan.ml import DEFAULT_MODEL_DIR, model_predict, train

    if not (DEFAULT_MODEL_DIR / "predictor.pt").exists():
        train()  # deterministic seed; trains in seconds on the synthetic set

    # No floor keyword appears here; the floor alone returns unclassified.
    alert = make_alert("worker evicted after node memory pressure climbed for an hour")
    assert predict(alert).incident_class == "unclassified"
    ml = model_predict(alert)
    assert ml.incident_class == "resource_exhaustion"
    assert 0.0 < ml.confidence <= 0.9
