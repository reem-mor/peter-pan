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
