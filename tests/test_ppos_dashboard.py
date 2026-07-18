"""PETER PAN OS dashboard feeds: time series and mesh health sweep.

(The legacy self-contained HTML page at /os/dashboard is retired — the
canonical operator console is the React app in web/agent-os.)
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from peterpan.usage import UsageEvent, log_usage, make_event, timeseries


def event_at(ts: datetime, cost: float = 0.01, tokens: int = 1000) -> UsageEvent:
    return UsageEvent(
        ts=ts.isoformat(),
        service="agent",
        agent="incident-agent",
        model="sonnet",
        input_tokens=tokens,
        output_tokens=200,
        cost_usd=cost,
    )


# --- timeseries --------------------------------------------------------------


def test_timeseries_buckets_events_and_keeps_empty_buckets() -> None:
    now = datetime.now(UTC)
    events = [event_at(now - timedelta(minutes=1)), event_at(now - timedelta(hours=23))]
    out = timeseries(events, hours=24, buckets=24)
    points = out["points"]
    assert isinstance(points, list)
    assert len(points) == 24
    assert sum(p["calls"] for p in points) == 2
    assert sum(p["input_tokens"] for p in points) == 2000
    # the fresh event lands in the final bucket
    assert points[-1]["calls"] == 1


def test_timeseries_excludes_events_outside_window() -> None:
    now = datetime.now(UTC)
    events = [event_at(now - timedelta(hours=30)), event_at(now)]
    out = timeseries(events, hours=24, buckets=12)
    assert sum(p["calls"] for p in out["points"]) == 1


def test_timeseries_empty_events_yields_zero_buckets() -> None:
    out = timeseries([], hours=1, buckets=6)
    points = out["points"]
    assert len(points) == 6
    assert all(p["cost_usd"] == 0.0 and p["calls"] == 0 for p in points)


def test_timeseries_rejects_nonpositive_args() -> None:
    with pytest.raises(ValueError):
        timeseries([], hours=0)
    with pytest.raises(ValueError):
        timeseries([], hours=1, buckets=0)


# --- endpoints ---------------------------------------------------------------


def test_series_endpoint(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    from peterpan.services import ppos

    log = tmp_path / "usage.jsonl"
    log_usage(make_event("agent", "incident-agent", "sonnet", 1000, 200, 0.01), log)
    monkeypatch.setattr(ppos.settings, "usage_log_path", str(log))

    client = TestClient(ppos.app)
    body = client.get("/os/usage/series", params={"hours": 24, "buckets": 10}).json()
    assert body["buckets"] == 10
    assert len(body["points"]) == 10
    assert sum(p["calls"] for p in body["points"]) == 1
    # validation guards
    assert client.get("/os/usage/series", params={"hours": 0}).status_code == 422
    assert client.get("/os/usage/series", params={"buckets": 0}).status_code == 422
    assert client.get("/os/usage/series", params={"buckets": 9999}).status_code == 422


def test_services_endpoint_reports_down_without_raising(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from peterpan.services import ppos

    monkeypatch.setattr(
        ppos.settings,
        "mesh",
        {"predictor": "http://127.0.0.1:1"},  # nothing listens here
    )
    monkeypatch.setattr(ppos, "_HEALTH_TIMEOUT_S", 0.2)

    client = TestClient(ppos.app)
    body = client.get("/os/services").json()
    assert body["services"][0]["name"] == "predictor"
    assert body["services"][0]["status"] == "down"
    assert body["services"][0]["latency_ms"] >= 0


def test_dashboard_route_is_retired() -> None:
    """/os/dashboard must stay gone — the operator console is web/agent-os."""
    from peterpan.services import ppos

    client = TestClient(ppos.app)
    assert client.get("/os/dashboard").status_code == 404
