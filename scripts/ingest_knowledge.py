"""Ingest knowledge/ into the Pinecone index (idempotent — upsert by source).

Usage: python scripts/ingest_knowledge.py
Needs PINECONE_API_KEY + VOYAGE_API_KEY in .env and the `rag` extra installed.
Creates the serverless index on first run. Re-running re-embeds everything —
fine at this corpus size; switch to checksum-gated upserts when it grows.
"""

from __future__ import annotations

import sys

from peterpan.config import Settings
from peterpan.knowledge import KNOWLEDGE_ROOT, load_corpus, load_full_text

EMBED_DIM = 1024  # voyage-3.5-lite


def main() -> int:
    settings = Settings()
    if not (settings.pinecone_api_key and settings.voyage_api_key):
        print("PINECONE_API_KEY and VOYAGE_API_KEY must be set in .env")
        return 2

    import voyageai
    from pinecone import Pinecone, ServerlessSpec

    corpus = load_corpus()
    print(f"{len(corpus)} documents under {KNOWLEDGE_ROOT}")

    pc = Pinecone(api_key=settings.pinecone_api_key)
    if settings.pinecone_index not in [i["name"] for i in pc.list_indexes()]:
        pc.create_index(
            name=settings.pinecone_index,
            dimension=EMBED_DIM,
            metric="cosine",
            spec=ServerlessSpec(cloud="aws", region="us-east-1"),
        )
        print(f"created index {settings.pinecone_index}")
    index = pc.Index(settings.pinecone_index)

    voyage = voyageai.Client(api_key=settings.voyage_api_key)
    # Embed the FULL document text (not just the summary) — retrieval quality
    # comes from the body; the summary is only what we display.
    texts = [load_full_text(e.source) for e in corpus]
    embeddings = voyage.embed(texts, model=settings.voyage_model, input_type="document").embeddings

    index.upsert(
        vectors=[
            {
                "id": e.source,  # stable id => idempotent upserts
                "values": emb,
                "metadata": {"kind": e.kind, "summary": e.summary, "source": e.source},
            }
            for e, emb in zip(corpus, embeddings, strict=True)
        ]
    )
    print(f"upserted {len(corpus)} vectors into {settings.pinecone_index}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
