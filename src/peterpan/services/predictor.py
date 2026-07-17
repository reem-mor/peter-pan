"""Predictor service — classifies inbound alerts and assigns severity.

MVP: a deterministic keyword/z-score floor. The PyTorch model slots in
*behind* this floor later — the deterministic path always has final say on
severity escalation (a model may raise severity, never silently lower it).
"""

from __future__ import annotations

from fastapi import FastAPI

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


@app.get("/healthz")
def healthz() -> dict[str, str]:
    return {"service": "predictor", "status": "ok"}


@app.post("/predict")
def predict_route(alert: Alert) -> Prediction:
    return predict(alert)
