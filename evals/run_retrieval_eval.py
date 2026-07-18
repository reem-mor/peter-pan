"""Retrieval eval — does the RAG backend return the right document?

A labeled golden set (query -> expected doc_id in the top-k) scored with
hit-rate@k and MRR. The LEXICAL backend is the default so this runs in CI with
zero keys (fixture-first invariant); the SAME golden set runs against the
Pinecone backend when keys are present via `--backend pinecone`, so the two
backends are compared on one ruler (contract §3: "compared by the retrieval
eval, not merged").

doc_id is the stable stem of a document's source path (INC-2401,
db-connection-pool, ...) — the same id the ingestion plan uses as metadata.

Usage:
    python evals/run_retrieval_eval.py                    # lexical, keyless
    python evals/run_retrieval_eval.py --backend pinecone # needs live keys

Exit non-zero if hit-rate@k falls below the threshold (CI gate).
"""

from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Callable
from pathlib import Path

from peterpan.schemas import Evidence
from peterpan.services import rag

ROOT = Path(__file__).parent.parent
CASES = ROOT / "data" / "eval" / "retrieval_cases.jsonl"

# Deterministic floor: the lexical backend must clear this on the committed
# corpus. Do not lower it to make a regression pass — fix retrieval instead.
HIT_RATE_THRESHOLD = 0.9

Retriever = Callable[[str, int], list[Evidence]]


def _load_cases(path: Path) -> list[dict]:
    return [
        json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()
    ]


def _doc_id(source: str) -> str:
    return Path(source).stem


def _lexical_retriever() -> Retriever:
    return lambda q, k: rag._search_lexical(q, k)


def _pinecone_retriever() -> Retriever:
    # kinds=None => fan out across all four namespaces (an incident query).
    return lambda q, k: rag._search_pinecone(q, k, None)


def _rank_of(expected: str, matches: list[Evidence]) -> int | None:
    """1-based rank of the first match whose doc_id equals `expected`, or None."""
    for i, m in enumerate(matches, start=1):
        if _doc_id(m.source) == expected:
            return i
    return None


def run(backend: str) -> int:
    retriever = _pinecone_retriever() if backend == "pinecone" else _lexical_retriever()
    cases = _load_cases(CASES)

    hits = 0
    reciprocal_ranks = 0.0
    failures: list[str] = []

    print(f"retrieval eval · backend={backend} · {len(cases)} cases\n")
    for case in cases:
        expected = case["expected_doc_id"]
        top_k = int(case.get("top_k", 3))
        matches = retriever(case["query"], top_k)
        rank = _rank_of(expected, matches)
        hit = rank is not None
        if hit:
            hits += 1
            reciprocal_ranks += 1.0 / rank
        else:
            failures.append(case["case_id"])
        got = ", ".join(f"{_doc_id(m.source)}" for m in matches) or "(none)"
        status = f"hit@{rank}" if hit else "MISS"
        print(f"{case['case_id']}: {status:<7} expect={expected:<18} got=[{got}]")

    total = len(cases)
    hit_rate = hits / total if total else 0.0
    mrr = reciprocal_ranks / total if total else 0.0
    print(f"\nhit-rate@k: {hit_rate:.3f} ({hits}/{total})   MRR: {mrr:.3f}")
    print(f"threshold:  {HIT_RATE_THRESHOLD:.3f}")

    if hit_rate < HIT_RATE_THRESHOLD:
        print(f"FAIL — hit-rate {hit_rate:.3f} < {HIT_RATE_THRESHOLD:.3f}; misses: {failures}")
        return 1
    print("PASS")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="RAG retrieval eval over a golden set.")
    parser.add_argument(
        "--backend",
        choices=["lexical", "pinecone"],
        default="lexical",
        help="lexical (default, keyless) or pinecone (needs live keys)",
    )
    args = parser.parse_args(argv)
    return run(args.backend)


if __name__ == "__main__":
    sys.exit(main())
