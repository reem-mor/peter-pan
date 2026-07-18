"""Predictor service — classifies inbound alerts and assigns severity.

A deterministic keyword floor with final say, plus an opt-in local PyTorch
classifier behind it (PP_PREDICTOR=torch). The model may refine an
unclassified alert or raise severity — never lower it, never override a
floor classification, and any model failure falls back to floor-only.
"""

from __future__ import annotations

import re

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
        # Leading word-boundary match: a bare substring check let "oom" fire
        # inside "zoom"/"room" (false resource_exhaustion P1). Only anchor
        # the *start* of the needle — real alert text glues suffixes on
        # ("OOMKilled", "timeouts"), and requiring a trailing boundary too
        # would reject those legitimate matches. Multi-word needles like
        # "out of memory" still match as a phrase.
        if re.search(rf"\b{re.escape(needle)}", text):
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
