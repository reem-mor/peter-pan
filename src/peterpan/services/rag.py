"""RAG service — retrieves runbooks and past incidents relevant to an alert.

MVP: fixture corpus + lexical scoring, same interface the real vector store
(ChromaDB/pgvector/Pinecone) will implement. Every match carries a `source` —
the citation trail is a product invariant, not a nice-to-have.
"""

from __future__ import annotations

import re

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from peterpan.schemas import Evidence, RagResult

app = FastAPI(title="peter-pan-rag")

# Fixture corpus — synthetic runbooks/past incidents. Replaced by a real
# vector store behind the same `search()` signature.
_CORPUS: list[Evidence] = [
    Evidence(
        kind="runbook",
        summary="OOM in checkout service: raise memory limit, roll pods, check for leak in v2.3+",
        source="knowledge/runbooks/checkout-oom.md",
        confidence=0.0,
    ),
    Evidence(
        kind="past_incident",
        summary="2026-05-12: payment latency spike from connection-pool exhaustion after deploy",
        source="knowledge/incidents/INC-2231.md",
        confidence=0.0,
    ),
    Evidence(
        kind="runbook",
        summary="Certificate expiry: rotate via cert-manager, verify with openssl s_client",
        source="knowledge/runbooks/cert-rotation.md",
        confidence=0.0,
    ),
    Evidence(
        kind="past_incident",
        summary="2026-06-03: 5xx storm from bad canary; rollback restored availability in 6 min",
        source="knowledge/incidents/INC-2307.md",
        confidence=0.0,
    ),
]


def _tokens(text: str) -> set[str]:
    # Split on any non-alphanumeric run so hyphenated/punctuated compounds
    # ("connection-pool") match their parts — found by eval case eval-07.
    return set(re.findall(r"[a-z0-9]+", text.lower()))


def _score(query: str, text: str) -> float:
    q, t = _tokens(query), _tokens(text)
    return round(len(q & t) / len(q), 3) if q else 0.0


def search(query: str, top_k: int = 3) -> RagResult:
    if not query.strip():
        raise ValueError("query must be non-empty")
    ranked = sorted(
        (e.model_copy(update={"confidence": _score(query, e.summary)}) for e in _CORPUS),
        key=lambda e: e.confidence,
        reverse=True,
    )
    matches = ranked[:top_k]
    cited = ", ".join(m.source for m in matches if m.confidence > 0) or "no relevant source"
    return RagResult(
        query=query,
        matches=matches,
        insight=f"Top context drawn from: {cited}. Verify against live signals before acting.",
    )


class QueryIn(BaseModel):
    query: str
    top_k: int = 3


@app.get("/healthz")
def healthz() -> dict[str, str]:
    return {"service": "rag", "status": "ok", "corpus_size": str(len(_CORPUS))}


@app.post("/query")
def query_route(body: QueryIn) -> RagResult:
    try:
        return search(body.query, body.top_k)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
