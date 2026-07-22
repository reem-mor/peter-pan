"""RAG service — retrieves runbooks and past incidents relevant to an alert.

The corpus is loaded from the committed files under knowledge/ (see
peterpan.knowledge) — citations can never point at documents that don't
exist. Two backends behind the same search() contract:

- lexical (default): token-overlap scoring, zero external accounts —
  fixture-first demo path.
- pinecone (PP_RAG_BACKEND=pinecone): Voyage embeddings + Pinecone index,
  falling back to lexical on ANY failure.
"""

from __future__ import annotations

import re
from pathlib import Path

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from peterpan import memory
from peterpan.auth import install_api_auth
from peterpan.config import RagBackend, Settings
from peterpan.knowledge import KNOWLEDGE_ROOT, load_corpus
from peterpan.memory import MemoryRecord
from peterpan.schemas import Evidence, RagResult

app = FastAPI(title="peter-pan-rag")
settings = Settings()
install_api_auth(app, settings)

# Deterministic confidence ceiling: retrieval never claims certainty
# (product invariant: confidence < 1.0 ALWAYS).
_MAX_SCORE = 0.99
# Full text carries body root-cause keywords the summary drops; the summary
# (title + symptom line) stays the dominant ranking signal, so weight it higher.
_SUMMARY_WEIGHT = 0.6


def _load_corpus_and_text(root: Path | None) -> tuple[list[Evidence], dict[str, str]]:
    """Corpus + a source->full-text cache built from the SAME root, so the
    lexical backend can score body terms Pinecone would embed. Reconstructing
    the on-disk path as base.parent / source works for both the real tree and
    the temp trees tests point the feed at."""
    corpus = load_corpus(root)
    base = root or KNOWLEDGE_ROOT
    texts = {e.source: (base.parent / e.source).read_text(encoding="utf-8") for e in corpus}
    return corpus, texts


_CORPUS, _FULLTEXT = _load_corpus_and_text(None)
# Tests point the feed at a temp knowledge tree; None = the real KNOWLEDGE_ROOT.
_KNOWLEDGE_ROOT_OVERRIDE: object = None


def _tokens(text: str) -> set[str]:
    # [^\W_]+ = runs of unicode letters/digits (underscore excluded), so
    # hyphenated/punctuated compounds ("connection-pool") match their parts
    # (eval-07) AND non-ASCII text tokenizes instead of vanishing. casefold()
    # folds case unicode-aware.
    return set(re.findall(r"[^\W_]+", text.casefold()))


def _overlap(query: str, text: str) -> float:
    q, t = _tokens(query), _tokens(text)
    return len(q & t) / len(q) if q else 0.0


def _score(query: str, text: str) -> float:
    # Capped below 1.0: a query whose tokens are a subset of the text still
    # can't land exactly 1.0 in Evidence.confidence (confidence < 1.0 invariant).
    return min(_MAX_SCORE, round(_overlap(query, text), 3))


def _lexical_confidence(query: str, e: Evidence) -> float:
    body = _FULLTEXT.get(e.source, e.summary)
    combined = _SUMMARY_WEIGHT * _overlap(query, e.summary) + (1 - _SUMMARY_WEIGHT) * _overlap(
        query, body
    )
    return min(_MAX_SCORE, round(combined, 3))


def _search_lexical(query: str, top_k: int) -> list[Evidence]:
    # Empty token set (e.g. a symbol/emoji-only query) would score every doc
    # 0.0 and return arbitrary top_k — short-circuit to no matches instead.
    if not _tokens(query):
        return []
    ranked = sorted(
        (e.model_copy(update={"confidence": _lexical_confidence(query, e)}) for e in _CORPUS),
        key=lambda e: e.confidence,
        reverse=True,
    )
    return ranked[:top_k]


def _search_pinecone(query: str, top_k: int, kinds: list[str] | None = None) -> list[Evidence]:
    """Semantic retrieval. Raises on any failure; search() falls back.

    Fans out across the namespaces relevant to the query (all four for an
    incident query; an explicit kind filter narrows). All network/embedding
    logic lives in peterpan.pinecone_store so it can be exercised with mocks."""
    from peterpan import pinecone_store

    return pinecone_store.query(query, top_k, max_score=_MAX_SCORE, kinds=kinds, settings=settings)


def search(query: str, top_k: int = 3) -> RagResult:
    if not query.strip():
        raise ValueError("query must be non-empty")
    backend = "lexical"
    fallback = False
    fallback_reason = ""
    if settings.rag_backend is RagBackend.PINECONE:
        try:
            matches = _search_pinecone(query, top_k)
            backend = "pinecone"
        except Exception as exc:
            # Fail-safe retrieval, but never label lexical results as Pinecone.
            matches = _search_lexical(query, top_k)
            backend = "fallback"
            fallback = True
            fallback_reason = f"pinecone_unavailable:{type(exc).__name__}"
    else:
        matches = _search_lexical(query, top_k)
    label = "lexical-fallback" if fallback else backend
    cited = ", ".join(m.source for m in matches if m.confidence > 0) or "no relevant source"
    return RagResult(
        query=query,
        matches=matches,
        insight=f"Top context ({label}) drawn from: {cited}. "
        "Verify against live signals before acting.",
        backend=backend,
        configured_backend=settings.rag_backend.value,
        fallback=fallback,
        fallback_reason=fallback_reason,
    )


class QueryIn(BaseModel):
    query: str
    # gt=0: top_k<=0 used to slice silently (ranked[:-1] = corpus minus one).
    top_k: int = Field(default=3, gt=0)


@app.get("/healthz")
def healthz() -> dict[str, object]:
    configured = settings.rag_backend.value
    pinecone_ready = bool(settings.pinecone_api_key and settings.voyage_api_key)
    return {
        "service": "rag",
        "status": "ok",
        "corpus_size": len(_CORPUS),
        # `backend` kept as configured for probe compat; prefer configured_backend.
        "backend": configured,
        "configured_backend": configured,
        "pinecone_credentials_present": pinecone_ready,
        "auth_required": settings.api_token is not None,
    }


@app.post("/query")
def query_route(body: QueryIn) -> RagResult:
    try:
        return search(body.query, body.top_k)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@app.post("/memory")
def memory_route(record: MemoryRecord) -> dict[str, object]:
    """Feed a resolved, human-approved incident into the knowledge base.

    The local write is the source of truth and reloads the corpus in place;
    the Pinecone upsert (pinecone backend only) is best-effort and reported
    honestly — a sync failure never rolls back the document.
    """
    global _CORPUS, _FULLTEXT

    root = _KNOWLEDGE_ROOT_OVERRIDE if isinstance(_KNOWLEDGE_ROOT_OVERRIDE, Path) else None
    source = memory.feed(record, root=root)
    # Reload corpus AND the full-text cache together — a stale cache would score
    # the fed incident against nothing and it'd never retrieve.
    _CORPUS, _FULLTEXT = _load_corpus_and_text(root)

    pinecone_synced = False
    sync_error = ""
    if settings.rag_backend is RagBackend.PINECONE:
        try:
            memory.upsert_to_pinecone(record, source)
            pinecone_synced = True
        except memory.MemoryFeedError as exc:
            sync_error = str(exc)

    return {
        "source": source,
        "corpus_size": len(_CORPUS),
        "pinecone_synced": pinecone_synced,
        **({"sync_error": sync_error} if sync_error else {}),
    }
