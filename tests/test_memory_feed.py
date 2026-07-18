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


def test_windows_reserved_and_trailing_ids_rejected() -> None:
    # Reserved device basenames (case-insensitive, incl. .md extension) and
    # trailing dot/hyphen OSError at write time on Windows — reject at parse.
    for bad in ("CON", "nul", "Com1", "LPT9", "aux", "prn", "CON.md", "INC-", "INC-2231."):
        with pytest.raises(ValidationError):
            record(incident_id=bad)
    # Non-reserved lookalikes still pass (COM10 is not a reserved device).
    assert record(incident_id="COM10").incident_id == "COM10"
    assert record(incident_id="CONSOLE").incident_id == "CONSOLE"


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
    # Memory-fed docs are namespaced under incidents/memory/.
    assert source == "knowledge/incidents/memory/INC-9001.md"
    corpus = load_corpus(root)
    entry = next(e for e in corpus if e.source == source)
    # Still classified past_incident despite the nested memory/ dir.
    assert entry.kind == "past_incident"
    assert "cache hit rate collapsed" in entry.summary


def test_feed_is_idempotent_by_incident_id(tmp_path: Path) -> None:
    root = tmp_path / "knowledge"
    (root / "incidents").mkdir(parents=True)
    feed(record(resolution="first resolution attempt"), root=root)
    feed(record(resolution="second, corrected resolution"), root=root)
    docs = list((root / "incidents" / "memory").glob("*.md"))
    assert len(docs) == 1
    assert "second, corrected" in docs[0].read_text(encoding="utf-8")


def test_feed_never_overwrites_a_curated_incident(tmp_path: Path) -> None:
    # A fed id colliding with a committed doc (INC-2231 exists in the real
    # knowledge tree) must NOT touch the curated file — it lands in memory/.
    root = tmp_path / "knowledge"
    (root / "incidents").mkdir(parents=True)
    curated = root / "incidents" / "INC-2231.md"
    curated.write_text("# INC-2231 - curated, do not overwrite\n", encoding="utf-8")

    source = feed(record(incident_id="INC-2231", title="fed collision"), root=root)
    assert source == "knowledge/incidents/memory/INC-2231.md"
    # Curated doc is byte-for-byte unchanged.
    assert curated.read_text(encoding="utf-8") == "# INC-2231 - curated, do not overwrite\n"
    # The fed version is a distinct, retrievable past_incident.
    corpus = load_corpus(root)
    sources = {e.source for e in corpus}
    assert "knowledge/incidents/INC-2231.md" in sources
    assert source in sources
    fed = next(e for e in corpus if e.source == source)
    assert fed.kind == "past_incident"


# --- endpoint ----------------------------------------------------------------


def test_memory_endpoint_feeds_and_reloads_corpus(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from peterpan.services import rag

    root = tmp_path / "knowledge"
    (root / "incidents").mkdir(parents=True)
    monkeypatch.setattr(rag, "_KNOWLEDGE_ROOT_OVERRIDE", root)
    monkeypatch.setattr(rag, "_CORPUS", load_corpus(root))
    # _FULLTEXT is a module global the /memory route reassigns; register it so
    # monkeypatch restores it and the reload cannot leak into later tests.
    monkeypatch.setattr(rag, "_FULLTEXT", dict(rag._FULLTEXT))

    client = TestClient(rag.app)
    body = record().model_dump(mode="json")
    resp = client.post("/memory", json=body)
    assert resp.status_code == 200
    out = resp.json()
    assert out["source"] == "knowledge/incidents/memory/INC-9001.md"
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
    # _FULLTEXT is a module global the /memory route reassigns; register it so
    # monkeypatch restores it and the reload cannot leak into later tests.
    monkeypatch.setattr(rag, "_FULLTEXT", dict(rag._FULLTEXT))
    monkeypatch.setattr(rag.settings, "rag_backend", RagBackend.PINECONE)

    def boom(*args: object, **kwargs: object) -> None:
        raise memory.MemoryFeedError("pinecone down")

    monkeypatch.setattr(memory, "upsert_to_pinecone", boom)

    client = TestClient(rag.app)
    resp = client.post("/memory", json=record().model_dump(mode="json"))
    assert resp.status_code == 200
    out = resp.json()
    assert out["pinecone_synced"] is False
    assert (root / "incidents" / "memory" / "INC-9001.md").exists()  # local write survived
