"""Agent: story building and the ActionPreview approval gate."""

from __future__ import annotations

from datetime import UTC, datetime

import pytest
from fastapi.testclient import TestClient

from peterpan.schemas import ActionRisk, Alert, Severity
from peterpan.services.agent import app, approve, build_story, propose_action


def make_alert() -> Alert:
    return Alert(
        id="inc-1",
        source="grafana",
        title="checkout OOMKilled",
        description="pod restarted twice, memory at limit",
        severity=Severity.P2,
        received_at=datetime.now(UTC),
    )


def test_story_contains_evidence_with_sources() -> None:
    story = build_story(make_alert())
    assert story.evidence
    assert all(e.source for e in story.evidence)


def test_story_never_claims_certainty() -> None:
    assert build_story(make_alert()).confidence < 1.0


def test_story_offers_repair_options() -> None:
    assert build_story(make_alert()).repair_options


def test_high_risk_action_always_requires_approval() -> None:
    preview = propose_action("rollback deploy 4111", ActionRisk.HIGH)
    assert preview.requires_approval
    assert not preview.executable


def test_approval_makes_action_executable() -> None:
    preview = propose_action("rollback deploy 4111", ActionRisk.HIGH)
    approved = approve(preview, approver="reem")
    assert approved.executable
    assert approved.approved_by == "reem"
    assert approved.approved_at is not None


def test_anonymous_approval_rejected() -> None:
    preview = propose_action("rollback deploy 4111", ActionRisk.HIGH)
    with pytest.raises(ValueError):
        approve(preview, approver="  ")


def test_read_only_action_needs_no_approval() -> None:
    preview = propose_action("fetch pod logs", ActionRisk.READ_ONLY)
    assert preview.executable


def test_story_endpoint() -> None:
    client = TestClient(app)
    resp = client.post(
        "/story",
        json={
            "id": "inc-2",
            "source": "pager",
            "title": "timeout on payments API",
            "received_at": datetime.now(UTC).isoformat(),
        },
    )
    assert resp.status_code == 200
    assert resp.json()["probable_cause"] == "latency"
