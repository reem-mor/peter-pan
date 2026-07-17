"""PETER PAN OS: usage logging, aggregation, and tips."""

from __future__ import annotations

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from peterpan.services.ppos import app
from peterpan.usage import aggregate, load_usage, log_usage, make_event, tips


def test_log_and_load_roundtrip(tmp_path: Path) -> None:
    log = tmp_path / "usage.jsonl"
    log_usage(make_event("rag", "incident-agent", "sonnet", 1200, 300, 0.012), log)
    log_usage(make_event("rag", "incident-agent", "sonnet", 900, 250, 0.010), log)
    events = load_usage(log)
    assert len(events) == 2
    agg = aggregate(events)
    assert agg["incident-agent"]["calls"] == 2
    assert agg["incident-agent"]["cost_usd"] == pytest.approx(0.022)


def test_negative_values_rejected() -> None:
    with pytest.raises(ValueError):
        make_event("rag", "a", "m", -1, 0, 0.0)


def test_tips_flag_context_bloat(tmp_path: Path) -> None:
    log = tmp_path / "usage.jsonl"
    log_usage(make_event("agent", "bloated-agent", "opus", 80_000, 500, 0.5), log)
    assert any("context bloat" in t for t in tips(load_usage(log)))


def test_tips_on_empty_log_prompt_wiring() -> None:
    assert "No usage recorded yet" in tips([])[0]


def test_os_endpoints(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    client = TestClient(app)
    assert client.get("/healthz").json()["status"] == "ok"
    agents = client.get("/os/agents").json()["agents"]
    assert "incident-agent" in agents
    assert client.get("/os/tips").status_code == 200
