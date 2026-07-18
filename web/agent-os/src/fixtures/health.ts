/**
 * Fixtures for the global health strip: mesh sweep fallback plus the last
 * eval-suite scores. Eval scores are a fixture by design for now — the
 * eval harness writes local artifacts, not an HTTP feed.
 */

import type { ServiceHealth } from "../lib/os";

export const FIXTURE_SERVICES: ServiceHealth[] = [
  { name: "predictor", status: "up", latency_ms: 6.2 },
  { name: "rag", status: "up", latency_ms: 9.8 },
  { name: "guardrails", status: "up", latency_ms: 4.1 },
  { name: "agent", status: "up", latency_ms: 12.4 },
];

export interface EvalScore {
  suite: string;
  score: number;
  threshold: number;
}

/** Last eval run (fixture) — mirrors the evals/ suites. */
export const FIXTURE_EVAL_SCORES: EvalScore[] = [
  { suite: "story faithfulness", score: 0.92, threshold: 0.85 },
  { suite: "retrieval hit-rate", score: 0.88, threshold: 0.8 },
  { suite: "guardrail catch-rate", score: 0.97, threshold: 0.95 },
];
