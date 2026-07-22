"""evals/run_retrieval_eval.py: the 0.900 hit-rate gate, actually executed.

Its docstring has claimed "CI gate" since it landed, but neither CI nor any
test ever ran it (release-audit P1-7) — retrieval quality could regress to
zero with green pipelines. This wrapper makes the gate real via the same
import pattern as tests/test_feedback_eval.py.
"""

from __future__ import annotations

import importlib
import json
import sys
from pathlib import Path

import pytest

EVALS_DIR = Path(__file__).parent.parent / "evals"


@pytest.fixture
def retrieval_eval(monkeypatch: pytest.MonkeyPatch):
    """Import evals/run_retrieval_eval.py fresh (it's not a package module)."""
    sys.path.insert(0, str(EVALS_DIR))
    try:
        module = importlib.import_module("run_retrieval_eval")
        yield importlib.reload(module)
    finally:
        sys.path.remove(str(EVALS_DIR))
        sys.modules.pop("run_retrieval_eval", None)


def test_eval_passes_on_the_committed_corpus(retrieval_eval) -> None:
    """Lexical backend, zero keys — the committed golden set must clear the
    0.900 hit-rate threshold on the committed knowledge/ corpus."""
    assert retrieval_eval.run("lexical") == 0


def test_eval_fails_when_expected_doc_is_unretrievable(
    retrieval_eval, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Non-zero exit is load-bearing: a renamed/deleted knowledge doc (or a
    broken retriever) must fail the gate, not print-and-pass."""
    cases = tmp_path / "retrieval_cases.jsonl"
    rows = [
        {"case_id": f"miss-{i}", "query": "zz-nonexistent-topic", "expected_doc_id": "no-such-doc"}
        for i in range(3)
    ]
    cases.write_text("\n".join(json.dumps(r) for r in rows) + "\n", encoding="utf-8")
    monkeypatch.setattr(retrieval_eval, "CASES", cases)
    assert retrieval_eval.run("lexical") == 1
