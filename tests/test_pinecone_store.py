"""Pinecone backend internals — batching, idempotency, bounded retry/backoff,
namespace routing, metadata. Every network call is driven through mocked
pinecone/voyage clients: NO test here requires live keys (fixture-first).
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest

from peterpan import pinecone_store as ps

# --- fakes -------------------------------------------------------------------


class _Embeddings:
    def __init__(self, vectors: list[list[float]]) -> None:
        self.embeddings = vectors


class FakeVoyage:
    """Deterministic embedder: one fixed-dim vector per text; records calls."""

    def __init__(self) -> None:
        self.calls: list[dict[str, Any]] = []

    def embed(self, texts: list[str], model: str, input_type: str) -> _Embeddings:
        self.calls.append({"n": len(texts), "model": model, "input_type": input_type})
        return _Embeddings([[float(len(t))] * 4 for t in texts])


class FakeIndex:
    """Records upserts keyed by (namespace, id) so re-upsert overwrites —
    exactly the idempotency contract. `fail_times` makes the first N upserts
    raise, to drive the retry path."""

    def __init__(self, fail_times: int = 0, status: int | None = 429) -> None:
        self.store: dict[tuple[str, str], dict[str, Any]] = {}
        self.upsert_calls: list[dict[str, Any]] = []
        self.query_calls: list[dict[str, Any]] = []
        self._fail_times = fail_times
        self._status = status
        self.query_returns: dict[str, list[dict[str, Any]]] = {}

    def upsert(self, vectors: list[dict[str, Any]], namespace: str) -> None:
        self.upsert_calls.append({"namespace": namespace, "n": len(vectors)})
        if self._fail_times > 0:
            self._fail_times -= 1
            exc = RuntimeError("rate limited")
            if self._status is not None:
                exc.status = self._status  # type: ignore[attr-defined]
            raise exc
        for v in vectors:
            self.store[(namespace, v["id"])] = v

    def query(
        self, vector: list[float], top_k: int, namespace: str, include_metadata: bool
    ) -> dict[str, Any]:
        self.query_calls.append({"namespace": namespace, "top_k": top_k})
        return {"matches": self.query_returns.get(namespace, [])}


def _no_sleep(_: float) -> None:
    pass


# --- namespace routing -------------------------------------------------------


def test_namespace_for_routes_by_kind_and_path() -> None:
    assert ps.namespace_for("knowledge/runbooks/db-connection-pool.md", "runbook") == ps.RUNBOOKS
    assert ps.namespace_for("knowledge/incidents/INC-2401.md", "past_incident") == ps.PAST_INCIDENTS
    assert ps.namespace_for("knowledge/docs/architecture.md", "document") == ps.DOCS


def test_memory_fed_doc_routes_to_memory_not_past_incidents() -> None:
    # A memory-fed incident keeps kind past_incident for retrieval, but its
    # on-disk path (incidents/memory/) must route it to the memory namespace.
    src = "knowledge/incidents/memory/INC-9001.md"
    assert ps.namespace_for(src, "past_incident") == ps.MEMORY


def test_namespaces_for_kinds_fans_out_or_narrows() -> None:
    assert ps.namespaces_for_kinds(None) == list(ps.NAMESPACES)  # incident query: all four
    assert ps.namespaces_for_kinds(["runbook"]) == [ps.RUNBOOKS]  # explicit filter narrows
    # Two kinds mapping to distinct namespaces, de-duped and order-preserved.
    # past_incident also searches memory: memory-fed incidents keep
    # kind="past_incident" but live in the memory namespace.
    assert ps.namespaces_for_kinds(["runbook", "past_incident", "runbook"]) == [
        ps.RUNBOOKS,
        ps.PAST_INCIDENTS,
        ps.MEMORY,
    ]


# --- metadata ----------------------------------------------------------------


def test_metadata_source_is_never_empty() -> None:
    with pytest.raises(ValueError):
        ps.build_metadata(doc_id="x", kind="runbook", title="t", source="   ")


def test_metadata_includes_fed_at_only_when_present() -> None:
    without = ps.build_metadata(doc_id="x", kind="runbook", title="t", source="s")
    assert "fed_at" not in without
    with_fed = ps.build_metadata(doc_id="x", kind="memory", title="t", source="s", fed_at="2026")
    assert with_fed["fed_at"] == "2026"


# --- planning from the corpus ------------------------------------------------


def _seed_tree(root: Path) -> None:
    (root / "runbooks").mkdir(parents=True)
    (root / "incidents" / "memory").mkdir(parents=True)
    (root / "docs").mkdir(parents=True)
    (root / "runbooks" / "rb.md").write_text(
        "# Runbook - pool\n\n**Symptoms:** pool full.\n", encoding="utf-8"
    )
    (root / "incidents" / "INC-1.md").write_text(
        "# INC-1 - outage\n\n**What happened:** it broke.\n", encoding="utf-8"
    )
    (root / "incidents" / "memory" / "INC-9.md").write_text(
        "# INC-9 - fed\n\n**What happened:** learned.\n", encoding="utf-8"
    )
    (root / "docs" / "arch.md").write_text("# Architecture\n\nDesign notes.\n", encoding="utf-8")


def test_plan_corpus_routes_namespaces_and_builds_metadata(tmp_path: Path) -> None:
    root = tmp_path / "knowledge"
    _seed_tree(root)
    plans = {p.doc_id: p for p in ps.plan_corpus(root)}

    assert plans["rb"].namespace == ps.RUNBOOKS
    assert plans["INC-1"].namespace == ps.PAST_INCIDENTS
    assert plans["INC-9"].namespace == ps.MEMORY
    assert plans["arch"].namespace == ps.DOCS

    # doc_id == stem, title from the heading, source == stable vector id, never empty.
    assert plans["rb"].title == "Runbook - pool"
    assert plans["rb"].vector_id == plans["rb"].source != ""
    # fed_at only on memory-namespace docs.
    assert plans["INC-9"].fed_at is not None
    assert plans["rb"].fed_at is None
    assert plans["INC-9"].metadata()["fed_at"] == plans["INC-9"].fed_at


def test_plan_summary_counts_per_namespace(tmp_path: Path) -> None:
    root = tmp_path / "knowledge"
    _seed_tree(root)
    summary = ps.plan_summary(ps.plan_corpus(root))
    assert summary == {ps.RUNBOOKS: 1, ps.PAST_INCIDENTS: 1, ps.MEMORY: 1, ps.DOCS: 1}


# --- batching ----------------------------------------------------------------


def test_batched_respects_the_100_limit() -> None:
    sizes = [len(b) for b in ps.batched(list(range(250)), size=100)]
    assert sizes == [100, 100, 50]


def test_batched_rejects_nonpositive_size() -> None:
    with pytest.raises(ValueError):
        list(ps.batched([1, 2, 3], size=0))


# --- retry / backoff bounds --------------------------------------------------


def test_is_retryable_classifies_status_codes() -> None:
    r429 = RuntimeError("x")
    r429.status = 429  # type: ignore[attr-defined]
    r400 = RuntimeError("x")
    r400.status = 400  # type: ignore[attr-defined]
    assert ps.is_retryable(r429) is True
    assert ps.is_retryable(r400) is False
    # No status attr: fall back to matching the code in the message.
    assert ps.is_retryable(RuntimeError("HTTP 503 from upstream")) is True
    assert ps.is_retryable(RuntimeError("invalid dimension")) is False


def test_upsert_batch_retries_then_succeeds_with_exponential_backoff() -> None:
    index = FakeIndex(fail_times=2, status=500)
    slept: list[float] = []
    n = ps.upsert_batch(
        index,
        [{"id": "a", "values": [0.0], "metadata": {"source": "s"}}],
        "docs",
        sleep=slept.append,
    )
    assert n == 1
    assert len(index.upsert_calls) == 3  # 2 failures + 1 success
    assert slept == [0.5, 1.0]  # base * 2**attempt, bounded exponential


def test_upsert_batch_gives_up_after_max_retries_bounded_loop() -> None:
    # Always fails with a retryable status: must stop after MAX_RETRIES retries
    # (=> MAX_RETRIES+1 attempts), never loop forever (bounded loops invariant).
    index = FakeIndex(fail_times=99, status=429)
    with pytest.raises(RuntimeError):
        ps.upsert_batch(
            index,
            [{"id": "a", "values": [0.0], "metadata": {}}],
            "docs",
            max_retries=3,
            sleep=_no_sleep,
        )
    assert len(index.upsert_calls) == 4  # 1 initial + 3 retries, then raises


def test_upsert_batch_does_not_retry_non_retryable() -> None:
    index = FakeIndex(fail_times=1, status=400)  # bad request: fail loud immediately
    with pytest.raises(RuntimeError):
        ps.upsert_batch(
            index, [{"id": "a", "values": [0.0], "metadata": {}}], "docs", sleep=_no_sleep
        )
    assert len(index.upsert_calls) == 1  # no retry


# --- ingest (batching + idempotency + metadata) ------------------------------


def _plan(doc_id: str, namespace: str, source: str) -> ps.PlannedVector:
    return ps.PlannedVector(
        vector_id=source,
        namespace=namespace,
        doc_id=doc_id,
        kind="runbook",
        title=f"title {doc_id}",
        source=source,
        text=f"body {doc_id}",
    )


def test_ingest_batches_per_namespace_and_writes_full_metadata() -> None:
    voyage = FakeVoyage()
    index = FakeIndex()
    plans = [
        _plan("a", ps.RUNBOOKS, "knowledge/runbooks/a.md"),
        _plan("b", ps.RUNBOOKS, "knowledge/runbooks/b.md"),
        _plan("c", ps.DOCS, "knowledge/docs/c.md"),
    ]
    stats = ps.ingest(plans, voyage_client=voyage, index=index, sleep=_no_sleep)

    assert stats.upserted == 3
    assert stats.by_namespace == {ps.RUNBOOKS: 2, ps.DOCS: 1}
    # Idempotency key is the source path; metadata carries the citation trail.
    stored = index.store[(ps.RUNBOOKS, "knowledge/runbooks/a.md")]
    assert stored["metadata"] == {
        "doc_id": "a",
        "kind": "runbook",
        "title": "title a",
        "source": "knowledge/runbooks/a.md",
    }
    # Documents were embedded as documents, not queries.
    assert all(c["input_type"] == "document" for c in voyage.calls)


def test_ingest_is_idempotent_by_source_id() -> None:
    voyage = FakeVoyage()
    index = FakeIndex()
    plans = [_plan("a", ps.RUNBOOKS, "knowledge/runbooks/a.md")]
    ps.ingest(plans, voyage_client=voyage, index=index, sleep=_no_sleep)
    ps.ingest(plans, voyage_client=voyage, index=index, sleep=_no_sleep)  # re-upsert overwrites
    assert len(index.store) == 1  # same id => one vector, not two


def test_ingest_splits_into_hundred_vector_batches() -> None:
    voyage = FakeVoyage()
    index = FakeIndex()
    plans = [_plan(str(i), ps.DOCS, f"knowledge/docs/{i}.md") for i in range(250)]
    ps.ingest(plans, voyage_client=voyage, index=index, sleep=_no_sleep)
    assert [c["n"] for c in index.upsert_calls] == [100, 100, 50]
    assert len(index.store) == 250


# --- query fan-out -----------------------------------------------------------


def _match(source: str, score: float, kind: str = "past_incident") -> dict[str, Any]:
    return {"score": score, "metadata": {"source": source, "kind": kind, "title": source}}


def test_query_fans_out_across_namespaces_and_merges_top_k(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from peterpan.config import Settings

    monkeypatch.setenv("PINECONE_API_KEY", "k")
    monkeypatch.setenv("VOYAGE_API_KEY", "k")
    settings = Settings()
    voyage = FakeVoyage()
    index = FakeIndex()
    index.query_returns = {
        ps.RUNBOOKS: [_match("rb.md", 0.40, "runbook")],
        ps.PAST_INCIDENTS: [_match("inc.md", 0.90)],
        ps.MEMORY: [_match("mem.md", 0.10, "memory")],
        ps.DOCS: [_match("doc.md", 0.70, "document")],
    }
    out = ps.query(
        "incident query",
        top_k=2,
        max_score=0.99,
        kinds=None,
        settings=settings,
        voyage_client=voyage,
        index=index,
    )
    # Fanned across all four namespaces, merged, re-sorted, sliced to top_k.
    assert {c["namespace"] for c in index.query_calls} == set(ps.NAMESPACES)
    assert [e.source for e in out] == ["inc.md", "doc.md"]
    assert all(e.confidence < 1.0 for e in out)  # capped below 1.0 invariant


def test_query_kind_filter_narrows_namespaces(monkeypatch: pytest.MonkeyPatch) -> None:
    from peterpan.config import Settings

    monkeypatch.setenv("PINECONE_API_KEY", "k")
    monkeypatch.setenv("VOYAGE_API_KEY", "k")
    settings = Settings()
    index = FakeIndex()
    index.query_returns = {ps.RUNBOOKS: [_match("rb.md", 0.5, "runbook")]}
    ps.query(
        "just runbooks",
        top_k=3,
        max_score=0.99,
        kinds=["runbook"],
        settings=settings,
        voyage_client=FakeVoyage(),
        index=index,
    )
    assert {c["namespace"] for c in index.query_calls} == {ps.RUNBOOKS}


def test_query_requires_keys(monkeypatch: pytest.MonkeyPatch) -> None:
    from peterpan.config import Settings

    # delenv alone is not hermetic: pydantic-settings would still load keys
    # from an ambient .env and this test would hit the live network. Blank the
    # resolved fields directly so the no-key guard is exercised deterministically.
    settings = Settings()
    monkeypatch.setattr(settings, "pinecone_api_key", None)
    monkeypatch.setattr(settings, "voyage_api_key", None)
    with pytest.raises(RuntimeError):
        ps.query("q", top_k=3, max_score=0.99, settings=settings)


def test_client_factories_unwrap_secret_keys(monkeypatch: pytest.MonkeyPatch) -> None:
    """SecretStr unwraps exactly at the client-construction boundary —
    the SDK receives the raw key, never the masked wrapper."""
    import sys
    import types

    from pydantic import SecretStr

    from peterpan.config import Settings

    captured: dict[str, str] = {}

    class _FakeVoyageClient:
        def __init__(self, api_key: str) -> None:
            captured["voyage"] = api_key

    class _FakePinecone:
        def __init__(self, api_key: str) -> None:
            captured["pinecone"] = api_key

    monkeypatch.setitem(sys.modules, "voyageai", types.SimpleNamespace(Client=_FakeVoyageClient))
    monkeypatch.setitem(sys.modules, "pinecone", types.SimpleNamespace(Pinecone=_FakePinecone))

    settings = Settings()
    monkeypatch.setattr(settings, "voyage_api_key", SecretStr("voyage-test-not-real"))
    monkeypatch.setattr(settings, "pinecone_api_key", SecretStr("pinecone-test-not-real"))

    ps._voyage_client(settings)
    ps._pinecone(settings)
    assert captured == {"voyage": "voyage-test-not-real", "pinecone": "pinecone-test-not-real"}


# --- memory feed routes to the memory namespace ------------------------------


def test_memory_upsert_routes_to_memory_namespace_with_fed_at(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from peterpan import memory

    monkeypatch.setenv("PINECONE_API_KEY", "k")
    monkeypatch.setenv("VOYAGE_API_KEY", "k")
    captured: list[ps.PlannedVector] = []

    def fake_upsert_one(plan: ps.PlannedVector, **kwargs: Any) -> None:
        captured.append(plan)

    monkeypatch.setattr(ps, "upsert_one", fake_upsert_one)

    record = memory.MemoryRecord(
        incident_id="INC-9001",
        title="Checkout latency",
        incident_class="latency",
        severity=memory.Severity.P2,
        what_happened="p95 tripled after a cache regression on rollout.",
        resolution="Rolled back the cache config; latency recovered.",
        approved_by="reem",
    )
    memory.upsert_to_pinecone(record, "knowledge/incidents/memory/INC-9001.md")

    assert len(captured) == 1
    plan = captured[0]
    assert plan.namespace == ps.MEMORY
    assert plan.kind == "memory"
    assert plan.doc_id == "INC-9001"
    assert plan.fed_at is not None  # operator-fed docs carry a feed timestamp
    assert plan.metadata()["source"] == "knowledge/incidents/memory/INC-9001.md"
