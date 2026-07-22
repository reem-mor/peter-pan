"""peterpan.knowledge.load_full_text — the one loader that resolves a
caller-supplied source string to a filesystem read. Its traversal guard is
security logic and had zero direct coverage (release-audit P2)."""

from __future__ import annotations

import pytest

from peterpan.knowledge import KNOWLEDGE_ROOT, load_full_text


def test_loads_a_real_knowledge_document() -> None:
    text = load_full_text("knowledge/runbooks/checkout-oom.md")
    assert "OOM" in text


@pytest.mark.parametrize(
    "source",
    [
        "../pyproject.toml",
        "knowledge/../pyproject.toml",
        "knowledge/../../etc/passwd",
        "pyproject.toml",
        "knowledge/runbooks/no-such-file.md",
    ],
    ids=["parent-escape", "inside-then-escape", "deep-escape", "sibling-file", "missing-doc"],
)
def test_rejects_paths_outside_the_knowledge_root(source: str) -> None:
    with pytest.raises(FileNotFoundError, match="not a knowledge document"):
        load_full_text(source)


def test_absolute_path_outside_root_rejected() -> None:
    outside = str((KNOWLEDGE_ROOT.parent / "pyproject.toml").resolve())
    with pytest.raises(FileNotFoundError, match="not a knowledge document"):
        load_full_text(outside)
