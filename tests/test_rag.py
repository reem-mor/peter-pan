"""RAG: retrieval with mandatory citation trail."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from peterpan.services.rag import app, search


def test_relevant_runbook_found_for_oom_query() -> None:
    result = search("checkout service out of memory OOM")
    assert result.matches
    assert result.matches[0].source == "runbooks/checkout-oom.md"


def test_every_match_carries_a_source() -> None:
    result = search("certificate expiry")
    assert all(m.source for m in result.matches)


def test_insight_cites_sources_not_fabrications() -> None:
    result = search("5xx storm canary rollback")
    assert "incidents/INC-2307.md" in result.insight


def test_empty_query_rejected() -> None:
    with pytest.raises(ValueError):
        search("   ")


def test_endpoint_rejects_empty_query_with_422() -> None:
    client = TestClient(app)
    assert client.post("/query", json={"query": " "}).status_code == 422


def test_healthz_reports_corpus() -> None:
    client = TestClient(app)
    body = client.get("/healthz").json()
    assert body["status"] == "ok"
    assert int(body["corpus_size"]) >= 4
