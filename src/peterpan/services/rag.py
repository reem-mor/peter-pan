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

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from peterpan.config import RagBackend, Settings
from peterpan.knowledge import load_corpus
from peterpan.schemas import Evidence, RagResult

app = FastAPI(title="peter-pan-rag")
settings = Settings()

_CORPUS: list[Evidence] = load_corpus()


def _tokens(text: str) -> set[str]:
    # Split on any non-alphanumeric run so hyphenated/punctuated compounds
    # ("connection-pool") match their parts — found by eval case eval-07.
    return set(re.findall(r"[a-z0-9]+", text.lower()))


def _score(query: str, text: str) -> float:
    q, t = _tokens(query), _tokens(text)
    return round(len(q & t) / len(q), 3) if q else 0.0


def _search_lexical(query: str, top_k: int) -> list[Evidence]:
    ranked = sorted(
        (e.model_copy(update={"confidence": _score(query, e.summary)}) for e in _CORPUS),
        key=lambda e: e.confidence,
        reverse=True,
    )
    return ranked[:top_k]


def _search_pinecone(query: str, top_k: int) -> list[Evidence]:
    """Semantic retrieval. Raises on any failure; search() falls back."""
    import pinecone  # noqa: F401  # lazy: optional `rag` extra
    import voyageai

    if not (settings.pinecone_api_key and settings.voyage_api_key):
        raise RuntimeError("pinecone backend needs PINECONE_API_KEY and VOYAGE_API_KEY")

    vector = (
        voyageai.Client(api_key=settings.voyage_api_key)
        .embed([query], model=settings.voyage_model, input_type="query")
        .embeddings[0]
    )
    index = pinecone.Pinecone(api_key=settings.pinecone_api_key).Index(settings.pinecone_index)
    result = index.query(vector=vector, top_k=top_k, include_metadata=True)
    return [
        Evidence(
            kind=m["metadata"].get("kind", "document"),
            summary=m["metadata"].get("summary", ""),
            source=m["metadata"].get("source", ""),
            confidence=round(max(0.0, min(1.0, m["score"])), 3),
        )
        for m in result["matches"]
    ]


def search(query: str, top_k: int = 3) -> RagResult:
    if not query.strip():
        raise ValueError("query must be non-empty")
    backend = "lexical"
    if settings.rag_backend is RagBackend.PINECONE:
        try:
            matches = _search_pinecone(query, top_k)
            backend = "pinecone"
        except Exception:
            matches = _search_lexical(query, top_k)  # fail-safe: never lose retrieval
    else:
        matches = _search_lexical(query, top_k)
    cited = ", ".join(m.source for m in matches if m.confidence > 0) or "no relevant source"
    return RagResult(
        query=query,
        matches=matches,
        insight=f"Top context ({backend}) drawn from: {cited}. "
        "Verify against live signals before acting.",
    )


class QueryIn(BaseModel):
    query: str
    top_k: int = 3


@app.get("/healthz")
def healthz() -> dict[str, str]:
    return {
        "service": "rag",
        "status": "ok",
        "corpus_size": str(len(_CORPUS)),
        "backend": settings.rag_backend.value,
    }


@app.post("/query")
def query_route(body: QueryIn) -> RagResult:
    try:
        return search(body.query, body.top_k)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
