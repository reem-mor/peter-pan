"""Deterministic feedback scoring — closes the learning loop measurably.

verdict -> score is a fixed, unit-tested mapping (helpful=1, partial=0.5,
wrong=0). This is a business/scoring decision, so it stays deterministic and
never LLM-decided (CLAUDE.md golden rule 1). Aggregation is pure arithmetic
over already-validated Feedback records; no network, no model call.
"""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Iterable, Mapping

from peterpan.schemas import Feedback, FeedbackVerdict

VERDICT_SCORES: dict[FeedbackVerdict, float] = {
    FeedbackVerdict.HELPFUL: 1.0,
    FeedbackVerdict.PARTIAL: 0.5,
    FeedbackVerdict.WRONG: 0.0,
}


def score_verdict(verdict: FeedbackVerdict) -> float:
    """The one place verdict -> score is decided. Every aggregate below is
    built from this, so changing the scale means changing exactly one line."""
    return VERDICT_SCORES[verdict]


def verdict_counts(items: Iterable[Feedback]) -> dict[str, int]:
    """Counts by verdict, zero-filled for every FeedbackVerdict member so a
    summary endpoint never has to special-case a verdict with no records yet."""
    counts: dict[str, int] = {v.value: 0 for v in FeedbackVerdict}
    for item in items:
        counts[item.verdict.value] += 1
    return counts


def accuracy(items: Iterable[Feedback]) -> float:
    """Mean deterministic score over items. An empty set scores 0.0 — "no
    feedback yet" is reported as no evidence of accuracy, not skipped or NaN,
    so a caller can gate on it directly."""
    items = list(items)
    if not items:
        return 0.0
    return sum(score_verdict(i.verdict) for i in items) / len(items)


def rolling_accuracy_by_prompt_version(
    items: Iterable[Feedback],
    prompt_version_by_trace: Mapping[str, str] | None = None,
) -> dict[str, float]:
    """Accuracy grouped by the prompt version that produced each trace.

    Feedback (and today's usage log) doesn't carry prompt_version on the
    record itself — that join lives wherever a caller tracks
    trace_id -> prompt_version (e.g. an eval's golden seed, or a future
    prompt-log). Graceful when that data is absent: no lookup, or a trace_id
    missing from it, means the record is skipped from the grouping rather
    than raising or crashing the endpoint/eval that calls this.
    """
    if not prompt_version_by_trace:
        return {}
    by_version: dict[str, list[Feedback]] = defaultdict(list)
    for item in items:
        version = prompt_version_by_trace.get(item.trace_id)
        if version is None:
            continue
        by_version[version].append(item)
    return {version: accuracy(group) for version, group in by_version.items()}
