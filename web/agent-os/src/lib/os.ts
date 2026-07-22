/**
 * Response shapes of the PETER PAN OS endpoints (src/peterpan/services/ppos.py).
 *
 * UsageAggregate/UsageRow live in @peterpan/types (schemas.py). Other OS
 * console shapes (series, budget, tips) remain local until promoted.
 */

import type { UsageAggregate, UsageRow } from "@peterpan/types";

import { getJSON } from "./api";

export type { UsageAggregate, UsageRow };

/** One bucket of `timeseries()` — /os/usage/series. `t` is the bucket start. */
export interface SeriesPoint {
  /** ISO-8601 datetime. */
  t: string;
  calls: number;
  input_tokens: number;
  output_tokens: number;
  cost_usd: number;
}

export interface UsageSeries {
  start: string;
  end: string;
  hours: number;
  buckets: number;
  points: SeriesPoint[];
}

export type BudgetState = "ok" | "warn" | "exceeded";

/** /os/budget — deterministic, report-only guard. */
export interface BudgetStatus {
  status: BudgetState;
  spent_usd: number;
  budget_usd: number;
  window_hours: number;
}

/** One probe of the /os/services mesh sweep. */
export interface ServiceHealth {
  name: string;
  url?: string;
  status: "up" | "down";
  latency_ms: number | null;
}

export function fetchUsage(
  by: "agent" | "model" | "service",
  hours: number,
  signal?: AbortSignal,
): Promise<UsageAggregate> {
  return getJSON<UsageAggregate>(`/os/usage?hours=${hours}&by=${by}`, signal);
}

export function fetchSeries(
  hours: number,
  buckets: number,
  signal?: AbortSignal,
): Promise<UsageSeries> {
  return getJSON<UsageSeries>(
    `/os/usage/series?hours=${hours}&buckets=${buckets}`,
    signal,
  );
}

export function fetchBudget(signal?: AbortSignal): Promise<BudgetStatus> {
  return getJSON<BudgetStatus>("/os/budget", signal);
}

export function fetchTips(signal?: AbortSignal): Promise<{ tips: string[] }> {
  return getJSON<{ tips: string[] }>("/os/tips", signal);
}

export function fetchServices(
  signal?: AbortSignal,
): Promise<{ services: ServiceHealth[] }> {
  return getJSON<{ services: ServiceHealth[] }>("/os/services", signal);
}
