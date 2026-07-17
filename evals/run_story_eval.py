"""Story-pipeline eval: run every eval case through build_story and score it.

Scores three things per case (the metrics RAGAS would call answer relevance /
groundedness, expressed deterministically so the eval runs with zero LLM
calls — a RAGAS/Langfuse layer can consume the same cases later):

- class_match      — predicted incident_class == expected
- severity_floor   — severity at least as severe as expected_min_severity
- citations        — every must_cite source appears in the story's evidence

Usage: python evals/run_story_eval.py   (exit 1 if any case fails)
"""

from __future__ import annotations

import json
import sys
from datetime import UTC, datetime
from pathlib import Path

from peterpan.schemas import Alert, Severity
from peterpan.services.agent import build_story
from peterpan.services.predictor import predict

ROOT = Path(__file__).parent.parent
ALERTS = ROOT / "data" / "synthetic" / "alerts.jsonl"
CASES = ROOT / "data" / "eval" / "story_cases.jsonl"


def _load_jsonl(path: Path) -> list[dict]:
    return [
        json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()
    ]


def run() -> int:
    alerts = {a["id"]: a for a in _load_jsonl(ALERTS)}
    cases = _load_jsonl(CASES)
    failures: list[str] = []

    for case in cases:
        raw = alerts[case["alert_id"]]
        alert = Alert(
            id=raw["id"],
            source=raw["source"],
            title=raw["title"],
            description=raw.get("description", ""),
            severity=Severity(raw.get("severity", "P3")),
            received_at=datetime.now(UTC),
            labels=raw.get("labels", {}),
        )
        story = build_story(alert)
        prediction = predict(alert)
        checks = {
            "class_match": story.probable_cause == case["expected_class"],
            # P1 < P2 lexically, so "at least as severe as expected" is <=
            "severity_floor": prediction.severity.value <= case["expected_min_severity"],
            "citations": all(
                any(e.source == src for e in story.evidence) for src in case["must_cite"]
            ),
        }
        failed = [name for name, ok in checks.items() if not ok]
        status = "PASS" if not failed else f"FAIL ({', '.join(failed)})"
        print(f"{case['case_id']}: {status}  [{story.probable_cause} @ conf {story.confidence}]")
        if failed:
            failures.append(case["case_id"])

    print(f"\n{len(cases) - len(failures)}/{len(cases)} cases passed")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(run())
