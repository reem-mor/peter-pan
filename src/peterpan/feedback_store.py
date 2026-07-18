"""Feedback store — append-only JSONL log of operator verdicts on agent
output, the raw material for the learning loop (see peterpan.scoring).

Mirrors peterpan.usage's log/load pattern: pure functions, the only side
effect is the append, isolated at the edge. Feedback text is
attacker-controllable (an operator comment box) — every read tolerates a
torn write or a poisoned-but-valid-JSON row rather than 500ing the whole
feed, same resilience contract as usage.load_usage.
"""

from __future__ import annotations

from pathlib import Path

from peterpan.schemas import Feedback

# Hard cap on one submitted record's raw wire size. Comment text is free-form
# operator input — bound it so one request can't be used to grow the JSONL
# log unboundedly. Enforced by the route before the body is even parsed.
MAX_FEEDBACK_BYTES = 10 * 1024


def append_feedback(feedback: Feedback, path: str | Path) -> int:
    """Append one record and return the new total record count."""
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    with p.open("a", encoding="utf-8") as f:
        f.write(feedback.model_dump_json() + "\n")
    return count_feedback(p)


def load_feedback(path: str | Path) -> list[Feedback]:
    """All valid records, in file order. A torn append (crash mid-write) or a
    schema-drifted-but-valid-JSON row is skipped, not fatal — the feedback
    summary endpoint must keep serving the good rows."""
    p = Path(path)
    if not p.exists():
        return []
    records: list[Feedback] = []
    for line in p.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        try:
            records.append(Feedback.model_validate_json(line))
        except ValueError:
            continue
    return records


def count_feedback(path: str | Path) -> int:
    return len(load_feedback(path))
