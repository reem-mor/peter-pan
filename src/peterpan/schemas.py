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
    # lt=1.0 (not le): retrieval/evidence never claims certainty. Every producer
    # caps below 1.0 (predictor floors, rag scores capped at 0.99) — the bound
    # makes the confidence < 1.0 invariant a type-level guarantee.
    confidence: float = Field(ge=0.0, lt=1.0)


class ProviderReport(BaseModel):
    """Honest runtime provenance for an incident run.

    Additive contract: older clients ignore unknown fields; older producers
    omit this object and consumers see the safe defaults (fixture / off).
    Never claim a live cloud provider when a deterministic fallback ran.
    """

    llm: str = "off"  # off | anthropic | bedrock | deterministic-fallback
    llm_fallback: bool = False
    rag_backend: str = "lexical"  # lexical | pinecone | fallback
    rag_fallback: bool = False
    rag_fallback_reason: str = ""
    predictor: str = "floor"  # floor | torch | floor-fallback
    predictor_model_version: str = ""
    agent_provider: str = "local"  # local | agentcore | local-fallback


class IncidentStory(BaseModel):
    """The explained incident: what changed, likely cause, evidence, options.

    This is what the Dynamic Incident Dashboard renders.
    """

    alert: Alert
    what_changed: str
    probable_cause: str
    # lt=1.0: same type-level guarantee as Evidence — every producer caps at
    # 0.9 (min(confidence, 0.9) in agent.py / graph.py / llm.py).
    confidence: float = Field(ge=0.0, lt=1.0)
    evidence: list[Evidence]
    repair_options: list[str]
    providers: ProviderReport = Field(default_factory=ProviderReport)


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


class Deployment(BaseModel):
    """A deployment event — the change-correlation signal for incident stories."""

    id: str
    service: str
    version: str
    deployed_at: datetime
    author: str = ""
    summary: str = ""
    labels: dict[str, str] = Field(default_factory=dict)


class FeedbackVerdict(StrEnum):
    HELPFUL = "helpful"
    WRONG = "wrong"
    PARTIAL = "partial"


class Feedback(BaseModel):
    """Operator feedback on an agent output, keyed to its trace for the
    learning loop. `trace_id` links back to usage/observability records.

    Every field beyond the original five is OPTIONAL and defaulted — old
    JSONL rows and old clients stay valid (additive contract change). The
    structured booleans exist so the learning loop can measure specific
    failure modes instead of parsing free-text comments.
    """

    trace_id: str
    verdict: FeedbackVerdict
    comment: str = ""
    submitted_by: str
    submitted_at: datetime

    # Structured outcome fields (learning-loop §feedback). None = not answered.
    alert_id: str | None = None
    root_cause_correct: bool | None = None
    recommendation_correct: bool | None = None
    dashboard_useful: bool | None = None
    final_root_cause: str = ""  # what it actually was, in the analyst's words
    resolution_action: str = ""  # what actually fixed it
    # le=1.0 deliberately: this is a HUMAN's stated certainty, not a system
    # output — the confidence < 1.0 invariant binds what the system claims,
    # never what an analyst reports.
    analyst_confidence: float | None = Field(default=None, ge=0.0, le=1.0)


class GuardrailVerdict(BaseModel):
    passed: bool
    flags: list[str] = Field(default_factory=list)
    reason: str = ""


class Prediction(BaseModel):
    incident_class: str
    severity: Severity
    # lt=1.0: floor emits 0.75/0.3; the torch path caps at _CONFIDENCE_CAP.
    confidence: float = Field(ge=0.0, lt=1.0)
    # Additive diagnostics — defaults preserve legacy JSONL / clients.
    mode: str = "floor"  # floor | torch | floor-fallback
    model_version: str = ""  # empty when floor-only / unavailable


class RagResult(BaseModel):
    query: str
    matches: list[Evidence]
    insight: str
    # Additive: which backend actually served results (never mislabel fallback).
    backend: str = "lexical"  # lexical | pinecone | fallback
    fallback: bool = False
    fallback_reason: str = ""


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

    Rendered by the Streamlit UI today; peterpan.grafana exports the same
    spec as a validated Grafana JSON model preview.
    """

    title: str
    problem: str
    generated_by: str  # "llm" | "deterministic-fallback"
    panels: list[Panel]


class GrafanaDashboardPreview(BaseModel):
    """A validated Grafana dashboard JSON model — preview/dry-run ONLY.

    Publishing to a live Grafana is a separate, explicit production action
    that does not exist in this codebase; nothing here talks to a network.
    `validated=False` means the preview failed a safety check and must not
    be imported — `warnings` says why. Every panel description states why
    the panel was selected and cites story evidence where it exists.
    """

    title: str
    objective: str  # the operator's problem statement, verbatim (data, not code)
    generated_by: str  # "grafana-exporter/<spec.generated_by>"
    panel_titles: list[str]
    warnings: list[str] = Field(default_factory=list)
    validated: bool
    dashboard_json: dict[str, object]  # importable Grafana model (schemaVersion 39)
