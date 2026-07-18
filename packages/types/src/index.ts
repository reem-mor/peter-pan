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

export interface IncidentStory {
  alert: Alert;
  what_changed: string;
  probable_cause: string;
  /** 0.0 <= confidence <= 1.0 */
  confidence: number;
  evidence: Evidence[];
  repair_options: string[];
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
  /** 0.0 <= confidence <= 1.0 */
  confidence: number;
}

// ---------------------------------------------------------------------------
// RagResult
// ---------------------------------------------------------------------------

export interface RagResult {
  query: string;
  matches: Evidence[];
  insight: string;
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
// Deployment — mirrored from the WS8 spec (lands in schemas.py on
// phase0/contracts-gates-graphify; keep in sync when that branch merges)
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
// Feedback — mirrored from the WS8 spec (same caveat as Deployment)
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
}
