/**
 * TypeScript mirror of `src/peterpan/schemas.py`.
 *
 * schemas.py is the source of truth — regenerate, never diverge.
 *
 * Conventions:
 * - pydantic `datetime` fields → ISO-8601 strings (what the JSON wire format carries).
 * - pydantic `StrEnum` → string-literal union types plus a frozen values array
 *   for iteration/validation at runtime.
 * - Field defaults and numeric bounds are documented but enforced server-side;
 *   the TS layer mirrors shape, not validation.
 */

// ---------------------------------------------------------------------------
// Severity
// ---------------------------------------------------------------------------

export const SEVERITIES = ["P1", "P2", "P3", "P4"] as const;
export type Severity = (typeof SEVERITIES)[number];

// ---------------------------------------------------------------------------
// Alert — inbound signal from monitoring (Grafana webhook, pager, etc.)
// ---------------------------------------------------------------------------

export interface Alert {
  id: string;
  source: string;
  title: string;
  description: string;
  severity: Severity;
  /** ISO-8601 datetime. */
  received_at: string;
  labels: Record<string, string>;
}

// ---------------------------------------------------------------------------
// Evidence — one piece of collected context, always with a citation trail
// ---------------------------------------------------------------------------

export interface Evidence {
  /** metric | log | deploy | runbook | past_incident | screenshot */
  kind: string;
  summary: string;
  /** Where this came from — URL, file, query. Never empty. */
  source: string;
  /** 0.0 <= confidence < 1.0 — evidence never claims certainty. */
  confidence: number;
}

// ---------------------------------------------------------------------------
// IncidentStory — the explained incident the Dynamic Incident Dashboard renders
// ---------------------------------------------------------------------------

/**
 * Honest runtime provenance for an incident run. Additive — older producers
 * omit this and consumers treat defaults as fixture/off.
 */
export interface ProviderReport {
  /** off | anthropic | bedrock | deterministic-fallback — what actually ran */
  llm: string;
  /** off | anthropic | bedrock — PP_LLM intent (may differ when llm_fallback) */
  configured_llm: string;
  llm_fallback: boolean;
  /** lexical | pinecone | fallback */
  rag_backend: string;
  rag_fallback: boolean;
  rag_fallback_reason: string;
  /** floor | torch | floor-fallback */
  predictor: string;
  predictor_model_version: string;
  /** local | agentcore | local-fallback */
  agent_provider: string;
}

export interface IncidentStory {
  alert: Alert;
  what_changed: string;
  probable_cause: string;
  /** 0.0 <= confidence < 1.0 — the system never claims certainty. */
  confidence: number;
  evidence: Evidence[];
  repair_options: string[];
  providers: ProviderReport;
}

// ---------------------------------------------------------------------------
// ActionRisk / ActionPreview — the human-approval gate
// ---------------------------------------------------------------------------

export const ACTION_RISKS = ["read_only", "low", "high"] as const;
export type ActionRisk = (typeof ACTION_RISKS)[number];

/**
 * A proposed action. HIGH-risk actions are never auto-executed — they require
 * an explicit human approval, recorded with who/when.
 */
export interface ActionPreview {
  action: string;
  risk: ActionRisk;
  rationale: string;
  requires_approval: boolean;
  approved_by: string | null;
  /** ISO-8601 datetime. */
  approved_at: string | null;
}

/** Mirror of `ActionPreview.executable` (a computed property in Python). */
export function isExecutable(preview: ActionPreview): boolean {
  return !preview.requires_approval || preview.approved_by !== null;
}

// ---------------------------------------------------------------------------
// GuardrailVerdict
// ---------------------------------------------------------------------------

export interface GuardrailVerdict {
  passed: boolean;
  flags: string[];
  reason: string;
}

// ---------------------------------------------------------------------------
// Prediction
// ---------------------------------------------------------------------------

export interface Prediction {
  incident_class: string;
  severity: Severity;
  /** 0.0 <= confidence < 1.0 — the floor never claims certainty. */
  confidence: number;
  /** floor | torch | floor-fallback */
  mode: string;
  /** Empty when floor-only / unavailable. */
  model_version: string;
}

// ---------------------------------------------------------------------------
// RagResult
// ---------------------------------------------------------------------------

export interface RagResult {
  query: string;
  matches: Evidence[];
  insight: string;
  /** lexical | pinecone | fallback — actual backend that served results. */
  backend: string;
  /** lexical | pinecone — PP_RAG_BACKEND intent (may differ when fallback). */
  configured_backend: string;
  fallback: boolean;
  fallback_reason: string;
}

// ---------------------------------------------------------------------------
// AgentRun
// ---------------------------------------------------------------------------

export interface AgentRun {
  query: string;
  answer: string;
  tools_used: string[];
  reasoning_steps: string[];
  token_cost_usd: number;
}

// ---------------------------------------------------------------------------
// PanelKind / Panel / DashboardSpec — "draw me the problem"
// ---------------------------------------------------------------------------

export const PANEL_KINDS = ["stat", "table", "markdown", "mermaid"] as const;
export type PanelKind = (typeof PANEL_KINDS)[number];

/**
 * One dashboard panel. `source` (when set) must cite real evidence — the
 * dashboard inherits the citation-trail invariant.
 */
export interface Panel {
  kind: PanelKind;
  title: string;
  /** stat value / markdown body / mermaid graph */
  content: string;
  /** TABLE only. */
  rows: Record<string, string>[];
  source: string | null;
}

/**
 * A renderable dashboard: the answer to "draw me the problem".
 */
export interface DashboardSpec {
  title: string;
  problem: string;
  /** "llm" | "deterministic-fallback" */
  generated_by: string;
  panels: Panel[];
}

// ---------------------------------------------------------------------------
// GrafanaDashboardPreview — validated Grafana JSON model, preview/dry-run ONLY
// ---------------------------------------------------------------------------

/**
 * A validated Grafana dashboard JSON model — preview/dry-run ONLY.
 * Publishing to a live Grafana is a separate, explicit production action
 * that does not exist in this codebase; nothing behind this shape talks to
 * a network. `validated === false` means the preview failed a safety check
 * and must not be imported — `warnings` says why.
 */
export interface GrafanaDashboardPreview {
  title: string;
  /** The operator's problem statement, verbatim (data, not code). */
  objective: string;
  /** "grafana-exporter/<spec.generated_by>" */
  generated_by: string;
  panel_titles: string[];
  warnings: string[];
  validated: boolean;
  /** Importable Grafana model (schemaVersion 39). */
  dashboard_json: Record<string, unknown>;
}

// ---------------------------------------------------------------------------
// UsageRow / UsageAggregate — GET /os/usage (PETER PAN OS metering table)
// ---------------------------------------------------------------------------

/** One group row from GET /os/usage (aggregate by agent|model|service). */
export interface UsageRow {
  calls: number;
  input_tokens: number;
  output_tokens: number;
  cost_usd: number;
}

/** Wire shape of GET /os/usage — map keyed by the chosen grouping dimension. */
export type UsageAggregate = Record<string, UsageRow>;

// ---------------------------------------------------------------------------
// Deployment — mirrors schemas.py (merged in PR #33)
// ---------------------------------------------------------------------------

export interface Deployment {
  id: string;
  service: string;
  version: string;
  /** ISO-8601 datetime. */
  deployed_at: string;
  author: string;
  summary: string;
  labels: Record<string, string>;
}

// ---------------------------------------------------------------------------
// Feedback — mirrors schemas.py (merged in PR #33)
// ---------------------------------------------------------------------------

export const FEEDBACK_VERDICTS = ["helpful", "wrong", "partial"] as const;
export type FeedbackVerdict = (typeof FEEDBACK_VERDICTS)[number];

export interface Feedback {
  trace_id: string;
  verdict: FeedbackVerdict;
  comment: string;
  submitted_by: string;
  /** ISO-8601 datetime. */
  submitted_at: string;
  // Structured outcome fields (additive, PR #53) — all optional; null/absent
  // means "not answered". Mirrors the enriched schemas.py Feedback.
  alert_id?: string | null;
  root_cause_correct?: boolean | null;
  recommendation_correct?: boolean | null;
  dashboard_useful?: boolean | null;
  final_root_cause?: string;
  resolution_action?: string;
  /** Human's stated certainty, 0..1 — MAY be 1.0 (the confidence < 1.0
   *  invariant binds system outputs, not analyst input). */
  analyst_confidence?: number | null;
}
