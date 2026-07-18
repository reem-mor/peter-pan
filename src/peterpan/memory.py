"""Memory feed — resolved incidents become retrievable knowledge.

Closes the learning loop: story → human-approved resolution → a document
under knowledge/incidents/ → future alerts retrieve it as past_incident
evidence with a citation. Deterministic gates, enforced in the schema:

- `approved_by` is required and non-blank — nothing enters memory without a
  named human (Action-Preview philosophy applied to knowledge writes).
- `incident_id` is allowlisted (alert ids ride in on attacker-controllable
  input; the id becomes a filename, so traversal is rejected at parse time).
- The local markdown file is the SOURCE OF TRUTH. The Pinecone upsert is a
  best-effort index of it: failure raises MemoryFeedError and the caller
  reports `pinecone_synced: false` — it never rolls back the local write.
"""

from __future__ import annotations

import re
from pathlib import Path

from pydantic import BaseModel, Field, field_validator

from peterpan.knowledge import KNOWLEDGE_ROOT
from peterpan.schemas import Severity

# Mirrors the predictor's class vocabulary (floor + model). Kept literal so a
# schema reader sees the contract without chasing imports.
KNOWN_CLASSES = frozenset(
    {
        "resource_exhaustion",
        "connectivity",
        "latency",
        "availability",
        "security",
        "change_related",
        "unclassified",
    }
)

_ID_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,63}$")


class MemoryFeedError(Exception):
    """Pinecone-path failure. The local write is unaffected; callers report it."""


class MemoryRecord(BaseModel):
    """A resolved, human-approved incident ready to enter the knowledge base."""

    incident_id: str
    title: str = Field(min_length=3, max_length=200)
    incident_class: str
    severity: Severity
    what_happened: str = Field(min_length=10)
    resolution: str = Field(min_length=10)
    evidence_sources: list[str] = Field(default_factory=list)
    approved_by: str

    @field_validator("incident_id")
    @classmethod
    def _safe_id(cls, v: str) -> str:
        if not _ID_PATTERN.match(v) or ".." in v:
            raise ValueError("incident_id must match [A-Za-z0-9][A-Za-z0-9._-]{0,63}, no '..'")
        return v

    @field_validator("incident_class")
    @classmethod
    def _known_class(cls, v: str) -> str:
        if v not in KNOWN_CLASSES:
            raise ValueError(
                f"unknown incident_class {v!r}; expected one of {sorted(KNOWN_CLASSES)}"
            )
        return v

    @field_validator("approved_by")
    @classmethod
    def _named_approver(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("approved_by must name the approving human — memory writes are gated")
        return v.strip()


def to_markdown(record: MemoryRecord) -> str:
    """Render in the same shape as the committed incident docs, so
    knowledge._summarize (which keys on '**What happened:**') indexes it."""
    sources = ", ".join(record.evidence_sources) or "none recorded"
    return (
        f"# {record.incident_id} - {record.title}\n\n"
        f"**Severity:** {record.severity.value} - **Class:** {record.incident_class}\n\n"
        f"**What happened:** {record.what_happened}\n\n"
        f"**Resolution:** {record.resolution}\n\n"
        f"**Evidence sources:** {sources}\n\n"
        f"*Fed by the memory loop - approved by {record.approved_by}.*\n"
    )


def feed(record: MemoryRecord, root: Path | None = None) -> str:
    """Write the record into knowledge/incidents/. Idempotent by incident_id.

    Returns the repo-relative source path (what citations will use).
    """
    base = root or KNOWLEDGE_ROOT
    target = base / "incidents" / f"{record.incident_id}.md"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(to_markdown(record), encoding="utf-8")
    return target.relative_to(base.parent).as_posix()


def upsert_to_pinecone(record: MemoryRecord, source: str) -> None:
    """Index the fed document in Pinecone. Raises MemoryFeedError on any failure."""
    from peterpan.config import Settings

    settings = Settings()
    if not (settings.pinecone_api_key and settings.voyage_api_key):
        raise MemoryFeedError("pinecone upsert needs PINECONE_API_KEY and VOYAGE_API_KEY")
    try:
        import voyageai
        from pinecone import Pinecone

        embedding = (
            voyageai.Client(api_key=settings.voyage_api_key)
            .embed([to_markdown(record)], model=settings.voyage_model, input_type="document")
            .embeddings[0]
        )
        Pinecone(api_key=settings.pinecone_api_key).Index(settings.pinecone_index).upsert(
            vectors=[
                {
                    "id": source,  # same stable id scheme as scripts/ingest_knowledge.py
                    "values": embedding,
                    "metadata": {
                        "kind": "past_incident",
                        "summary": f"{record.incident_id} - {record.title}: {record.what_happened}"[
                            :300
                        ],
                        "source": source,
                    },
                }
            ]
        )
    except MemoryFeedError:
        raise
    except Exception as exc:
        raise MemoryFeedError(f"pinecone upsert failed: {type(exc).__name__}") from exc
