"""Memory feed: resolved incidents become retrievable knowledge — gated, safe.

Deterministic gates under test: the human-approval requirement, the id
allowlist (alert ids are attacker-controllable input), idempotent writes,
and the fail-safe Pinecone seam (local file is the source of truth).
"""

from __future__ import annotations

from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError

from peterpan.knowledge import load_corpus
from peterpan.memory import MemoryRecord, feed, to_markdown
from peterpan.schemas import Severity


def record(**overrides: object) -> MemoryRecord:
    base: dict[str, object] = {
        "incident_id": "INC-9001",
        "title": "Checkout latency after cache regression",
        "incident_class": "latency",
        "severity": Severity.P2,
        "what_happened": "p95 tripled after cache hit rate collapsed on the 12:00 rollout.",
        "resolution": "Rolled back the cache config; hit rate and latency recovered in 10m.",
        "evidence_sources": ["alert:grafana", "predictor:/predict"],
        "approved_by": "reem",
    }
    base.update(overrides)
    return MemoryRecord(**base)  # type: ignore[arg-type]


# --- deterministic gates -----------------------------------------------------


def test_unapproved_record_rejected() -> None:
    with pytest.raises(ValidationError):
        record(approved_by="")
    with pytest.raises(ValidationError):
        record(approved_by="   ")


def test_hostile_incident_id_rejected() -> None:
    for bad in ("../../etc/passwd", "a/b", "x" * 65, "", "INC 1", "..", ".hidden"):
        with pytest.raises(ValidationError):
            record(incident_id=bad)


def test_unknown_incident_class_rejected() -> None:
    with pytest.raises(ValidationError):
        record(incident_class="not_a_class")


# --- markdown + corpus roundtrip --------------------------------------------


def test_markdown_matches_corpus_doc_shape() -> None:
    md = to_markdown(record())
    assert md.startswith("# INC-9001")
    assert "**What happened:**" in md  # _summarize keys on this line
    assert "**Resolution:**" in md
    assert "reem" in md  # approval is part of the audit trail


def test_feed_writes_doc_and_corpus_finds_it(tmp_path: Path) -> None:
    root = tmp_path / "knowledge"
    (root / "incidents").mkdir(parents=True)
    source = feed(record(), root=root)
    assert source == "knowledge/incidents/INC-9001.md"
    corpus = load_corpus(root)
    entry = next(e for e in corpus if e.source == source)
    assert entry.kind == "past_incident"
    assert "cache hit rate collapsed" in entry.summary


def test_feed_is_idempotent_by_incident_id(tmp_path: Path) -> None:
    root = tmp_path / "knowledge"
    (root / "incidents").mkdir(parents=True)
    feed(record(resolution="first resolution attempt"), root=root)
    feed(record(resolution="second, corrected resolution"), root=root)
    docs = list((root / "incidents").glob("*.md"))
    assert len(docs) == 1
    assert "second, corrected" in docs[0].read_text(encoding="utf-8")


# --- endpoint ----------------------------------------------------------------


def test_memory_endpoint_feeds_and_reloads_corpus(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from peterpan.services import rag

    root = tmp_path / "knowledge"
    (root / "incidents").mkdir(parents=True)
    monkeypatch.setattr(rag, "_KNOWLEDGE_ROOT_OVERRIDE", root)
    monkeypatch.setattr(rag, "_CORPUS", load_corpus(root))

    client = TestClient(rag.app)
    body = record().model_dump(mode="json")
    resp = client.post("/memory", json=body)
    assert resp.status_code == 200
    out = resp.json()
    assert out["source"] == "knowledge/incidents/INC-9001.md"
    assert out["corpus_size"] == 1
    assert out["pinecone_synced"] is False  # lexical settings: no upsert attempted

    # The fed incident is immediately retrievable and citable.
    hits = client.post("/query", json={"query": "cache hit rate collapsed latency"}).json()
    assert any(m["source"] == out["source"] for m in hits["matches"])


def test_memory_endpoint_rejects_unapproved(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from peterpan.services import rag

    root = tmp_path / "knowledge"
    (root / "incidents").mkdir(parents=True)
    monkeypatch.setattr(rag, "_KNOWLEDGE_ROOT_OVERRIDE", root)

    client = TestClient(rag.app)
    body = record().model_dump(mode="json")
    body["approved_by"] = ""
    assert client.post("/memory", json=body).status_code == 422
    assert not list((root / "incidents").glob("*.md"))  # nothing written


def test_pinecone_failure_never_loses_the_local_write(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from peterpan import memory
    from peterpan.config import RagBackend
    from peterpan.services import rag

    root = tmp_path / "knowledge"
    (root / "incidents").mkdir(parents=True)
    monkeypatch.setattr(rag, "_KNOWLEDGE_ROOT_OVERRIDE", root)
    monkeypatch.setattr(rag, "_CORPUS", load_corpus(root))
    monkeypatch.setattr(rag.settings, "rag_backend", RagBackend.PINECONE)

    def boom(*args: object, **kwargs: object) -> None:
        raise memory.MemoryFeedError("pinecone down")

    monkeypatch.setattr(memory, "upsert_to_pinecone", boom)

    client = TestClient(rag.app)
    resp = client.post("/memory", json=record().model_dump(mode="json"))
    assert resp.status_code == 200
    out = resp.json()
    assert out["pinecone_synced"] is False
    assert (root / "incidents" / "INC-9001.md").exists()  # local write survived
