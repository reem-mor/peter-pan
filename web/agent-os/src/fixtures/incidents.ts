/**
 * Synthetic incident catalog — fixture data in the style of
 * data/synthetic/alerts.jsonl and knowledge/incidents/*.md.
 * No real incidents, systems, or people (synthetic-data invariant).
 */

import type { Severity } from "@peterpan/types";

export type IncidentStatus = "investigating" | "mitigated" | "resolved";

export interface IncidentSummary {
  id: string;
  title: string;
  service: string;
  severity: Severity;
  status: IncidentStatus;
  incidentClass: string;
  /** ISO-8601 datetime. */
  startedAt: string;
  durationMin: number | null;
  summary: string;
  /** Confidence of the agent's story, always < 1.0 (product invariant). */
  storyConfidence: number;
}

export const FIXTURE_INCIDENTS: IncidentSummary[] = [
  {
    id: "INC-2481",
    title: "checkout p99 latency above threshold after 13:40 deploy",
    service: "checkout",
    severity: "P2",
    status: "investigating",
    incidentClass: "latency_regression",
    startedAt: "2026-07-18T10:42:00Z",
    durationMin: null,
    summary:
      "p99 rose 4x within ten minutes of the checkout v2026.07.18.1 rollout; agent correlates with the deploy and proposes rollback.",
    storyConfidence: 0.81,
  },
  {
    id: "INC-2478",
    title: "5xx storm on public API canary",
    service: "gateway",
    severity: "P1",
    status: "mitigated",
    incidentClass: "availability",
    startedAt: "2026-07-17T22:05:00Z",
    durationMin: 18,
    summary:
      "Canary error rate hit 14%; traffic shifted back to stable. Root-cause story points at a config flag enabled only on canary.",
    storyConfidence: 0.87,
  },
  {
    id: "INC-2470",
    title: "orders → inventory connection refused",
    service: "orders",
    severity: "P2",
    status: "resolved",
    incidentClass: "connectivity",
    startedAt: "2026-07-16T14:31:00Z",
    durationMin: 26,
    summary:
      "Inventory pod cycled during a node drain; orders retried into a dead endpoint. Resolved by draining with pod-disruption budgets.",
    storyConfidence: 0.9,
  },
  {
    id: "INC-2465",
    title: "disk usage 97% on db-2 primary volume",
    service: "db",
    severity: "P1",
    status: "resolved",
    incidentClass: "resource_exhaustion",
    startedAt: "2026-07-15T06:12:00Z",
    durationMin: 41,
    summary:
      "WAL retention misconfiguration after the replication change; agent story cited the retention diff and the runbook cleanup path.",
    storyConfidence: 0.84,
  },
  {
    id: "INC-2456",
    title: "internal DNS resolution failure after policy change",
    service: "platform-network",
    severity: "P1",
    status: "resolved",
    incidentClass: "connectivity",
    startedAt: "2026-07-14T11:47:00Z",
    durationMin: 23,
    summary:
      "Egress policy tightened and blocked UDP/53 to the in-cluster resolver; reverting the policy restored resolution immediately.",
    storyConfidence: 0.92,
  },
  {
    id: "INC-2449",
    title: "TLS certificate expiring on api gateway",
    service: "gateway",
    severity: "P3",
    status: "resolved",
    incidentClass: "certificate",
    startedAt: "2026-07-12T09:00:00Z",
    durationMin: 55,
    summary:
      "20-hour expiry warning; renewal job re-run and verified against the live listener per the cert-rotation runbook.",
    storyConfidence: 0.88,
  },
];
