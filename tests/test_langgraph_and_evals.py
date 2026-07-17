"""LangGraph story graph equivalence + eval harness health."""

from __future__ import annotations

import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path

import pytest

from peterpan.schemas import Alert, Severity
from peterpan.services.agent import build_story


def make_alert() -> Alert:
    return Alert(
        id="lg-1",
        source="grafana",
        title="checkout OOMKilled",
        description="pod restarted twice, memory at limit",
        severity=Severity.P2,
        received_at=datetime.now(UTC),
    )


def test_langgraph_story_matches_deterministic_pipeline() -> None:
    pytest.importorskip("langgraph")
    from peterpan.agents.graph import run_story_graph

    alert = make_alert()
    graph_story = run_story_graph(alert)
    direct_story = build_story(alert)
    assert graph_story.probable_cause == direct_story.probable_cause
    assert graph_story.confidence == direct_story.confidence
    assert [e.source for e in graph_story.evidence] == [e.source for e in direct_story.evidence]


def test_langgraph_story_keeps_invariants() -> None:
    pytest.importorskip("langgraph")
    from peterpan.agents.graph import run_story_graph

    story = run_story_graph(make_alert())
    assert story.confidence < 1.0
    assert all(e.source for e in story.evidence)


def test_eval_harness_passes_all_cases() -> None:
    result = subprocess.run(
        [sys.executable, str(Path(__file__).parent.parent / "evals" / "run_story_eval.py")],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, f"eval failures:\n{result.stdout}\n{result.stderr}"
    assert "10/10 cases passed" in result.stdout
