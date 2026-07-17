"""Knowledge base loader — the files under knowledge/ ARE the corpus.

Both retrieval backends (lexical fixture and Pinecone) build from these same
files, so a citation can never point at a document that doesn't exist and
the corpus can never drift from what's committed.
"""

from __future__ import annotations

from pathlib import Path

from peterpan.schemas import Evidence

KNOWLEDGE_ROOT = Path(__file__).parent.parent.parent / "knowledge"

_KIND_BY_DIR = {"runbooks": "runbook", "incidents": "past_incident"}


def _summarize(text: str) -> str:
    """Title + the symptom/what-happened line — keyword-rich for retrieval."""
    lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
    title = lines[0].lstrip("# ") if lines else ""
    detail = next(
        (
            ln.replace("**Symptoms:**", "").replace("**What happened:**", "").strip()
            for ln in lines
            if ln.startswith(("**Symptoms:**", "**What happened:**"))
        ),
        "",
    )
    return f"{title}: {detail}"[:300]


def load_corpus(root: Path | None = None) -> list[Evidence]:
    """One Evidence entry per knowledge document, source = repo-relative path."""
    base = root or KNOWLEDGE_ROOT
    corpus: list[Evidence] = []
    for path in sorted(base.rglob("*.md")):
        kind = _KIND_BY_DIR.get(path.parent.name, "document")
        rel = path.relative_to(base.parent).as_posix()
        corpus.append(
            Evidence(
                kind=kind,
                summary=_summarize(path.read_text(encoding="utf-8")),
                source=rel,
                confidence=0.0,
            )
        )
    return corpus


def load_full_text(source: str) -> str:
    """Fetch a cited document's full text (UI drill-down / LLM context)."""
    path = KNOWLEDGE_ROOT.parent / source
    if not path.is_file() or KNOWLEDGE_ROOT not in path.resolve().parents:
        raise FileNotFoundError(f"not a knowledge document: {source}")
    return path.read_text(encoding="utf-8")
