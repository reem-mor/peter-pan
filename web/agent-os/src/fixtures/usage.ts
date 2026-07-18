/**
 * Synthetic token-usage fixture — renders the full Token Usage page with
 * zero backends (fixture-first / mirage-mode invariant). Shapes mirror the
 * OS endpoints exactly; numbers are invented and deterministic so demos
 * and screenshots are reproducible.
 */

import type {
  BudgetStatus,
  SeriesPoint,
  UsageAggregate,
  UsageSeries,
} from "../lib/os";

export const FIXTURE_BY_AGENT: UsageAggregate = {
  "incident-agent": {
    calls: 42,
    input_tokens: 51240,
    output_tokens: 38920,
    cost_usd: 0.7462,
  },
  "llm-judge": {
    calls: 38,
    input_tokens: 36110,
    output_tokens: 9860,
    cost_usd: 0.2564,
  },
  rag: { calls: 61, input_tokens: 18300, output_tokens: 6100, cost_usd: 0.0915 },
  predictor: {
    calls: 57,
    input_tokens: 8550,
    output_tokens: 1140,
    cost_usd: 0.0299,
  },
};

export const FIXTURE_BY_MODEL: UsageAggregate = {
  "claude-sonnet-5": {
    calls: 80,
    input_tokens: 87350,
    output_tokens: 48780,
    cost_usd: 1.0026,
  },
  "claude-haiku-4-5-20251001": {
    calls: 118,
    input_tokens: 26850,
    output_tokens: 7240,
    cost_usd: 0.1214,
  },
};

export const FIXTURE_BY_SERVICE: UsageAggregate = {
  agent: {
    calls: 42,
    input_tokens: 51240,
    output_tokens: 38920,
    cost_usd: 0.7462,
  },
  evals: {
    calls: 38,
    input_tokens: 36110,
    output_tokens: 9860,
    cost_usd: 0.2564,
  },
  rag: { calls: 61, input_tokens: 18300, output_tokens: 6100, cost_usd: 0.0915 },
  predictor: {
    calls: 57,
    input_tokens: 8550,
    output_tokens: 1140,
    cost_usd: 0.0299,
  },
};

/**
 * Deterministic wave series with two deliberate spikes so the anomaly
 * detector has something honest to flag in fixture mode.
 */
export function fixtureSeries(hours: number, buckets = 48): UsageSeries {
  const now = Date.now();
  const stepMs = (hours * 3600 * 1000) / buckets;
  const points: SeriesPoint[] = [];
  for (let i = 0; i < buckets; i++) {
    const wave = Math.sin(i / 5.1) * 0.5 + 0.5;
    const spike = i % 17 === 0 && i > 0 ? 3.4 : 1;
    points.push({
      t: new Date(now - (buckets - i) * stepMs).toISOString(),
      calls: Math.round((2 + wave * 6) * spike),
      input_tokens: Math.round((900 + wave * 2400) * spike),
      output_tokens: Math.round((300 + wave * 900) * spike),
      cost_usd: +((0.004 + wave * 0.02) * spike).toFixed(6),
    });
  }
  return {
    start: points[0].t,
    end: new Date(now).toISOString(),
    hours,
    buckets,
    points,
  };
}

export const FIXTURE_BUDGET: BudgetStatus = {
  status: "ok",
  spent_usd: 1.124,
  budget_usd: 5.0,
  window_hours: 24,
};

export const FIXTURE_TIPS: string[] = [
  "incident-agent: avg input 1,220 tokens/call — healthy; retrieval caps are holding.",
  "llm-judge: routine verdicts could route to the haiku tier and save ~60% of eval spend.",
];
