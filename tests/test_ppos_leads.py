"""Landing-page lead capture on the PPOS service (POST /leads)."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest
from fastapi.testclient import TestClient

from peterpan.services import ppos

client = TestClient(ppos.app)

VALID_LEAD = {
    "name": "Ada Oncall",
    "email": "ada@example.com",
    "company": "Example Corp",
    "message": "We want the evidence-cited incident story for our on-call rotation.",
}


@pytest.fixture()
def leads_path(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    path = tmp_path / "leads.jsonl"
    monkeypatch.setattr(ppos, "LEADS_PATH", path)
    return path


def test_create_lead_appends_jsonl(leads_path: Path) -> None:
    resp = client.post("/leads", json=VALID_LEAD)
    assert resp.status_code == 201
    body = resp.json()
    assert body["status"] == "stored"
    lines = leads_path.read_text(encoding="utf-8").splitlines()
    assert len(lines) == 1
    record = json.loads(lines[0])
    assert record["id"] == body["id"]
    assert record["email"] == VALID_LEAD["email"]
    assert record["name"] == VALID_LEAD["name"]
    assert record["company"] == VALID_LEAD["company"]
    assert record["message"] == VALID_LEAD["message"]
    assert record["received_at"]  # ISO timestamp stamped server-side


def test_create_lead_message_optional(leads_path: Path) -> None:
    lead = {k: v for k, v in VALID_LEAD.items() if k != "message"}
    resp = client.post("/leads", json=lead)
    assert resp.status_code == 201
    record = json.loads(leads_path.read_text(encoding="utf-8"))
    assert record["message"] == ""


@pytest.mark.parametrize(
    "email",
    ["", "not-an-email", "missing-tld@host", "spaces in@example.com", "@example.com"],
)
def test_invalid_email_rejected(leads_path: Path, email: str) -> None:
    resp = client.post("/leads", json={**VALID_LEAD, "email": email})
    assert resp.status_code == 422
    assert not leads_path.exists()


@pytest.mark.parametrize(
    "overrides",
    [
        {"name": ""},
        {"name": "x" * 121},
        {"company": ""},
        {"company": "x" * 201},
        {"message": "x" * 2001},
    ],
)
def test_bounds_enforced(leads_path: Path, overrides: dict[str, str]) -> None:
    resp = client.post("/leads", json={**VALID_LEAD, **overrides})
    assert resp.status_code == 422
    assert not leads_path.exists()


def test_missing_fields_rejected(leads_path: Path) -> None:
    resp = client.post("/leads", json={"email": "ada@example.com"})
    assert resp.status_code == 422
    assert not leads_path.exists()


def test_webhook_not_fired_when_unset(leads_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(ppos.settings, "n8n_lead_webhook", None)
    monkeypatch.setattr(
        ppos.httpx, "post", lambda *a, **k: pytest.fail("webhook must not fire when unset")
    )
    assert client.post("/leads", json=VALID_LEAD).status_code == 201


def test_webhook_fired_when_set(leads_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[tuple[str, dict[str, Any]]] = []

    def fake_post(url: str, **kwargs: Any) -> None:
        calls.append((url, kwargs))

    monkeypatch.setattr(ppos.settings, "n8n_lead_webhook", "http://n8n.local/webhook/lead")
    monkeypatch.setattr(ppos.httpx, "post", fake_post)
    resp = client.post("/leads", json=VALID_LEAD)
    assert resp.status_code == 201
    assert len(calls) == 1
    url, kwargs = calls[0]
    assert url == "http://n8n.local/webhook/lead"
    assert kwargs["json"]["email"] == VALID_LEAD["email"]
    assert kwargs["timeout"] == 2.0


def test_webhook_failure_never_loses_the_lead(
    leads_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    def broken_post(url: str, **kwargs: Any) -> None:
        raise RuntimeError("n8n is down")

    monkeypatch.setattr(ppos.settings, "n8n_lead_webhook", "http://n8n.local/webhook/lead")
    monkeypatch.setattr(ppos.httpx, "post", broken_post)
    resp = client.post("/leads", json=VALID_LEAD)
    assert resp.status_code == 201
    assert len(leads_path.read_text(encoding="utf-8").splitlines()) == 1
