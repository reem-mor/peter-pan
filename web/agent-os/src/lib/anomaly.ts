/**
 * Client-side spend anomaly detection — plain z-score over the cost series.
 *
 * Deliberately deterministic and dumb: an LLM never decides what counts as
 * an anomaly (deterministic-floors invariant). A bucket is anomalous when
 * its cost sits more than Z_THRESHOLD standard deviations above the series
 * mean and the series has enough signal to make a deviation meaningful.
 */

import type { SeriesPoint } from "./os";

export interface Anomaly {
  index: number;
  point: SeriesPoint;
  zScore: number;
}

const Z_THRESHOLD = 2.5;
const MIN_BUCKETS = 8;

export function detectAnomalies(points: SeriesPoint[]): Anomaly[] {
  if (points.length < MIN_BUCKETS) return [];
  const costs = points.map((p) => p.cost_usd);
  const mean = costs.reduce((s, c) => s + c, 0) / costs.length;
  const variance =
    costs.reduce((s, c) => s + (c - mean) ** 2, 0) / costs.length;
  const std = Math.sqrt(variance);
  if (std === 0) return []; // flat series — nothing can deviate
  return points
    .map((point, index) => ({
      index,
      point,
      zScore: (point.cost_usd - mean) / std,
    }))
    .filter((a) => a.zScore >= Z_THRESHOLD && a.point.cost_usd > 0)
    .sort((a, b) => b.zScore - a.zScore);
}
