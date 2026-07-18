/**
 * Synthetic deployment feed — typed against the shared Deployment schema
 * (@peterpan/types mirrors schemas.py). Incident correlation is a console
 * concern, so it lives in a local wrapper instead of the product schema.
 */

import type { Deployment } from "@peterpan/types";

export interface DeploymentRow {
  deployment: Deployment;
  /** Incident id when the change-timeline correlates this deploy. */
  correlatedIncident: string | null;
}

export const FIXTURE_DEPLOYMENTS: DeploymentRow[] = [
  {
    deployment: {
      id: "dep-90412",
      service: "checkout",
      version: "v2026.07.18.1",
      deployed_at: "2026-07-18T10:31:00Z",
      author: "Riley Sandbox",
      summary: "Enable the new pricing rules engine behind a flag",
      labels: { env: "prod", strategy: "rolling" },
    },
    correlatedIncident: "INC-2481",
  },
  {
    deployment: {
      id: "dep-90398",
      service: "gateway",
      version: "v2026.07.17.4",
      deployed_at: "2026-07-17T21:48:00Z",
      author: "Morgan Mirage",
      summary: "Canary: request-coalescing flag on 10% of traffic",
      labels: { env: "prod", strategy: "canary" },
    },
    correlatedIncident: "INC-2478",
  },
  {
    deployment: {
      id: "dep-90371",
      service: "rag",
      version: "v2026.07.17.1",
      deployed_at: "2026-07-17T13:02:00Z",
      author: "Casey Canary",
      summary: "Chunk-metadata backfill for the runbook corpus",
      labels: { env: "prod", strategy: "rolling" },
    },
    correlatedIncident: null,
  },
  {
    deployment: {
      id: "dep-90344",
      service: "platform-network",
      version: "policy-2026-07-14a",
      deployed_at: "2026-07-14T11:40:00Z",
      author: "Devon Drill",
      summary: "Tighten namespace egress rules (reverted at 12:07)",
      labels: { env: "prod", strategy: "config" },
    },
    correlatedIncident: "INC-2456",
  },
  {
    deployment: {
      id: "dep-90310",
      service: "predictor",
      version: "v2026.07.13.2",
      deployed_at: "2026-07-13T15:22:00Z",
      author: "Jamie Fixture",
      summary: "Retrain severity floor on June incident set",
      labels: { env: "prod", strategy: "blue-green" },
    },
    correlatedIncident: null,
  },
  {
    deployment: {
      id: "dep-90287",
      service: "orders",
      version: "v2026.07.12.3",
      deployed_at: "2026-07-12T09:44:00Z",
      author: "Riley Sandbox",
      summary: "Retry budget + jitter on inventory client",
      labels: { env: "prod", strategy: "rolling" },
    },
    correlatedIncident: null,
  },
];
