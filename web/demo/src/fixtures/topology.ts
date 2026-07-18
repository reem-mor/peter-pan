/**
 * Static synthetic service-dependency map for the "draw me the problem"
 * incident graph (brief §6.7). Everything here is invented demo data —
 * no real services, owners, or incidents (repo golden rule 3).
 *
 * Alert ids mirror DEMO_ALERTS in src/peterpan/services/agent.py.
 */
import type { Deployment } from "@peterpan/types";

export type ServiceKind = "gateway" | "service" | "database" | "cache";
export type EdgeKind = "http" | "sql" | "cache";

export interface ServiceNodeSpec {
  id: string;
  label: string;
  kind: ServiceKind;
  /** Fixed layout position (left-to-right request flow). */
  position: { x: number; y: number };
}

export interface ServiceEdgeSpec {
  /** Caller (traffic flows source → target). */
  source: string;
  target: string;
  kind: EdgeKind;
}

export const SERVICES: readonly ServiceNodeSpec[] = [
  { id: "gateway", label: "gateway", kind: "gateway", position: { x: 0, y: 90 } },
  { id: "checkout", label: "checkout", kind: "service", position: { x: 230, y: 90 } },
  { id: "payments", label: "payments", kind: "service", position: { x: 460, y: 90 } },
  { id: "payments-db", label: "payments-db", kind: "database", position: { x: 690, y: 90 } },
  { id: "cache", label: "cache", kind: "cache", position: { x: 345, y: 230 } },
];

export const SERVICE_EDGES: readonly ServiceEdgeSpec[] = [
  { source: "gateway", target: "checkout", kind: "http" },
  { source: "checkout", target: "payments", kind: "http" },
  { source: "checkout", target: "cache", kind: "cache" },
  { source: "payments", target: "payments-db", kind: "sql" },
  { source: "payments", target: "cache", kind: "cache" },
];

/** How each demo alert maps onto the topology: which service the signal
 * fired on, and the likely root-cause path suggested by the retrieved
 * evidence (see fixtures/replay.ts for the citations). */
export interface IncidentMapping {
  affectedService: string;
  /** Ordered service ids; edges along this path get emphasized. */
  rootCausePath: readonly string[];
  rationale: string;
}

export const INCIDENT_MAPPINGS: Record<string, IncidentMapping> = {
  "demo-oom": {
    affectedService: "checkout",
    rootCausePath: ["checkout", "cache"],
    rationale:
      "OOMKilled on checkout; past incident INC-2263 points at unbounded session-cache growth.",
  },
  "demo-latency": {
    affectedService: "payments",
    rootCausePath: ["payments", "payments-db"],
    rationale:
      "p99 breach after the 14:00 deploy; INC-2231 points at the payments-db connection pool.",
  },
  "demo-5xx": {
    affectedService: "checkout",
    rootCausePath: ["checkout"],
    rationale:
      "5xx spike correlates with the canary rollout of checkout itself.",
  },
};

/** Upstream consumers of `serviceId` (callers, transitively) — the blast
 * radius: user-facing paths that degrade when this service does. */
export function blastRadius(serviceId: string): Set<string> {
  const callers = new Map<string, string[]>();
  for (const e of SERVICE_EDGES) {
    const list = callers.get(e.target) ?? [];
    list.push(e.source);
    callers.set(e.target, list);
  }
  const impacted = new Set<string>();
  const queue = [serviceId];
  while (queue.length > 0) {
    const current = queue.pop();
    if (current === undefined) break;
    for (const caller of callers.get(current) ?? []) {
      if (!impacted.has(caller)) {
        impacted.add(caller);
        queue.push(caller);
      }
    }
  }
  impacted.delete(serviceId);
  return impacted;
}

// ---------------------------------------------------------------------------
// Per-service detail for the click-through side panel (all synthetic).
// ---------------------------------------------------------------------------

export interface ServiceDetail {
  owner: { team: string; oncall: string };
  deploys: Deployment[];
  /** Ids from the demo alert catalog that involve this service. */
  relatedAlerts: readonly string[];
}

export const SERVICE_DETAILS: Record<string, ServiceDetail> = {
  gateway: {
    owner: { team: "edge-platform", oncall: "rotation: edge-primary" },
    deploys: [
      {
        id: "dep-9101",
        service: "gateway",
        version: "v3.2.0",
        deployed_at: "2026-01-01T09:10:00Z",
        author: "synthetic.dev",
        summary: "TLS config refresh; no routing changes.",
        labels: { env: "mirage" },
      },
    ],
    relatedAlerts: [],
  },
  checkout: {
    owner: { team: "storefront", oncall: "rotation: storefront-primary" },
    deploys: [
      {
        id: "dep-9114",
        service: "checkout",
        version: "v2.4.1",
        deployed_at: "2026-01-01T13:55:00Z",
        author: "synthetic.dev",
        summary: "Canary rollout: new session-cache eviction policy.",
        labels: { env: "mirage", strategy: "canary" },
      },
      {
        id: "dep-9088",
        service: "checkout",
        version: "v2.4.0",
        deployed_at: "2025-12-30T11:20:00Z",
        author: "synthetic.dev",
        summary: "Order reconciler background job.",
        labels: { env: "mirage" },
      },
    ],
    relatedAlerts: ["demo-oom", "demo-5xx"],
  },
  payments: {
    owner: { team: "money-movement", oncall: "rotation: payments-primary" },
    deploys: [
      {
        id: "dep-9120",
        service: "payments",
        version: "v1.9.3",
        deployed_at: "2026-01-01T14:00:00Z",
        author: "synthetic.dev",
        summary: "Config override consolidating DB pool settings.",
        labels: { env: "mirage" },
      },
    ],
    relatedAlerts: ["demo-latency"],
  },
  "payments-db": {
    owner: { team: "data-infra", oncall: "rotation: dbre-primary" },
    deploys: [
      {
        id: "dep-9050",
        service: "payments-db",
        version: "pg-16.3-r2",
        deployed_at: "2025-12-28T08:00:00Z",
        author: "synthetic.dev",
        summary: "Minor version patch window.",
        labels: { env: "mirage" },
      },
    ],
    relatedAlerts: ["demo-latency"],
  },
  cache: {
    owner: { team: "data-infra", oncall: "rotation: cache-primary" },
    deploys: [
      {
        id: "dep-9047",
        service: "cache",
        version: "redis-7.4.1",
        deployed_at: "2025-12-27T10:30:00Z",
        author: "synthetic.dev",
        summary: "Cluster resize, no eviction policy change.",
        labels: { env: "mirage" },
      },
    ],
    relatedAlerts: ["demo-oom"],
  },
};
