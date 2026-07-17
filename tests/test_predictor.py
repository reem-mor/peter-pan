"""Predictor: deterministic floor behavior."""

from __future__ import annotations

from datetime import UTC, datetime

from fastapi.testclient import TestClient

from peterpan.schemas import Alert, Severity
from peterpan.services.predictor import app, predict


def make_alert(title: str, severity: Severity = Severity.P3) -> Alert:
    return Alert(
        id="a1", source="grafana", title=title, severity=severity, received_at=datetime.now(UTC)
    )


def test_oom_classified_as_resource_exhaustion_and_escalated_to_p1() -> None:
    p = predict(make_alert("Pod killed: out of memory", Severity.P3))
    assert p.incident_class == "resource_exhaustion"
    assert p.severity == Severity.P1


def test_floor_never_lowers_existing_severity() -> None:
    # Alert already P1; 'deploy' floor is P3 — severity must stay P1.
    p = predict(make_alert("deploy gone wrong", Severity.P1))
    assert p.severity == Severity.P1


def test_unknown_signal_falls_back_to_unclassified() -> None:
    p = predict(make_alert("mysterious blip"))
    assert p.incident_class == "unclassified"
    assert p.confidence < 0.5


def test_healthz_and_predict_endpoint() -> None:
    client = TestClient(app)
    assert client.get("/healthz").json()["status"] == "ok"
    resp = client.post(
        "/predict",
        json={
            "id": "a2",
            "source": "pager",
            "title": "connection refused on payments",
            "received_at": datetime.now(UTC).isoformat(),
        },
    )
    assert resp.status_code == 200
    assert resp.json()["incident_class"] == "connectivity"
