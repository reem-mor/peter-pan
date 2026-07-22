"""POST /feedback + GET /feedback/summary contract."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from peterpan.feedback_store import MAX_FEEDBACK_BYTES
from peterpan.services import ppos


@pytest.fixture
def client(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> TestClient:
    log = tmp_path / "feedback.jsonl"
    monkeypatch.setattr(ppos.settings, "feedback_log_path", str(log))
    return TestClient(ppos.app)


def _body(**overrides: object) -> dict[str, object]:
    payload: dict[str, object] = {
        "trace_id": "trace-1",
        "verdict": "helpful",
        "comment": "matched the postmortem",
        "submitted_by": "sre-alex",
        "submitted_at": "2026-01-05T09:00:00+00:00",
    }
    payload.update(overrides)
    return payload


# --- POST /feedback ----------------------------------------------------------


def test_post_feedback_stores_and_counts(client: TestClient) -> None:
    resp = client.post("/feedback", json=_body())
    assert resp.status_code == 201
    assert resp.json() == {"stored": True, "count": 1}

    resp2 = client.post("/feedback", json=_body(trace_id="trace-2"))
    assert resp2.json() == {"stored": True, "count": 2}


def test_post_feedback_rejects_invalid_verdict(client: TestClient) -> None:
    resp = client.post("/feedback", json=_body(verdict="amazing"))
    assert resp.status_code == 422


def test_post_feedback_rejects_blank_submitted_by(client: TestClient) -> None:
    resp = client.post("/feedback", json=_body(submitted_by="   "))
    assert resp.status_code == 422


def test_post_feedback_rejects_missing_required_field(client: TestClient) -> None:
    payload = _body()
    del payload["trace_id"]
    resp = client.post("/feedback", json=payload)
    assert resp.status_code == 422


def test_post_enriched_feedback_roundtrips_through_the_route(client: TestClient) -> None:
    """PR #53's structured outcome fields, HTTP-level: accepted on POST and
    served back verbatim by /feedback/summary entries (release-audit P2 —
    previously proven only at store level)."""
    enriched = _body(
        alert_id="demo-oom",
        root_cause_correct=True,
        recommendation_correct=False,
        dashboard_useful=True,
        final_root_cause="session cache leak after config regression",
        resolution_action="re-enabled the eviction job",
        analyst_confidence=1.0,  # deliberate le=1.0: human input, not system output
    )
    assert client.post("/feedback", json=enriched).status_code == 201

    entry = client.get("/feedback/summary").json()["entries"][-1]
    assert entry["alert_id"] == "demo-oom"
    assert entry["root_cause_correct"] is True
    assert entry["recommendation_correct"] is False
    assert entry["final_root_cause"] == "session cache leak after config regression"
    assert entry["analyst_confidence"] == 1.0


def test_post_feedback_rejects_out_of_range_analyst_confidence(client: TestClient) -> None:
    resp = client.post("/feedback", json=_body(analyst_confidence=1.5))
    assert resp.status_code == 422


def test_summary_serves_a_mixed_legacy_and_enriched_log(client: TestClient) -> None:
    """The on-disk JSONL a real deployment accumulates: legacy 5-field rows
    (pre-#53), enriched rows, and a poisoned line. Summary must serve both
    valid shapes — legacy rows emitting the enriched keys as nulls (the wire
    shape the TS mirror types) — and skip the poison without 500ing."""
    log = Path(ppos.settings.feedback_log_path)
    log.parent.mkdir(parents=True, exist_ok=True)
    legacy = {
        "trace_id": "legacy-1",
        "verdict": "helpful",
        "comment": "pre-enrichment row",
        "submitted_by": "sre-priya",
        "submitted_at": "2026-01-04T08:00:00+00:00",
    }
    enriched = _body(trace_id="rich-1", alert_id="demo-5xx", root_cause_correct=False)
    log.write_text(
        json.dumps(legacy) + "\n" + json.dumps(enriched) + "\n" + "{not-json\n",
        encoding="utf-8",
    )

    body = client.get("/feedback/summary").json()
    assert body["total"] == 2
    by_trace = {e["trace_id"]: e for e in body["entries"]}
    assert by_trace["legacy-1"]["alert_id"] is None
    assert by_trace["legacy-1"]["analyst_confidence"] is None
    assert by_trace["rich-1"]["alert_id"] == "demo-5xx"
    assert by_trace["rich-1"]["root_cause_correct"] is False


def test_post_feedback_rejects_oversize_body(client: TestClient) -> None:
    huge = _body(comment="x" * (MAX_FEEDBACK_BYTES + 1))
    resp = client.post(
        "/feedback",
        content=json.dumps(huge).encode("utf-8"),
        headers={"content-type": "application/json"},
    )
    assert resp.status_code == 413


def test_post_feedback_accepts_body_at_the_boundary(client: TestClient) -> None:
    # Comment sized so the whole JSON body sits comfortably under the cap —
    # confirms the check isn't off-by-one-rejecting valid small payloads.
    resp = client.post("/feedback", json=_body(comment="ok"))
    assert resp.status_code == 201


# --- GET /feedback/summary ----------------------------------------------------


def test_summary_counts_and_accuracy(client: TestClient) -> None:
    client.post("/feedback", json=_body(trace_id="t1", verdict="helpful"))
    client.post("/feedback", json=_body(trace_id="t2", verdict="wrong"))
    client.post("/feedback", json=_body(trace_id="t3", verdict="partial"))

    body = client.get("/feedback/summary").json()
    assert body["counts"] == {"helpful": 1, "wrong": 1, "partial": 1}
    assert body["total"] == 3
    assert body["accuracy"] == pytest.approx(0.5)
    assert len(body["entries"]) == 3


def test_summary_last_n_is_bounded(client: TestClient) -> None:
    for i in range(5):
        client.post("/feedback", json=_body(trace_id=f"t{i}"))

    body = client.get("/feedback/summary", params={"limit": 2}).json()
    assert body["total"] == 5
    assert len(body["entries"]) == 2
    assert [e["trace_id"] for e in body["entries"]] == ["t3", "t4"]


def test_summary_limit_rejects_out_of_range(client: TestClient) -> None:
    assert client.get("/feedback/summary", params={"limit": 0}).status_code == 422
    assert client.get("/feedback/summary", params={"limit": 10_000}).status_code == 422


def test_summary_filters_by_trace_id(client: TestClient) -> None:
    client.post("/feedback", json=_body(trace_id="t1", verdict="helpful"))
    client.post("/feedback", json=_body(trace_id="t2", verdict="wrong"))
    client.post("/feedback", json=_body(trace_id="t1", verdict="partial"))

    body = client.get("/feedback/summary", params={"trace_id": "t1"}).json()
    assert body["total"] == 2
    assert all(e["trace_id"] == "t1" for e in body["entries"])


def test_summary_on_empty_log(client: TestClient) -> None:
    body = client.get("/feedback/summary").json()
    assert body == {
        "counts": {"helpful": 0, "wrong": 0, "partial": 0},
        "total": 0,
        "accuracy": 0.0,
        "entries": [],
    }
