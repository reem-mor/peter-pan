"""PETER PAN OS: time windows, groupings, and the deterministic budget guard."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from peterpan.usage import (
    UsageEvent,
    aggregate,
    budget_status,
    load_usage,
    log_usage,
    make_event,
    window,
)


def event_at(ts: datetime, agent: str = "incident-agent", cost: float = 0.01) -> UsageEvent:
    return UsageEvent(
        ts=ts.isoformat(),
        service="agent",
        agent=agent,
        model="sonnet",
        input_tokens=1000,
        output_tokens=200,
        cost_usd=cost,
    )


# --- window ------------------------------------------------------------------


def test_window_keeps_only_recent_events() -> None:
    now = datetime.now(UTC)
    old = event_at(now - timedelta(hours=30))
    fresh = event_at(now - timedelta(hours=1))
    assert window([old, fresh], hours=24) == [fresh]


def test_window_none_means_everything() -> None:
    now = datetime.now(UTC)
    events = [event_at(now - timedelta(days=365)), event_at(now)]
    assert window(events, hours=None) == events


# --- groupings ---------------------------------------------------------------


def test_aggregate_by_model_and_service() -> None:
    now = datetime.now(UTC)
    events = [event_at(now), event_at(now)]
    by_model = aggregate(events, by="model")
    assert by_model["sonnet"]["calls"] == 2
    by_service = aggregate(events, by="service")
    assert by_service["agent"]["cost_usd"] == pytest.approx(0.02)


def test_aggregate_rejects_unknown_grouping() -> None:
    with pytest.raises(ValueError):
        aggregate([], by="nonsense")


# --- budget guard ------------------------------------------------------------


def test_budget_ok_below_warn_threshold() -> None:
    now = datetime.now(UTC)
    status = budget_status([event_at(now, cost=0.5)], daily_budget_usd=5.0)
    assert status["status"] == "ok"
    assert status["spent_usd"] == pytest.approx(0.5)
    assert status["budget_usd"] == pytest.approx(5.0)


def test_budget_warn_at_80_percent() -> None:
    now = datetime.now(UTC)
    status = budget_status([event_at(now, cost=4.2)], daily_budget_usd=5.0)
    assert status["status"] == "warn"


def test_budget_exceeded_over_100_percent() -> None:
    now = datetime.now(UTC)
    status = budget_status([event_at(now, cost=6.0)], daily_budget_usd=5.0)
    assert status["status"] == "exceeded"


def test_budget_counts_last_24h_only() -> None:
    now = datetime.now(UTC)
    events = [event_at(now - timedelta(hours=30), cost=100.0), event_at(now, cost=0.1)]
    status = budget_status(events, daily_budget_usd=5.0)
    assert status["spent_usd"] == pytest.approx(0.1)
    assert status["status"] == "ok"


def test_budget_rejects_nonpositive_budget() -> None:
    with pytest.raises(ValueError):
        budget_status([], daily_budget_usd=0.0)


# --- endpoints ---------------------------------------------------------------


def test_usage_endpoint_supports_window_and_grouping(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from peterpan.services import ppos

    log = tmp_path / "usage.jsonl"
    log_usage(make_event("agent", "incident-agent", "sonnet", 1000, 200, 0.01), log)
    monkeypatch.setattr(ppos.settings, "usage_log_path", str(log))

    client = TestClient(ppos.app)
    body = client.get("/os/usage", params={"hours": 24, "by": "model"}).json()
    assert body["sonnet"]["calls"] == 1
    assert client.get("/os/usage", params={"by": "nonsense"}).status_code == 422


def test_budget_endpoint(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    from peterpan.services import ppos

    log = tmp_path / "usage.jsonl"
    log_usage(make_event("agent", "incident-agent", "sonnet", 1000, 200, 0.01), log)
    monkeypatch.setattr(ppos.settings, "usage_log_path", str(log))

    client = TestClient(ppos.app)
    body = client.get("/os/budget").json()
    assert body["status"] == "ok"
    assert body["spent_usd"] == pytest.approx(0.01)
    assert load_usage(log)  # sanity: the log we wrote is what the endpoint read
