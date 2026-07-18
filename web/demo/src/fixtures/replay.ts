/**
 * Canned SSE replay fixture — the no-backend fallback (fixture-first rule).
 *
 * Frames were captured verbatim from the live deterministic endpoint
 * (`curl -N http://localhost:8004/agent/stream?alert_id=…`, mirage env,
 * PP_LLM unset), one array per DEMO_ALERTS id in
 * src/peterpan/services/agent.py. Only the `ts` fields vary run-to-run;
 * everything else is byte-identical to what the service emits.
 *
 * Synthetic data only — no real incidents or PII (repo golden rule 3).
 */
import type { StreamFrame } from "../lib/stream";

export const REPLAY_STREAMS: Record<string, readonly StreamFrame[]> = {
  "demo-oom": [
    {
      event: "step",
      data: {
        name: "classify",
        detail: "Classifying the alert against the deterministic floor.",
        ts: "2026-07-18T15:25:08.097435+00:00",
      },
    },
    {
      event: "step",
      data: {
        name: "retrieve",
        detail: "Retrieving runbooks and past incidents.",
        ts: "2026-07-18T15:25:08.160789+00:00",
      },
    },
    {
      event: "step",
      data: {
        name: "synthesize",
        detail: "Synthesizing the incident story (deterministic).",
        ts: "2026-07-18T15:25:08.211209+00:00",
      },
    },
    {
      event: "evidence",
      data: {
        kind: "metric",
        summary: "classified as resource_exhaustion at P1",
        source: "predictor:/predict",
        confidence: 0.75,
      },
    },
    {
      event: "evidence",
      data: {
        kind: "runbook",
        summary:
          "Runbook — checkout service OOM: `OOMKilled` restarts on checkout pods; memory at limit before kill.",
        source: "knowledge/runbooks/checkout-oom.md",
        confidence: 0.625,
      },
    },
    {
      event: "evidence",
      data: {
        kind: "past_incident",
        summary:
          "INC-2263 - Memory leak in session cache v2.3 (2026-05-21): Checkout pods OOMKilled every 6-8 hours; heap diffs showed unbounded session cache growth when the eviction job was disabled by a config regression.",
        source: "knowledge/incidents/INC-2263.md",
        confidence: 0.375,
      },
    },
    {
      event: "evidence",
      data: {
        kind: "past_incident",
        summary:
          "INC-2401 — checkout DB connection pool exhaustion (2026-06-18): the checkout service began returning 503s at 09:14 as its database connection pool saturated at 100% utilization. A background reconciler deployed that morning opened a connection per order row and never released it on the error path, s",
        source: "knowledge/incidents/INC-2401.md",
        confidence: 0.25,
      },
    },
    {
      event: "story",
      data: {
        alert: {
          id: "demo-oom",
          source: "grafana",
          title: "checkout OOMKilled",
          description: "pod restarted twice, memory at limit",
          severity: "P1",
          received_at: "2026-01-01T00:00:00Z",
          labels: {},
        },
        what_changed: "Signal 'checkout OOMKilled' from grafana",
        probable_cause: "resource_exhaustion",
        confidence: 0.75,
        evidence: [
          {
            kind: "metric",
            summary: "classified as resource_exhaustion at P1",
            source: "predictor:/predict",
            confidence: 0.75,
          },
          {
            kind: "runbook",
            summary:
              "Runbook — checkout service OOM: `OOMKilled` restarts on checkout pods; memory at limit before kill.",
            source: "knowledge/runbooks/checkout-oom.md",
            confidence: 0.625,
          },
          {
            kind: "past_incident",
            summary:
              "INC-2263 - Memory leak in session cache v2.3 (2026-05-21): Checkout pods OOMKilled every 6-8 hours; heap diffs showed unbounded session cache growth when the eviction job was disabled by a config regression.",
            source: "knowledge/incidents/INC-2263.md",
            confidence: 0.375,
          },
          {
            kind: "past_incident",
            summary:
              "INC-2401 — checkout DB connection pool exhaustion (2026-06-18): the checkout service began returning 503s at 09:14 as its database connection pool saturated at 100% utilization. A background reconciler deployed that morning opened a connection per order row and never released it on the error path, s",
            source: "knowledge/incidents/INC-2401.md",
            confidence: 0.25,
          },
        ],
        repair_options: [
          "raise memory/disk limits",
          "roll affected pods",
          "hunt the leak",
        ],
      },
    },
    { event: "done", data: { status: "done" } },
  ],
  "demo-latency": [
    {
      event: "step",
      data: {
        name: "classify",
        detail: "Classifying the alert against the deterministic floor.",
        ts: "2026-07-18T15:25:08.877793+00:00",
      },
    },
    {
      event: "step",
      data: {
        name: "retrieve",
        detail: "Retrieving runbooks and past incidents.",
        ts: "2026-07-18T15:25:08.941850+00:00",
      },
    },
    {
      event: "step",
      data: {
        name: "synthesize",
        detail: "Synthesizing the incident story (deterministic).",
        ts: "2026-07-18T15:25:08.993008+00:00",
      },
    },
    {
      event: "evidence",
      data: {
        kind: "metric",
        summary: "classified as latency at P2",
        source: "predictor:/predict",
        confidence: 0.75,
      },
    },
    {
      event: "evidence",
      data: {
        kind: "past_incident",
        summary:
          "INC-2231 — payment latency spike (2026-05-12): p95 on payments API rose 6× within 10 minutes of the 13:40 deploy. Connection pool to the payments DB was exhausted — the deploy halved the pool size via a mis-scoped config override.",
        source: "knowledge/incidents/INC-2231.md",
        confidence: 0.462,
      },
    },
    {
      event: "evidence",
      data: {
        kind: "past_incident",
        summary:
          "INC-2423 — bad deploy rolled back after error-rate spike (2026-06-27): the 14:05 deploy of the orders API shipped a serialization change that dropped a required field from the event schema. Consumers began rejecting messages and the orders API error rate climbed from 0.2% to 11% within three minutes",
        source: "knowledge/incidents/INC-2423.md",
        confidence: 0.415,
      },
    },
    {
      event: "evidence",
      data: {
        kind: "past_incident",
        summary:
          "INC-2401 — checkout DB connection pool exhaustion (2026-06-18): the checkout service began returning 503s at 09:14 as its database connection pool saturated at 100% utilization. A background reconciler deployed that morning opened a connection per order row and never released it on the error path, s",
        source: "knowledge/incidents/INC-2401.md",
        confidence: 0.354,
      },
    },
    {
      event: "story",
      data: {
        alert: {
          id: "demo-latency",
          source: "pager",
          title: "timeout on payments API",
          description: "p99 latency breached SLO after the 14:00 deploy",
          severity: "P2",
          received_at: "2026-01-01T00:00:00Z",
          labels: {},
        },
        what_changed: "Signal 'timeout on payments API' from pager",
        probable_cause: "latency",
        confidence: 0.75,
        evidence: [
          {
            kind: "metric",
            summary: "classified as latency at P2",
            source: "predictor:/predict",
            confidence: 0.75,
          },
          {
            kind: "past_incident",
            summary:
              "INC-2231 — payment latency spike (2026-05-12): p95 on payments API rose 6× within 10 minutes of the 13:40 deploy. Connection pool to the payments DB was exhausted — the deploy halved the pool size via a mis-scoped config override.",
            source: "knowledge/incidents/INC-2231.md",
            confidence: 0.462,
          },
          {
            kind: "past_incident",
            summary:
              "INC-2423 — bad deploy rolled back after error-rate spike (2026-06-27): the 14:05 deploy of the orders API shipped a serialization change that dropped a required field from the event schema. Consumers began rejecting messages and the orders API error rate climbed from 0.2% to 11% within three minutes",
            source: "knowledge/incidents/INC-2423.md",
            confidence: 0.415,
          },
          {
            kind: "past_incident",
            summary:
              "INC-2401 — checkout DB connection pool exhaustion (2026-06-18): the checkout service began returning 503s at 09:14 as its database connection pool saturated at 100% utilization. A background reconciler deployed that morning opened a connection per order row and never released it on the error path, s",
            source: "knowledge/incidents/INC-2401.md",
            confidence: 0.354,
          },
        ],
        repair_options: [
          "check connection pools",
          "review recent deploys",
          "scale horizontally",
        ],
      },
    },
    { event: "done", data: { status: "done" } },
  ],
  "demo-5xx": [
    {
      event: "step",
      data: {
        name: "classify",
        detail: "Classifying the alert against the deterministic floor.",
        ts: "2026-07-18T15:25:09.614265+00:00",
      },
    },
    {
      event: "step",
      data: {
        name: "retrieve",
        detail: "Retrieving runbooks and past incidents.",
        ts: "2026-07-18T15:25:09.676314+00:00",
      },
    },
    {
      event: "step",
      data: {
        name: "synthesize",
        detail: "Synthesizing the incident story (deterministic).",
        ts: "2026-07-18T15:25:09.731338+00:00",
      },
    },
    {
      event: "evidence",
      data: {
        kind: "metric",
        summary: "classified as availability at P2",
        source: "predictor:/predict",
        confidence: 0.75,
      },
    },
    {
      event: "evidence",
      data: {
        kind: "runbook",
        summary:
          "Runbook - Canary rollback procedure: Error rate or latency regression isolated to the canary cohort after a progressive rollout.",
        source: "knowledge/runbooks/canary-rollback.md",
        confidence: 0.527,
      },
    },
    {
      event: "evidence",
      data: {
        kind: "runbook",
        summary:
          "Runbook - Feature flag related incident response: Error spike correlates exactly with a flag flip; blast radius matches the flag cohort.",
        source: "knowledge/runbooks/feature-flag-incident.md",
        confidence: 0.491,
      },
    },
    {
      event: "evidence",
      data: {
        kind: "past_incident",
        summary:
          "INC-2401 — checkout DB connection pool exhaustion (2026-06-18): the checkout service began returning 503s at 09:14 as its database connection pool saturated at 100% utilization. A background reconciler deployed that morning opened a connection per order row and never released it on the error path, s",
        source: "knowledge/incidents/INC-2401.md",
        confidence: 0.436,
      },
    },
    {
      event: "story",
      data: {
        alert: {
          id: "demo-5xx",
          source: "grafana",
          title: "checkout returning 5xx",
          description: "error rate spike correlates with the canary rollout",
          severity: "P2",
          received_at: "2026-01-01T00:00:00Z",
          labels: {},
        },
        what_changed: "Signal 'checkout returning 5xx' from grafana",
        probable_cause: "availability",
        confidence: 0.75,
        evidence: [
          {
            kind: "metric",
            summary: "classified as availability at P2",
            source: "predictor:/predict",
            confidence: 0.75,
          },
          {
            kind: "runbook",
            summary:
              "Runbook - Canary rollback procedure: Error rate or latency regression isolated to the canary cohort after a progressive rollout.",
            source: "knowledge/runbooks/canary-rollback.md",
            confidence: 0.527,
          },
          {
            kind: "runbook",
            summary:
              "Runbook - Feature flag related incident response: Error spike correlates exactly with a flag flip; blast radius matches the flag cohort.",
            source: "knowledge/runbooks/feature-flag-incident.md",
            confidence: 0.491,
          },
          {
            kind: "past_incident",
            summary:
              "INC-2401 — checkout DB connection pool exhaustion (2026-06-18): the checkout service began returning 503s at 09:14 as its database connection pool saturated at 100% utilization. A background reconciler deployed that morning opened a connection per order row and never released it on the error path, s",
            source: "knowledge/incidents/INC-2401.md",
            confidence: 0.436,
          },
        ],
        repair_options: [
          "roll back last deploy",
          "shift traffic off bad canary",
        ],
      },
    },
    { event: "done", data: { status: "done" } },
  ],
};
