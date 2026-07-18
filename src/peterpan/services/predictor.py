"""Predictor service — classifies inbound alerts and assigns severity.

A deterministic keyword floor with final say, plus an opt-in local PyTorch
classifier behind it (PP_PREDICTOR=torch). The model may refine an
unclassified alert or raise severity — never lower it, never override a
floor classification, and any model failure falls back to floor-only.
"""

from __future__ import annotations

from fastapi import FastAPI

from peterpan import ml
from peterpan.config import PredictorBackend, Settings
from peterpan.schemas import Alert, Prediction, Severity

app = FastAPI(title="peter-pan-predictor")

# Deterministic floor: keyword → (class, minimum severity). The ML model may
# refine the class or raise severity above the floor, never lower it.
_FLOOR: list[tuple[str, str, Severity]] = [
    ("out of memory", "resource_exhaustion", Severity.P1),
    ("oom", "resource_exhaustion", Severity.P1),
    ("disk full", "resource_exhaustion", Severity.P1),
    ("connection refused", "connectivity", Severity.P2),
    ("timeout", "latency", Severity.P2),
    ("5xx", "availability", Severity.P2),
    ("certificate", "security", Severity.P2),
    ("deploy", "change_related", Severity.P3),
]


def predict(alert: Alert) -> Prediction:
    """Pure classification. Falls back to 'unclassified' at the alert's own severity."""
    text = f"{alert.title} {alert.description}".lower()
    for needle, incident_class, floor_severity in _FLOOR:
        if needle in text:
            # Never lower severity below what the alert already carries.
            severity = min(alert.severity, floor_severity, key=lambda s: s.value)
            return Prediction(incident_class=incident_class, severity=severity, confidence=0.75)
    return Prediction(incident_class="unclassified", severity=alert.severity, confidence=0.3)


def predict_full(alert: Alert, settings: Settings) -> Prediction:
    """Floor verdict, optionally refined by the local model under its guardrails."""
    floor = predict(alert)
    if settings.predictor is not PredictorBackend.TORCH:
        return floor
    try:
        return ml.apply_floor_guardrails(floor, ml.model_predict(alert))
    except ml.MlPredictError:
        return floor  # fail-safe: the deterministic path always answers


@app.get("/healthz")
def healthz() -> dict[str, str]:
    return {"service": "predictor", "status": "ok"}


@app.post("/predict")
def predict_route(alert: Alert) -> Prediction:
    return predict_full(alert, Settings())
