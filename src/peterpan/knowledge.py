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
_DETAIL_MARKERS = ("**Symptoms:**", "**What happened:**")


def _kind_for(path: Path, base: Path) -> str:
    """Classify by ancestor dir, not just the immediate parent — so incidents
    fed under incidents/memory/ still index as past_incident, not document."""
    parts = path.relative_to(base).parts
    for dirname, kind in _KIND_BY_DIR.items():
        if dirname in parts:
            return kind
    return "document"


def _summarize(text: str) -> str:
    """Title + the symptom/what-happened paragraph — keyword-rich for retrieval.

    Hard-wrapped paragraphs are joined up to the next blank line *before* the
    300-char cut, so root-cause keywords on continuation lines (which retrieval
    keys on) survive instead of being truncated to the first physical line."""
    raw = text.splitlines()
    nonblank = [ln.strip() for ln in raw if ln.strip()]
    title = nonblank[0].lstrip("# ") if nonblank else ""

    detail = ""
    for i, ln in enumerate(raw):
        if ln.strip().startswith(_DETAIL_MARKERS):
            para = [ln.strip()]
            for cont in raw[i + 1 :]:
                if not cont.strip():  # blank line ends the paragraph
                    break
                para.append(cont.strip())
            detail = " ".join(para)
            for marker in _DETAIL_MARKERS:
                detail = detail.replace(marker, "")
            detail = detail.strip()
            break
    return f"{title}: {detail}"[:300]


def load_corpus(root: Path | None = None) -> list[Evidence]:
    """One Evidence entry per knowledge document, source = repo-relative path."""
    base = root or KNOWLEDGE_ROOT
    corpus: list[Evidence] = []
    for path in sorted(base.rglob("*.md")):
        kind = _kind_for(path, base)
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
