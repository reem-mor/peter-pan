"""Ingest knowledge/ into the Pinecone index (contract §3, opt-in live path).

Builds one vector per committed knowledge document via the existing loaders,
routes each to its namespace (runbooks / past-incidents / memory / docs), and
upserts in idempotent batches with bounded retry. Re-running overwrites by
stable id (the repo-relative source path) — safe to run repeatedly.

Usage:
    python scripts/ingest_kb.py --dry-run   # keyless: prints the plan, no network
    python scripts/ingest_kb.py             # needs PINECONE_API_KEY + VOYAGE_API_KEY

The dry-run is the fixture-first escape hatch: it exercises the full planning
path (namespace routing, metadata, batching shape) with zero external accounts.
"""

from __future__ import annotations

import argparse
import sys

from peterpan import pinecone_store
from peterpan.config import Settings
from peterpan.knowledge import KNOWLEDGE_ROOT
from peterpan.pinecone_store import EMBED_DIM, UPSERT_BATCH_SIZE, batched


def _print_plan(plans: list[pinecone_store.PlannedVector]) -> None:
    print(f"{len(plans)} documents under {KNOWLEDGE_ROOT}")
    for namespace, count in pinecone_store.plan_summary(plans).items():
        n_batches = len(list(batched(range(count)))) if count else 0
        print(f"  namespace {namespace:<14} {count:>3} vectors  ({n_batches} batch(es))")
    print(f"\nvector batch size: {UPSERT_BATCH_SIZE}  ·  embedding dim: {EMBED_DIM}")
    # Show every planned vector's id + metadata so the citation trail is auditable.
    for p in plans:
        fed = f"  fed_at={p.fed_at}" if p.fed_at else ""
        print(f"  [{p.namespace}] {p.doc_id:<12} kind={p.kind:<13} id={p.vector_id}{fed}")


def _ensure_index(settings: Settings) -> None:
    """Create the serverless index on first run (idempotent — skips if present)."""
    from pinecone import ServerlessSpec

    pc = pinecone_store._pinecone(settings)
    if settings.pinecone_index not in [i["name"] for i in pc.list_indexes()]:
        pc.create_index(
            name=settings.pinecone_index,
            dimension=EMBED_DIM,
            metric="cosine",
            spec=ServerlessSpec(cloud="aws", region="us-east-1"),
        )
        print(f"created index {settings.pinecone_index}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Ingest knowledge/ into Pinecone.")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="print the ingestion plan and exit; no keys, no network",
    )
    args = parser.parse_args(argv)

    plans = pinecone_store.plan_corpus()
    _print_plan(plans)

    if args.dry_run:
        print("\ndry-run: no vectors upserted")
        return 0

    settings = Settings()
    if not (settings.pinecone_api_key and settings.voyage_api_key):
        print("\nPINECONE_API_KEY and VOYAGE_API_KEY must be set (or use --dry-run)")
        return 2

    _ensure_index(settings)
    stats = pinecone_store.ingest(plans, settings=settings)
    print(f"\nupserted {stats.upserted} vectors into {settings.pinecone_index}")
    for namespace, count in stats.by_namespace.items():
        print(f"  {namespace}: {count}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
