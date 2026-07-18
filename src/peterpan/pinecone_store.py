"""Pinecone backend internals — namespaces, metadata, idempotent batched upserts.

This is the OPT-IN live path (contract §3). The fixture-first invariant holds:
lexical retrieval over knowledge/ is the default and needs no keys; nothing in
the demo path imports this module's network functions. Every network call here
is exercised in tests via monkeypatched pinecone/voyage clients — no test
requires live keys.

Layout mirrors the contract:

- **Namespaces:** runbooks / past-incidents / memory / docs — one domain each.
  Ingestion routes a doc to its namespace by kind + on-disk path; queries fan
  out across the relevant namespaces (an incident query hits all four; an
  explicit kind filter narrows to one).
- **Metadata per vector:** doc_id, kind, title, source (citation trail — never
  empty), fed_at (memory docs). Enforced by build_metadata.
- **Upserts:** batched (100/vector batch), idempotent by a stable vector id
  (the source path), retry with bounded exponential backoff on 429/5xx.
"""

from __future__ import annotations

import time
from collections.abc import Callable, Iterator, Sequence
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from peterpan.config import Settings
from peterpan.knowledge import KNOWLEDGE_ROOT, load_corpus
from peterpan.schemas import Evidence

# --- namespaces --------------------------------------------------------------

RUNBOOKS = "runbooks"
PAST_INCIDENTS = "past-incidents"
MEMORY = "memory"
DOCS = "docs"
NAMESPACES = (RUNBOOKS, PAST_INCIDENTS, MEMORY, DOCS)

# Evidence.kind vocabulary -> namespace. Note memory-fed docs carry kind
# "past_incident" for retrieval semantics but live under incidents/memory/ on
# disk, so the on-disk path is the tie-breaker (see namespace_for).
_KIND_TO_NAMESPACE = {
    "runbook": RUNBOOKS,
    "past_incident": PAST_INCIDENTS,
    "memory": MEMORY,
    "document": DOCS,
}

# Batching + retry bounds are product invariants (bounded loops): 100 vectors
# per upsert, at most MAX_RETRIES retries (=> MAX_RETRIES+1 attempts).
UPSERT_BATCH_SIZE = 100
MAX_RETRIES = 3
_BACKOFF_BASE_SECONDS = 0.5
# HTTP status codes that are worth retrying: rate limit + transient server-side.
_RETRYABLE_STATUS = frozenset({429, 500, 502, 503, 504})

EMBED_DIM = 1024  # voyage-3.5-lite — index dimension must match (contract §3)


def namespace_for(source: str, kind: str) -> str:
    """Route a document to its namespace. The on-disk path wins over kind so a
    memory-fed incident (kind past_incident, but under incidents/memory/) lands
    in `memory`, never in `past-incidents`."""
    if "memory" in Path(source).parts:
        return MEMORY
    return _KIND_TO_NAMESPACE.get(kind, DOCS)


def namespaces_for_kinds(kinds: Sequence[str] | None) -> list[str]:
    """Which namespaces a query should search. None (an incident query) fans
    out across all four; an explicit kind filter narrows to just its namespaces."""
    if not kinds:
        return list(NAMESPACES)
    ordered = [_KIND_TO_NAMESPACE[k] for k in kinds if k in _KIND_TO_NAMESPACE]
    # De-dupe while preserving order (two kinds can map to one namespace).
    seen: dict[str, None] = {}
    for ns in ordered:
        seen.setdefault(ns, None)
    return list(seen) or list(NAMESPACES)


# --- planning (build vectors from the committed corpus) ----------------------


def _title_of(text: str) -> str:
    """First non-blank line, stripped of leading markdown heading marks — the
    human-readable citation label."""
    for line in text.splitlines():
        stripped = line.strip()
        if stripped:
            return stripped.lstrip("# ").strip()
    return ""


@dataclass(frozen=True)
class PlannedVector:
    """One ingestion unit: enough to upsert without re-reading disk, and to
    print a keyless dry-run plan."""

    vector_id: str  # stable => idempotent upsert (re-upsert overwrites)
    namespace: str
    doc_id: str
    kind: str
    title: str
    source: str
    text: str
    fed_at: str | None = None

    def metadata(self) -> dict[str, Any]:
        return build_metadata(
            doc_id=self.doc_id,
            kind=self.kind,
            title=self.title,
            source=self.source,
            fed_at=self.fed_at,
        )


def build_metadata(
    *,
    doc_id: str,
    kind: str,
    title: str,
    source: str,
    fed_at: str | None = None,
) -> dict[str, Any]:
    """Metadata per vector (contract §3). `source` is the citation trail and is
    never allowed to be empty — an empty source would make a citation unverifiable."""
    if not source.strip():
        raise ValueError("vector metadata.source must be non-empty (citation trail)")
    meta: dict[str, Any] = {
        "doc_id": doc_id,
        "kind": kind,
        "title": title,
        "source": source,
    }
    if fed_at:
        meta["fed_at"] = fed_at
    return meta


def plan_corpus(root: Path | None = None) -> list[PlannedVector]:
    """Build the full ingestion plan from the committed knowledge/ tree — no
    network, no keys. Text is read from the SAME root the corpus was loaded from
    (base.parent / source), matching rag._load_corpus_and_text."""
    corpus = load_corpus(root)
    base = root or KNOWLEDGE_ROOT
    plans: list[PlannedVector] = []
    for e in corpus:
        path = base.parent / e.source
        text = path.read_text(encoding="utf-8")
        namespace = namespace_for(e.source, e.kind)
        fed_at = _fed_at_for(path) if namespace == MEMORY else None
        plans.append(
            PlannedVector(
                vector_id=e.source,  # repo-relative path == stable, unique id
                namespace=namespace,
                doc_id=Path(e.source).stem,
                kind=e.kind,
                title=_title_of(text),
                source=e.source,
                text=text,
                fed_at=fed_at,
            )
        )
    return plans


def _fed_at_for(path: Path) -> str:
    """ISO-8601 UTC feed timestamp for a memory doc, from its file mtime."""
    from datetime import UTC, datetime

    return datetime.fromtimestamp(path.stat().st_mtime, tz=UTC).isoformat()


def plan_summary(plans: Sequence[PlannedVector]) -> dict[str, int]:
    """Vector count per namespace — the shape a dry-run prints."""
    counts = dict.fromkeys(NAMESPACES, 0)
    for p in plans:
        counts[p.namespace] = counts.get(p.namespace, 0) + 1
    return counts


# --- batching + retry (network) ----------------------------------------------


def batched(items: Sequence[Any], size: int = UPSERT_BATCH_SIZE) -> Iterator[list[Any]]:
    """Yield fixed-size batches (<= size). Guards the 100-vector upsert limit."""
    if size <= 0:
        raise ValueError("batch size must be positive")
    for start in range(0, len(items), size):
        yield list(items[start : start + size])


def _status_of(exc: Exception) -> int | None:
    """Best-effort HTTP status extraction across pinecone client exception shapes."""
    for attr in ("status", "status_code", "code"):
        value = getattr(exc, attr, None)
        if isinstance(value, int):
            return value
    return None


def is_retryable(exc: Exception) -> bool:
    """A 429 or 5xx is transient and worth a bounded retry; anything else
    (auth, bad request, dimension mismatch) fails loud immediately."""
    status = _status_of(exc)
    if status is not None:
        return status in _RETRYABLE_STATUS
    text = str(exc)
    return any(str(code) in text for code in _RETRYABLE_STATUS)


def _backoff_seconds(attempt: int) -> float:
    """Exponential: base * 2**attempt (attempt starts at 0)."""
    return _BACKOFF_BASE_SECONDS * (2.0**attempt)


def upsert_batch(
    index: Any,
    vectors: list[dict[str, Any]],
    namespace: str,
    *,
    max_retries: int = MAX_RETRIES,
    sleep: Callable[[float], None] = time.sleep,
) -> int:
    """Upsert one batch into one namespace with bounded exponential backoff on
    429/5xx. Idempotent: the vector ids are stable, so a re-upsert overwrites.

    Bounded loop invariant: at most `max_retries` retries (max_retries+1 total
    attempts) — a persistently failing backend raises rather than looping."""
    attempt = 0
    while True:
        try:
            index.upsert(vectors=vectors, namespace=namespace)
            return len(vectors)
        except Exception as exc:  # noqa: BLE001 — classified by is_retryable
            if attempt >= max_retries or not is_retryable(exc):
                raise
            sleep(_backoff_seconds(attempt))
            attempt += 1


# --- clients (lazy — optional `rag` extra) -----------------------------------


def _voyage_client(settings: Settings) -> Any:
    import voyageai

    return voyageai.Client(api_key=settings.voyage_api_key)


def _pinecone(settings: Settings) -> Any:
    from pinecone import Pinecone

    return Pinecone(api_key=settings.pinecone_api_key)


def embed_documents(client: Any, texts: Sequence[str], model: str) -> list[list[float]]:
    result = client.embed(list(texts), model=model, input_type="document")
    return list(result.embeddings)


def embed_query(client: Any, query: str, model: str) -> list[float]:
    result = client.embed([query], model=model, input_type="query")
    return list(result.embeddings[0])


@dataclass
class IngestStats:
    """Per-run ingestion tally (returned by ingest, printed by the script)."""

    upserted: int = 0
    by_namespace: dict[str, int] = field(default_factory=dict)


def ingest(
    plans: Sequence[PlannedVector],
    *,
    settings: Settings | None = None,
    voyage_client: Any | None = None,
    index: Any | None = None,
    sleep: Callable[[float], None] = time.sleep,
) -> IngestStats:
    """Embed + upsert a plan, grouped by namespace, batched and retried.

    Clients are injectable so tests drive the whole path with mocks; in
    production they're built lazily from Settings. Requires keys only when it
    actually has to build a client — a caller passing mocks never needs them."""
    settings = settings or Settings()
    voyage_client = voyage_client or _voyage_client(settings)
    if index is None:
        index = _pinecone(settings).Index(settings.pinecone_index)

    stats = IngestStats()
    by_ns: dict[str, list[PlannedVector]] = {}
    for p in plans:
        by_ns.setdefault(p.namespace, []).append(p)

    for namespace, items in by_ns.items():
        for batch in batched(items):
            embeddings = embed_documents(
                voyage_client, [p.text for p in batch], settings.voyage_model
            )
            vectors = [
                {"id": p.vector_id, "values": emb, "metadata": p.metadata()}
                for p, emb in zip(batch, embeddings, strict=True)
            ]
            n = upsert_batch(index, vectors, namespace, sleep=sleep)
            stats.upserted += n
            stats.by_namespace[namespace] = stats.by_namespace.get(namespace, 0) + n
    return stats


def upsert_one(
    plan: PlannedVector,
    *,
    settings: Settings | None = None,
    voyage_client: Any | None = None,
    index: Any | None = None,
    sleep: Callable[[float], None] = time.sleep,
) -> None:
    """Single-doc upsert (the memory-feed path). Same batching/retry code as
    bulk ingest — one plan is just a one-item corpus."""
    ingest([plan], settings=settings, voyage_client=voyage_client, index=index, sleep=sleep)


# --- query (network) ---------------------------------------------------------


def _match_to_evidence(match: dict[str, Any], max_score: float) -> Evidence:
    meta = match.get("metadata", {}) or {}
    return Evidence(
        kind=meta.get("kind", "document"),
        summary=meta.get("title", "") or meta.get("summary", ""),
        source=meta.get("source", ""),
        confidence=round(max(0.0, min(max_score, float(match.get("score", 0.0)))), 3),
    )


def query(
    query_text: str,
    top_k: int,
    *,
    max_score: float,
    kinds: Sequence[str] | None = None,
    settings: Settings | None = None,
    voyage_client: Any | None = None,
    index: Any | None = None,
) -> list[Evidence]:
    """Dense retrieval fanned out across the relevant namespaces, merged and
    re-sorted to a single top_k. `kinds=None` searches all four namespaces (an
    incident query); an explicit kind filter narrows the fan-out."""
    settings = settings or Settings()
    if not (settings.pinecone_api_key and settings.voyage_api_key):
        raise RuntimeError("pinecone backend needs PINECONE_API_KEY and VOYAGE_API_KEY")
    voyage_client = voyage_client or _voyage_client(settings)
    if index is None:
        index = _pinecone(settings).Index(settings.pinecone_index)

    vector = embed_query(voyage_client, query_text, settings.voyage_model)
    matches: list[dict[str, Any]] = []
    for namespace in namespaces_for_kinds(kinds):
        result = index.query(vector=vector, top_k=top_k, namespace=namespace, include_metadata=True)
        matches.extend(result["matches"])

    ranked = sorted(matches, key=lambda m: m.get("score", 0.0), reverse=True)
    return [_match_to_evidence(m, max_score) for m in ranked[:top_k]]
