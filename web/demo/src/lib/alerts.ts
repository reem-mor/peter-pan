import type { Severity } from "@peterpan/types";

/** Demo alert picker catalog. Ids (and titles/severities) mirror the
 * fixture-first DEMO_ALERTS dict in src/peterpan/services/agent.py — the
 * SSE endpoint resolves `alert_id` against that catalog, so keep in sync. */
export interface DemoAlertRef {
  id: string;
  title: string;
  severity: Severity;
  source: string;
}

export const DEMO_ALERTS: readonly DemoAlertRef[] = [
  { id: "demo-oom", title: "checkout OOMKilled", severity: "P1", source: "grafana" },
  { id: "demo-latency", title: "timeout on payments API", severity: "P2", source: "pager" },
  { id: "demo-5xx", title: "checkout returning 5xx", severity: "P2", source: "grafana" },
];
