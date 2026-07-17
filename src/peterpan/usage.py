"""Token/cost usage logging — the data source for PETER PAN OS.

Every LLM call in any service logs one JSONL row via `log_usage`. PETER PAN
OS aggregates these into per-agent/per-service dashboards and improvement
tips. Pure functions; the only side effect is the append, isolated at the
edge.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path


@dataclass(frozen=True)
class UsageEvent:
    ts: str
    service: str
    agent: str
    model: str
    input_tokens: int
    output_tokens: int
    cost_usd: float


def make_event(
    service: str, agent: str, model: str, input_tokens: int, output_tokens: int, cost_usd: float
) -> UsageEvent:
    if input_tokens < 0 or output_tokens < 0 or cost_usd < 0:
        raise ValueError("token counts and cost must be non-negative")
    return UsageEvent(
        ts=datetime.now(UTC).isoformat(),
        service=service,
        agent=agent,
        model=model,
        input_tokens=input_tokens,
        output_tokens=output_tokens,
        cost_usd=cost_usd,
    )


def log_usage(event: UsageEvent, path: str | Path) -> None:
    with Path(path).open("a", encoding="utf-8") as f:
        f.write(json.dumps(asdict(event)) + "\n")


def load_usage(path: str | Path) -> list[UsageEvent]:
    p = Path(path)
    if not p.exists():
        return []
    events: list[UsageEvent] = []
    for line in p.read_text(encoding="utf-8").splitlines():
        if line.strip():
            events.append(UsageEvent(**json.loads(line)))
    return events


def aggregate(events: list[UsageEvent]) -> dict[str, dict[str, float]]:
    """Cost and token totals per agent — the PETER PAN OS headline table."""
    out: dict[str, dict[str, float]] = {}
    for e in events:
        row = out.setdefault(
            e.agent, {"calls": 0.0, "input_tokens": 0.0, "output_tokens": 0.0, "cost_usd": 0.0}
        )
        row["calls"] += 1
        row["input_tokens"] += e.input_tokens
        row["output_tokens"] += e.output_tokens
        row["cost_usd"] += e.cost_usd
    return out


def tips(events: list[UsageEvent]) -> list[str]:
    """Cheap heuristics that catch the common cost regressions early."""
    out: list[str] = []
    if not events:
        return ["No usage recorded yet — wire log_usage() into every LLM call."]
    agg = aggregate(events)
    for agent, row in agg.items():
        avg_in = row["input_tokens"] / row["calls"]
        if avg_in > 50_000:
            out.append(
                f"{agent}: avg input {avg_in:,.0f} tokens/call — likely context bloat; "
                "trim retrieval or summarize history."
            )
        if row["cost_usd"] > 1.0 and row["calls"] > 10:
            out.append(
                f"{agent}: ${row['cost_usd']:.2f} over {row['calls']:.0f} calls — "
                "consider routing routine calls to a cheaper model tier."
            )
    return out or ["Usage looks healthy."]
