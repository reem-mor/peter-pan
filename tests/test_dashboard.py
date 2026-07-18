"""Dashboard generator: fallback determinism, allowlist guard, endpoint."""

from __future__ import annotations

from datetime import UTC, datetime

import pytest
from fastapi.testclient import TestClient

from peterpan.config import Settings
from peterpan.dashboard import DashboardError, build_dashboard, deterministic_spec
from peterpan.schemas import Alert, Severity
from peterpan.services.agent import app, build_story


def make_story():
    return build_story(
        Alert(
            id="d-1",
            source="grafana",
            title="checkout pod OOMKilled",
            description="pod restarted twice, memory at limit",
            severity=Severity.P2,
            received_at=datetime.now(UTC),
        )
    )


def test_deterministic_spec_is_story_first_and_cited() -> None:
    story = make_story()
    spec = deterministic_spec("why is checkout dying", story)
    assert spec.generated_by == "deterministic-fallback"
    assert spec.panels[0].kind == "stat"
    assert story.probable_cause in spec.panels[0].content
    table = next(p for p in spec.panels if p.kind == "table")
    assert all(row["source"] for row in table.rows)


def test_llm_off_returns_deterministic() -> None:
    spec = build_dashboard("problem", make_story(), Settings())
    assert spec.generated_by == "deterministic-fallback"


def test_llm_spec_api_failure_raises_dashboard_error(monkeypatch: pytest.MonkeyPatch) -> None:
    """_llm_spec unwraps the SecretStr key for the SDK and wraps any API
    failure in DashboardError (which build_dashboard turns into a fallback)."""
    import sys
    import types

    import peterpan.dashboard as dash

    class _Messages:
        def create(self, **kwargs: object) -> object:
            raise ConnectionError("down")

    class _Anthropic:
        def __init__(self, api_key: str) -> None:
            assert api_key == "test-not-real"  # raw key, not the masked wrapper
            self.messages = _Messages()

    monkeypatch.setitem(sys.modules, "anthropic", types.SimpleNamespace(Anthropic=_Anthropic))
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-not-real")
    settings = Settings()
    with pytest.raises(DashboardError, match="anthropic API failure"):
        dash._llm_spec("why is checkout dying", make_story(), settings)


def test_llm_failure_falls_back(monkeypatch: pytest.MonkeyPatch) -> None:
    import peterpan.dashboard as dash

    def boom(*a: object, **k: object) -> object:
        raise DashboardError("simulated")

    monkeypatch.setattr(dash, "_llm_spec", boom)
    spec = build_dashboard(
        "problem", make_story(), Settings(llm="anthropic", anthropic_api_key="x")
    )
    assert spec.generated_by == "deterministic-fallback"


def test_dashboard_endpoint() -> None:
    client = TestClient(app)
    resp = client.post(
        "/dashboard",
        json={
            "problem": "why is checkout dying",
            "alert": {
                "id": "d-2",
                "source": "webui",
                "title": "checkout pod OOMKilled",
                "received_at": datetime.now(UTC).isoformat(),
            },
        },
    )
    assert resp.status_code == 200
    body = resp.json()
    assert 3 <= len(body["panels"]) <= 6
    assert body["problem"] == "why is checkout dying"
