"""RAG: retrieval with mandatory citation trail."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from peterpan.services.rag import _score, app, search


def test_relevant_runbook_found_for_oom_query() -> None:
    result = search("checkout service out of memory OOM")
    assert result.matches
    assert result.matches[0].source == "knowledge/runbooks/checkout-oom.md"


def test_every_match_carries_a_source() -> None:
    result = search("certificate expiry")
    assert all(m.source for m in result.matches)


def test_every_corpus_citation_resolves_to_a_real_file() -> None:
    # The citation trail is only honest if the cited document exists.
    from pathlib import Path

    from peterpan.services.rag import _CORPUS

    repo_root = Path(__file__).parent.parent
    missing = [e.source for e in _CORPUS if not (repo_root / e.source).exists()]
    assert not missing, f"corpus cites files that don't exist: {missing}"


def test_insight_cites_sources_not_fabrications() -> None:
    result = search("5xx storm canary rollback")
    assert "knowledge/incidents/INC-2307.md" in result.insight


def test_empty_query_rejected() -> None:
    with pytest.raises(ValueError):
        search("   ")


def test_endpoint_rejects_empty_query_with_422() -> None:
    client = TestClient(app)
    assert client.post("/query", json={"query": " "}).status_code == 422


def test_body_only_term_retrieves_its_doc() -> None:
    # "CODEOWNERS" appears only in INC-2231's Lessons body, never in its
    # summary. Summary-only scoring would miss it and return arbitrary docs;
    # full-text scoring must surface the right incident.
    result = search("CODEOWNERS")
    assert result.matches
    assert result.matches[0].source == "knowledge/incidents/INC-2231.md"
    assert result.matches[0].confidence > 0


def test_score_never_reaches_one_for_subset_query() -> None:
    # Query tokens are a strict subset of the text — raw overlap is 1.0, which
    # must be capped below 1.0 (confidence < 1.0 invariant).
    score = _score("checkout oom", "runbook checkout service oom killed pods")
    assert score < 1.0
    assert score == 0.99


def test_non_ascii_query_returns_no_arbitrary_docs() -> None:
    # A symbol/emoji-only query tokenizes to nothing; it must return empty,
    # not an arbitrary top_k of zero-scored docs.
    result = search("🔥🔥🔥 ⚠️ 💥")
    assert result.matches == []
    assert "no relevant source" in result.insight


def test_healthz_reports_corpus() -> None:
    client = TestClient(app)
    body = client.get("/healthz").json()
    assert body["status"] == "ok"
    assert int(body["corpus_size"]) >= 4
