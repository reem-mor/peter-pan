"""Feedback eval — does the learning loop actually show the prompt improving?

Replays the recorded feedback log against a synthetic golden seed
(data/eval/feedback_seed.jsonl, ~10 entries spanning two incident-agent
prompt versions) and scores it with peterpan.scoring's deterministic
verdict->score mapping. Prints a before/after accuracy table by
prompt_version and gates CI on the overall accuracy.

Feedback (and today's usage log) doesn't carry prompt_version on the record
itself — see peterpan.scoring.rolling_accuracy_by_prompt_version. The seed
file is the trace_id -> prompt_version ground truth for this eval; any real
operator feedback recorded for the same trace_ids (data/feedback.jsonl)
takes priority over the seed's canned verdict, since it reflects what an
actual operator reported. Fully keyless — no live LLM, no network.

Usage:
    python evals/run_feedback_eval.py

Exit non-zero if overall accuracy falls below the threshold (CI gate).
"""

from __future__ import annotations

import sys
from pathlib import Path

from peterpan import feedback_store, scoring
from peterpan.schemas import Feedback

ROOT = Path(__file__).parent.parent
SEED_PATH = ROOT / "data" / "eval" / "feedback_seed.jsonl"
FEEDBACK_LOG_PATH = ROOT / "data" / "feedback.jsonl"

# Deterministic floor: the learning loop must clear this on the seeded
# golden set. Do not lower it to make a regression pass — investigate the
# prompt/verdict data instead.
ACCURACY_THRESHOLD = 0.6


class SeedFeedback(Feedback):
    """One golden feedback record plus the prompt version it was recorded
    against — the join key real Feedback/usage rows don't carry yet."""

    prompt_version: str


def _load_seed(path: Path) -> list[SeedFeedback]:
    if not path.exists():
        return []
    records: list[SeedFeedback] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        records.append(SeedFeedback.model_validate_json(line))
    return records


def _replay(seed: list[SeedFeedback], recorded: list[Feedback]) -> list[Feedback]:
    """Real operator feedback wins over the seed's canned verdict for the
    same trace_id; the seed fills in every trace with no real feedback yet
    so the eval stays keyless and self-contained in a fresh checkout."""
    by_trace: dict[str, Feedback] = {f.trace_id: f for f in seed}
    for record in recorded:
        by_trace[record.trace_id] = record
    return list(by_trace.values())


def run() -> int:
    seed = _load_seed(SEED_PATH)
    if not seed:
        print(f"FAIL — no golden seed data at {SEED_PATH}")
        return 1

    prompt_version_by_trace = {f.trace_id: f.prompt_version for f in seed}
    recorded = feedback_store.load_feedback(FEEDBACK_LOG_PATH)
    replayed = _replay(seed, recorded)

    overall = scoring.accuracy(replayed)
    by_version = scoring.rolling_accuracy_by_prompt_version(replayed, prompt_version_by_trace)

    print(
        f"feedback eval · {len(replayed)} records ({len(recorded)} recorded, {len(seed)} seeded)\n"
    )
    print("(synthetic seed — illustrative plumbing check, not a measured result)")
    print(f"{'prompt_version':<32} {'n':>4} {'accuracy':>10}")
    for version in sorted(by_version):
        n = sum(1 for f in replayed if prompt_version_by_trace.get(f.trace_id) == version)
        print(f"{version:<32} {n:>4} {by_version[version]:>10.3f}")
    print(f"\n{'overall':<32} {len(replayed):>4} {overall:>10.3f}")
    print(f"threshold: {ACCURACY_THRESHOLD:.3f}")

    if overall < ACCURACY_THRESHOLD:
        print(f"\nFAIL — overall accuracy {overall:.3f} < {ACCURACY_THRESHOLD:.3f}")
        return 1
    print("\nPASS")
    return 0


def main(argv: list[str] | None = None) -> int:
    del argv  # no CLI flags today — kept for parity with the other evals
    return run()


if __name__ == "__main__":
    sys.exit(main())
