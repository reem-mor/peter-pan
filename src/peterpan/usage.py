"""Token/cost usage logging — the data source for PETER PAN OS.

Every LLM call in any service logs one JSONL row via `log_usage`. PETER PAN
OS aggregates these into per-agent/per-service dashboards and improvement
tips. Pure functions; the only side effect is the append, isolated at the
edge.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from datetime import UTC, datetime, timedelta
from pathlib import Path

# Rough USD-per-token (input, output) by model id for cost metering. One table
# so every metering site prices the same way; "_default" catches unknown ids
# with sonnet-tier pricing instead of crashing or silently metering $0.
MODEL_RATES: dict[str, tuple[float, float]] = {
    "claude-sonnet-5": (3e-06, 1.5e-05),
    "claude-opus-4-8": (1.5e-05, 7.5e-05),
    "claude-haiku-4-5-20251001": (1e-06, 5e-06),
    # Bedrock list price for Sonnet matches the direct API ($3/$15 per MTok).
    "anthropic.claude-sonnet-4-5-20250929-v1:0": (3e-06, 1.5e-05),
    "us.anthropic.claude-sonnet-4-5-20250929-v1:0": (3e-06, 1.5e-05),
    "_default": (3e-06, 1.5e-05),
}


def model_rates(model: str) -> tuple[float, float]:
    """(input_rate, output_rate) for a model id, defaulting loudly-visibly."""
    return MODEL_RATES.get(model, MODEL_RATES["_default"])


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


def _is_valid_row(event: UsageEvent) -> bool:
    """Schema-valid JSON can still be a poisoned row: an unparsable/naive ts,
    or non-numeric token counts, load fine here but crash aggregate/window/
    timeseries later at request time. Reject those up front."""
    try:
        ts = datetime.fromisoformat(event.ts)
    except ValueError:
        return False
    if ts.tzinfo is None:
        return False
    # bool is an int subclass — exclude it explicitly so True/False tokens
    # don't silently pass the isinstance(int) check.
    if isinstance(event.input_tokens, bool) or not isinstance(event.input_tokens, int):
        return False
    if isinstance(event.output_tokens, bool) or not isinstance(event.output_tokens, int):
        return False
    if isinstance(event.cost_usd, bool) or not isinstance(event.cost_usd, int | float):
        return False
    return True


def load_usage(path: str | Path) -> list[UsageEvent]:
    p = Path(path)
    if not p.exists():
        return []
    events: list[UsageEvent] = []
    for line in p.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        # A torn append (crash mid-write), schema drift, or a poisoned-but-
        # valid-JSON row must not take down PETER PAN OS — skip the bad row,
        # keep serving the good ones.
        try:
            event = UsageEvent(**json.loads(line))
        except (ValueError, TypeError):
            continue
        if not _is_valid_row(event):
            continue
        events.append(event)
    return events


_GROUPINGS = ("agent", "model", "service")


def window(events: list[UsageEvent], hours: float | None) -> list[UsageEvent]:
    """Events from the last N hours (None = everything)."""
    if hours is None:
        return events
    cutoff = datetime.now(UTC) - timedelta(hours=hours)
    return [e for e in events if datetime.fromisoformat(e.ts) >= cutoff]


def aggregate(events: list[UsageEvent], by: str = "agent") -> dict[str, dict[str, float]]:
    """Cost and token totals grouped by agent/model/service — the OS headline table."""
    if by not in _GROUPINGS:
        raise ValueError(f"unknown grouping {by!r}; expected one of {_GROUPINGS}")
    out: dict[str, dict[str, float]] = {}
    for e in events:
        row = out.setdefault(
            getattr(e, by),
            {"calls": 0.0, "input_tokens": 0.0, "output_tokens": 0.0, "cost_usd": 0.0},
        )
        row["calls"] += 1
        row["input_tokens"] += e.input_tokens
        row["output_tokens"] += e.output_tokens
        row["cost_usd"] += e.cost_usd
    return out


def timeseries(
    events: list[UsageEvent], hours: float = 24.0, buckets: int = 48
) -> dict[str, object]:
    """Bucketed cost/token series over the last N hours — the OS chart feed.

    Empty buckets are kept so charts render a continuous axis; the bucket
    timestamp is the bucket's start.
    """
    if hours <= 0:
        raise ValueError("hours must be positive")
    if buckets <= 0:
        raise ValueError("buckets must be positive")
    end = datetime.now(UTC)
    start = end - timedelta(hours=hours)
    step = (end - start) / buckets
    calls = [0] * buckets
    input_tokens = [0] * buckets
    output_tokens = [0] * buckets
    cost_usd = [0.0] * buckets
    for e in window(events, hours):
        idx = min(int((datetime.fromisoformat(e.ts) - start) / step), buckets - 1)
        calls[idx] += 1
        input_tokens[idx] += e.input_tokens
        output_tokens[idx] += e.output_tokens
        cost_usd[idx] += e.cost_usd
    points = [
        {
            "t": (start + i * step).isoformat(),
            "calls": calls[i],
            "input_tokens": input_tokens[i],
            "output_tokens": output_tokens[i],
            "cost_usd": round(cost_usd[i], 6),
        }
        for i in range(buckets)
    ]
    return {
        "start": start.isoformat(),
        "end": end.isoformat(),
        "hours": hours,
        "buckets": buckets,
        "points": points,
    }


# Warn threshold for the budget guard. Deterministic and unit-tested — an LLM
# never decides whether spend is acceptable.
_BUDGET_WARN_RATIO = 0.8


def budget_status(events: list[UsageEvent], daily_budget_usd: float) -> dict[str, object]:
    """Spend over the last 24h vs the configured daily budget.

    Report-only: PETER PAN OS surfaces the state; enforcement (routing to a
    cheaper tier, refusing calls) is a deliberate, separate decision.
    """
    if daily_budget_usd <= 0:
        raise ValueError("daily_budget_usd must be positive")
    spent = sum(e.cost_usd for e in window(events, hours=24))
    ratio = spent / daily_budget_usd
    status = "ok" if ratio < _BUDGET_WARN_RATIO else ("warn" if ratio <= 1.0 else "exceeded")
    return {
        "status": status,
        "spent_usd": round(spent, 6),
        "budget_usd": daily_budget_usd,
        "window_hours": 24,
    }


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
