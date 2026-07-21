"""Feedback store: append/load JSONL roundtrip and resilience to bad rows."""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

from peterpan.feedback_store import append_feedback, count_feedback, load_feedback
from peterpan.schemas import Feedback, FeedbackVerdict


def _fb(trace_id: str = "trace-1", verdict: FeedbackVerdict = FeedbackVerdict.HELPFUL) -> Feedback:
    return Feedback(
        trace_id=trace_id,
        verdict=verdict,
        comment="looked right",
        submitted_by="sre-alex",
        submitted_at=datetime.now(UTC),
    )


def test_append_creates_parent_dir_and_returns_count(tmp_path: Path) -> None:
    log = tmp_path / "nested" / "feedback.jsonl"
    assert append_feedback(_fb("t1"), log) == 1
    assert append_feedback(_fb("t2"), log) == 2
    assert log.exists()


def test_load_roundtrips_fields(tmp_path: Path) -> None:
    log = tmp_path / "feedback.jsonl"
    original = _fb("trace-42", FeedbackVerdict.PARTIAL)
    append_feedback(original, log)
    loaded = load_feedback(log)
    assert len(loaded) == 1
    assert loaded[0].trace_id == "trace-42"
    assert loaded[0].verdict == FeedbackVerdict.PARTIAL
    assert loaded[0].comment == "looked right"


def test_load_missing_file_returns_empty(tmp_path: Path) -> None:
    assert load_feedback(tmp_path / "nope.jsonl") == []


def test_enriched_fields_roundtrip(tmp_path: Path) -> None:
    """The structured outcome fields (learning loop) survive the JSONL trip."""
    log = tmp_path / "feedback.jsonl"
    enriched = Feedback(
        trace_id="trace-rich",
        verdict=FeedbackVerdict.PARTIAL,
        comment="cause right, fix wrong",
        submitted_by="sre-alex",
        submitted_at=datetime.now(UTC),
        alert_id="demo-oom",
        root_cause_correct=True,
        recommendation_correct=False,
        dashboard_useful=True,
        final_root_cause="connection pool exhausted by retry storm",
        resolution_action="lowered client retry budget",
        analyst_confidence=1.0,  # a HUMAN may be certain — invariant binds the system only
    )
    append_feedback(enriched, log)
    (row,) = load_feedback(log)
    assert row.alert_id == "demo-oom"
    assert row.root_cause_correct is True
    assert row.recommendation_correct is False
    assert row.dashboard_useful is True
    assert row.final_root_cause.startswith("connection pool")
    assert row.analyst_confidence == 1.0


def test_legacy_rows_without_new_fields_still_load(tmp_path: Path) -> None:
    """Additive contract: pre-enrichment JSONL rows (the five original
    fields only) must keep loading with defaults — never skipped as drift."""
    log = tmp_path / "feedback.jsonl"
    legacy = (
        '{"trace_id": "old-1", "verdict": "helpful", "comment": "",'
        ' "submitted_by": "sre-dana", "submitted_at": "2026-07-01T00:00:00+00:00"}'
    )
    log.write_text(legacy + "\n", encoding="utf-8")
    (row,) = load_feedback(log)
    assert row.trace_id == "old-1"
    assert row.alert_id is None
    assert row.root_cause_correct is None
    assert row.analyst_confidence is None
    assert row.final_root_cause == ""


def test_analyst_confidence_rejects_out_of_range() -> None:
    import pytest

    payload = {**_fb().model_dump(mode="json"), "analyst_confidence": 1.5}
    with pytest.raises(ValueError):
        Feedback.model_validate(payload)


def test_load_skips_poisoned_rows(tmp_path: Path) -> None:
    log = tmp_path / "feedback.jsonl"
    append_feedback(_fb("good-1"), log)
    with log.open("a", encoding="utf-8") as f:
        f.write("not json at all\n")
        f.write('{"trace_id": "bad", "verdict": "not-a-real-verdict"}\n')
        f.write("\n")  # blank line
    append_feedback(_fb("good-2"), log)

    loaded = load_feedback(log)
    assert {r.trace_id for r in loaded} == {"good-1", "good-2"}


def test_count_feedback(tmp_path: Path) -> None:
    log = tmp_path / "feedback.jsonl"
    assert count_feedback(log) == 0
    append_feedback(_fb(), log)
    assert count_feedback(log) == 1
