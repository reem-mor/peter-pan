"""LLM-judge layer over the story eval cases (RAGAS-style faithfulness).

For each eval case: build the story, then ask Claude to *refute* it —
is every claim grounded in the listed evidence, are citations real, are
there fabricated specifics? The judge never sees the knowledge base, only
the story's own evidence list: a claim the evidence can't support fails.

Deterministic metrics (class/severity/citations) stay in run_story_eval.py;
this adds the judgment layer those can't express. Requires ANTHROPIC_API_KEY
and the `llm` extra. Usage: python evals/run_llm_judge.py [max_cases]
"""

from __future__ import annotations

import json
import sys
from datetime import UTC, datetime
from pathlib import Path

from pydantic import BaseModel, Field

from peterpan.config import Settings
from peterpan.schemas import Alert, Severity
from peterpan.services.agent import build_story
from peterpan.usage import log_usage, make_event

ROOT = Path(__file__).parent.parent

JUDGE_SYSTEM = """You audit AI-generated incident reports. Try to REFUTE the report:
- ungrounded: any claim in what_changed/probable_cause/repair_options that the
  evidence list cannot support
- fabricated_specifics: versions, dates, teams, or metrics absent from evidence
- overconfidence: certainty language, guarantees, or claims an action was taken
Default to failing the report when uncertain.
Answer with exactly one JSON object, no prose:
{"grounded": bool, "violations": ["<quote> - <rule>"]}"""


class Verdict(BaseModel):
    grounded: bool
    violations: list[str] = Field(default_factory=list)


def judge(story_json: str, settings: Settings) -> Verdict:
    import anthropic

    client = anthropic.Anthropic(api_key=settings.anthropic_api_key)
    response = client.messages.create(
        model=settings.anthropic_model,
        max_tokens=1500,
        system=JUDGE_SYSTEM,
        messages=[{"role": "user", "content": story_json}],
    )
    log_usage(
        make_event(
            service="evals",
            agent="llm-judge",
            model=settings.anthropic_model,
            input_tokens=response.usage.input_tokens,
            output_tokens=response.usage.output_tokens,
            cost_usd=round(
                response.usage.input_tokens * 3e-06 + response.usage.output_tokens * 1.5e-05, 6
            ),
        ),
        settings.usage_log_path,
    )
    raw = "".join(b.text for b in response.content if b.type == "text").strip()
    if raw.startswith("```"):
        raw = raw.strip("`").removeprefix("json").strip()
    return Verdict.model_validate_json(raw)


def main() -> int:
    settings = Settings()
    if not settings.anthropic_api_key:
        print("ANTHROPIC_API_KEY not set - judge layer needs it")
        return 2
    max_cases = int(sys.argv[1]) if len(sys.argv) > 1 else 10

    alerts = {
        json.loads(line)["id"]: json.loads(line)
        for line in (ROOT / "data/synthetic/alerts.jsonl").read_text(encoding="utf-8").splitlines()
        if line.strip()
    }
    cases = [
        json.loads(line)
        for line in (ROOT / "data/eval/story_cases.jsonl").read_text(encoding="utf-8").splitlines()
        if line.strip()
    ][:max_cases]

    failures = []
    for case in cases:
        raw = alerts[case["alert_id"]]
        alert = Alert(
            id=raw["id"],
            source=raw["source"],
            title=raw["title"],
            description=raw.get("description", ""),
            severity=Severity(raw.get("severity", "P3")),
            received_at=datetime.now(UTC),
        )
        story = build_story(alert)
        verdict = judge(story.model_dump_json(exclude={"alert"}), settings)
        status = "GROUNDED" if verdict.grounded else f"REFUTED: {verdict.violations}"
        print(f"{case['case_id']}: {status}")
        if not verdict.grounded:
            failures.append(case["case_id"])

    print(f"\n{len(cases) - len(failures)}/{len(cases)} stories judged grounded")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
