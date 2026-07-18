"""evals/run_feedback_eval.py: replays feedback against the golden seed and
gates on the deterministic accuracy threshold."""

from __future__ import annotations

import importlib
import sys
from pathlib import Path

import pytest

EVALS_DIR = Path(__file__).parent.parent / "evals"


@pytest.fixture
def feedback_eval(monkeypatch: pytest.MonkeyPatch):
    """Import evals/run_feedback_eval.py fresh (it's not a package module)."""
    sys.path.insert(0, str(EVALS_DIR))
    try:
        module = importlib.import_module("run_feedback_eval")
        yield importlib.reload(module)
    finally:
        sys.path.remove(str(EVALS_DIR))
        sys.modules.pop("run_feedback_eval", None)


def test_eval_passes_on_the_committed_seed(feedback_eval) -> None:
    assert feedback_eval.run() == 0


def test_eval_fails_below_threshold(
    feedback_eval, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    seed = tmp_path / "feedback_seed.jsonl"
    seed.write_text(
        "\n".join(
            [
                '{"trace_id": "bad-1", "prompt_version": "v9", "verdict": "wrong", '
                '"submitted_by": "sre-eval", "submitted_at": "2026-01-01T00:00:00+00:00"}',
                '{"trace_id": "bad-2", "prompt_version": "v9", "verdict": "wrong", '
                '"submitted_by": "sre-eval", "submitted_at": "2026-01-01T00:00:00+00:00"}',
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    monkeypatch.setattr(feedback_eval, "SEED_PATH", seed)
    monkeypatch.setattr(feedback_eval, "FEEDBACK_LOG_PATH", tmp_path / "feedback.jsonl")

    assert feedback_eval.run() == 1


def test_eval_fails_loudly_on_missing_seed(
    feedback_eval, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(feedback_eval, "SEED_PATH", tmp_path / "nope.jsonl")
    assert feedback_eval.run() == 1


def test_eval_recorded_feedback_overrides_seed_verdict(
    feedback_eval, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A real operator verdict for a seeded trace_id replaces the canned one."""
    seed = tmp_path / "feedback_seed.jsonl"
    seed.write_text(
        '{"trace_id": "t1", "prompt_version": "v5", "verdict": "wrong", '
        '"submitted_by": "sre-eval", "submitted_at": "2026-01-01T00:00:00+00:00"}\n',
        encoding="utf-8",
    )
    recorded = tmp_path / "feedback.jsonl"
    recorded.write_text(
        '{"trace_id": "t1", "verdict": "helpful", "submitted_by": "sre-real", '
        '"submitted_at": "2026-01-02T00:00:00+00:00"}\n',
        encoding="utf-8",
    )
    monkeypatch.setattr(feedback_eval, "SEED_PATH", seed)
    monkeypatch.setattr(feedback_eval, "FEEDBACK_LOG_PATH", recorded)

    assert feedback_eval.run() == 0  # helpful (1.0) beats the threshold; wrong (0.0) wouldn't
