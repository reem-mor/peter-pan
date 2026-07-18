/**
 * Synthetic on-call roster. Every name is deliberately fake (surnames are
 * test-infrastructure words) — no real people, ever (synthetic-data
 * invariant).
 */

export interface EscalationStep {
  level: number;
  role: string;
  person: string;
  respondWithin: string;
  channel: string;
}

export interface ServiceOwner {
  service: string;
  team: string;
  primary: string;
  runbook: string;
}

export const FIXTURE_ESCALATION: EscalationStep[] = [
  {
    level: 1,
    role: "Primary on-call",
    person: "Riley Sandbox",
    respondWithin: "5 min",
    channel: "pager",
  },
  {
    level: 2,
    role: "Secondary on-call",
    person: "Morgan Mirage",
    respondWithin: "10 min",
    channel: "pager",
  },
  {
    level: 3,
    role: "Team lead",
    person: "Casey Canary",
    respondWithin: "15 min",
    channel: "phone",
  },
  {
    level: 4,
    role: "Incident commander",
    person: "Devon Drill",
    respondWithin: "20 min",
    channel: "phone",
  },
];

export const FIXTURE_OWNERS: ServiceOwner[] = [
  {
    service: "checkout",
    team: "Commerce",
    primary: "Riley Sandbox",
    runbook: "knowledge/runbooks/checkout.md",
  },
  {
    service: "gateway",
    team: "Edge",
    primary: "Morgan Mirage",
    runbook: "knowledge/runbooks/gateway.md",
  },
  {
    service: "orders",
    team: "Commerce",
    primary: "Jamie Fixture",
    runbook: "knowledge/runbooks/orders.md",
  },
  {
    service: "db",
    team: "Data Platform",
    primary: "Casey Canary",
    runbook: "knowledge/runbooks/db-connection-pool.md",
  },
  {
    service: "platform-network",
    team: "Infra",
    primary: "Devon Drill",
    runbook: "knowledge/runbooks/dns.md",
  },
  {
    service: "rag / predictor / agent",
    team: "AI Platform",
    primary: "Sam Staging",
    runbook: "knowledge/runbooks/agent-mesh.md",
  },
];
