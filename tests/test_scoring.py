"""Deterministic feedback scoring: verdict->score mapping and aggregation."""

from __future__ import annotations

from datetime import UTC, datetime

from peterpan.schemas import Feedback, FeedbackVerdict
from peterpan.scoring import (
    accuracy,
    rolling_accuracy_by_prompt_version,
    score_verdict,
    verdict_counts,
)


def _fb(trace_id: str, verdict: FeedbackVerdict, submitted_by: str = "sre-alex") -> Feedback:
    return Feedback(
        trace_id=trace_id,
        verdict=verdict,
        submitted_by=submitted_by,
        submitted_at=datetime.now(UTC),
    )


# --- score_verdict -------------------------------------------------------------


def test_score_verdict_mapping() -> None:
    assert score_verdict(FeedbackVerdict.HELPFUL) == 1.0
    assert score_verdict(FeedbackVerdict.PARTIAL) == 0.5
    assert score_verdict(FeedbackVerdict.WRONG) == 0.0


# --- verdict_counts --------------------------------------------------------------


def test_verdict_counts_zero_fills_missing_verdicts() -> None:
    items = [_fb("t1", FeedbackVerdict.HELPFUL)]
    counts = verdict_counts(items)
    assert counts == {"helpful": 1, "wrong": 0, "partial": 0}


def test_verdict_counts_tallies_each_verdict() -> None:
    items = [
        _fb("t1", FeedbackVerdict.HELPFUL),
        _fb("t2", FeedbackVerdict.HELPFUL),
        _fb("t3", FeedbackVerdict.WRONG),
        _fb("t4", FeedbackVerdict.PARTIAL),
    ]
    counts = verdict_counts(items)
    assert counts == {"helpful": 2, "wrong": 1, "partial": 1}


# --- accuracy --------------------------------------------------------------------


def test_accuracy_empty_is_zero() -> None:
    assert accuracy([]) == 0.0


def test_accuracy_averages_scores() -> None:
    items = [
        _fb("t1", FeedbackVerdict.HELPFUL),  # 1.0
        _fb("t2", FeedbackVerdict.PARTIAL),  # 0.5
        _fb("t3", FeedbackVerdict.WRONG),  # 0.0
        _fb("t4", FeedbackVerdict.HELPFUL),  # 1.0
    ]
    assert accuracy(items) == 0.625


# --- rolling_accuracy_by_prompt_version -------------------------------------------


def test_rolling_accuracy_empty_lookup_is_graceful() -> None:
    items = [_fb("t1", FeedbackVerdict.HELPFUL)]
    assert rolling_accuracy_by_prompt_version(items) == {}
    assert rolling_accuracy_by_prompt_version(items, {}) == {}


def test_rolling_accuracy_skips_traces_missing_from_lookup() -> None:
    items = [_fb("t1", FeedbackVerdict.HELPFUL), _fb("unmapped", FeedbackVerdict.WRONG)]
    result = rolling_accuracy_by_prompt_version(items, {"t1": "v5"})
    assert result == {"v5": 1.0}


def test_rolling_accuracy_groups_by_version() -> None:
    items = [
        _fb("t1", FeedbackVerdict.HELPFUL),
        _fb("t2", FeedbackVerdict.WRONG),
        _fb("t3", FeedbackVerdict.HELPFUL),
    ]
    lookup = {"t1": "v5", "t2": "v5", "t3": "v6"}
    result = rolling_accuracy_by_prompt_version(items, lookup)
    assert result == {"v5": 0.5, "v6": 1.0}
