"""Shared typed contracts for every PETER PAN service.

These schemas ARE the product spec: every service speaks them, the WebUI
renders them, and tests assert against them. Changing one is a contract
change — do it deliberately (see CLAUDE.md).
"""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, Field


class Severity(StrEnum):
    P1 = "P1"
    P2 = "P2"
    P3 = "P3"
    P4 = "P4"


class Alert(BaseModel):
    """Inbound signal from monitoring (Grafana webhook, pager, etc.)."""

    id: str
    source: str
    title: str
    description: str = ""
    severity: Severity = Severity.P3
    received_at: datetime
    labels: dict[str, str] = Field(default_factory=dict)


class Evidence(BaseModel):
    """One piece of collected context, always with a citation trail."""

    kind: str  # metric | log | deploy | runbook | past_incident | screenshot
    summary: str
    source: str  # where this came from — URL, file, query. Never empty.
    confidence: float = Field(ge=0.0, le=1.0)


class IncidentStory(BaseModel):
    """The explained incident: what changed, likely cause, evidence, options.

    This is what the Dynamic Incident Dashboard renders.
    """

    alert: Alert
    what_changed: str
    probable_cause: str
    confidence: float = Field(ge=0.0, le=1.0)
    evidence: list[Evidence]
    repair_options: list[str]


class ActionRisk(StrEnum):
    READ_ONLY = "read_only"
    LOW = "low"
    HIGH = "high"


class ActionPreview(BaseModel):
    """A proposed action. HIGH-risk actions are never auto-executed —
    they require an explicit human approval, recorded with who/when."""

    action: str
    risk: ActionRisk
    rationale: str
    requires_approval: bool
    approved_by: str | None = None
    approved_at: datetime | None = None

    @property
    def executable(self) -> bool:
        return not self.requires_approval or self.approved_by is not None


class GuardrailVerdict(BaseModel):
    passed: bool
    flags: list[str] = Field(default_factory=list)
    reason: str = ""


class Prediction(BaseModel):
    incident_class: str
    severity: Severity
    confidence: float = Field(ge=0.0, le=1.0)


class RagResult(BaseModel):
    query: str
    matches: list[Evidence]
    insight: str


class AgentRun(BaseModel):
    query: str
    answer: str
    tools_used: list[str]
    reasoning_steps: list[str]
    token_cost_usd: float = 0.0


class PanelKind(StrEnum):
    STAT = "stat"
    TABLE = "table"
    MARKDOWN = "markdown"
    MERMAID = "mermaid"


class Panel(BaseModel):
    """One dashboard panel. `source` (when set) must cite real evidence —
    the dashboard inherits the citation-trail invariant."""

    kind: PanelKind
    title: str
    content: str  # stat value / markdown body / mermaid graph
    rows: list[dict[str, str]] = Field(default_factory=list)  # TABLE only
    source: str | None = None


class DashboardSpec(BaseModel):
    """A renderable dashboard: the answer to 'draw me the problem'.

    Rendered by the Streamlit UI today; the same spec maps 1:1 onto Grafana
    panel JSON when the Grafana exporter lands.
    """

    title: str
    problem: str
    generated_by: str  # "llm" | "deterministic-fallback"
    panels: list[Panel]
