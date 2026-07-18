/**
 * Token Usage — the console centerpiece. Live-ish (10s poll) view of what
 * the agent mesh is spending: series, budget guard, per-model/agent/service
 * breakdowns, top consumers, and deterministic z-score anomaly callouts.
 *
 * All-or-nothing data cycle: either every panel is live or every panel is
 * fixture (mixing would be indistinguishable from real data — see
 * useLiveData).
 */

import { useMemo, useState } from "react";
import { useLiveData } from "../hooks/useLiveData";
import {
  fetchBudget,
  fetchSeries,
  fetchTips,
  fetchUsage,
  type BudgetStatus,
  type UsageAggregate,
  type UsageSeries,
} from "../lib/os";
import { detectAnomalies } from "../lib/anomaly";
import { fmtInt, fmtTime, fmtTok, fmtUsd } from "../lib/format";
import {
  FIXTURE_BUDGET,
  FIXTURE_BY_AGENT,
  FIXTURE_BY_MODEL,
  FIXTURE_BY_SERVICE,
  FIXTURE_TIPS,
  fixtureSeries,
} from "../fixtures/usage";
import { Panel } from "../components/Panel";
import { PageHeader } from "../components/PageHeader";
import { BudgetPill, SourceBadge } from "../components/Pill";
import { AreaChart } from "../components/charts/AreaChart";
import { Donut } from "../components/charts/Donut";
import { BarList } from "../components/charts/BarList";

const POLL_MS = 10_000;
const BUCKETS = 48;
const WINDOWS = [
  { hours: 1, label: "1H" },
  { hours: 6, label: "6H" },
  { hours: 24, label: "24H" },
  { hours: 168, label: "7D" },
] as const;

interface TokenUsageData {
  byAgent: UsageAggregate;
  byModel: UsageAggregate;
  byService: UsageAggregate;
  series: UsageSeries;
  budget: BudgetStatus;
  tips: string[];
}

function makeLoader(hours: number) {
  return async (signal: AbortSignal): Promise<TokenUsageData> => {
    const [byAgent, byModel, byService, series, budget, tips] =
      await Promise.all([
        fetchUsage("agent", hours, signal),
        fetchUsage("model", hours, signal),
        fetchUsage("service", hours, signal),
        fetchSeries(hours, BUCKETS, signal),
        fetchBudget(signal),
        fetchTips(signal),
      ]);
    return { byAgent, byModel, byService, series, budget, tips: tips.tips };
  };
}

function makeFixture(hours: number): TokenUsageData {
  return {
    byAgent: FIXTURE_BY_AGENT,
    byModel: FIXTURE_BY_MODEL,
    byService: FIXTURE_BY_SERVICE,
    series: fixtureSeries(hours, BUCKETS),
    budget: FIXTURE_BUDGET,
    tips: FIXTURE_TIPS,
  };
}

function totals(agg: UsageAggregate) {
  let calls = 0;
  let tin = 0;
  let tout = 0;
  let cost = 0;
  for (const row of Object.values(agg)) {
    calls += row.calls;
    tin += row.input_tokens;
    tout += row.output_tokens;
    cost += row.cost_usd;
  }
  return { calls, tin, tout, cost };
}

function Kpi({
  label,
  value,
  hint,
  accent = false,
}: {
  label: string;
  value: string;
  hint: string;
  accent?: boolean;
}) {
  return (
    <div className="rounded-xl border border-edge bg-panel p-[18px] transition-colors hover:border-edge-hi">
      <div className="font-mono text-[10.5px] tracking-[0.16em] text-ink-soft uppercase">
        {label}
      </div>
    <div
        className={`mt-1.5 font-mono text-3xl leading-tight font-bold ${
          accent
            ? "text-accent [text-shadow:0_0_18px_rgba(47,230,176,0.35)]"
            : "text-ink"
        }`}
      >
        {value}
      </div>
      <div className="mt-1 font-mono text-[12.5px] text-ink-faint">{hint}</div>
    </div>
  );
}

export function TokenUsage() {
  const [hours, setHours] = useState<number>(24);
  const loader = useMemo(() => makeLoader(hours), [hours]);
  const fixture = useMemo(() => makeFixture(hours), [hours]);
  const { data, live, refreshedAt } = useLiveData(loader, fixture, POLL_MS);

  const t = totals(data.byAgent);
  const anomalies = useMemo(
    () => detectAnomalies(data.series.points),
    [data.series],
  );

  // Top consumers across every dimension — where is the money actually going.
  const topConsumers = useMemo(() => {
    const rows: { name: string; dim: string; cost: number }[] = [];
    const push = (agg: UsageAggregate, dim: string) => {
      for (const [name, r] of Object.entries(agg))
        rows.push({ name, dim, cost: r.cost_usd });
    };
    push(data.byAgent, "agent");
    push(data.byModel, "model");
    push(data.byService, "service");
    return rows.sort((a, b) => b.cost - a.cost).slice(0, 6);
  }, [data]);
  const maxConsumerCost = Math.max(...topConsumers.map((r) => r.cost), 1e-9);

  const budgetPct = Math.min(
    100,
    (data.budget.spent_usd / data.budget.budget_usd) * 100,
  );

  return (
    <div className="p-6">
      <PageHeader
        title="Token Usage"
        subtitle="What the agent mesh is spending — metered by log_usage() on every LLM call."
      >
        <SourceBadge live={live} />
        <nav
          className="inline-flex overflow-hidden rounded-lg border border-edge-hi"
          aria-label="Time window"
        >
          {WINDOWS.map((w) => (
            <button
              key={w.hours}
              type="button"
              aria-pressed={hours === w.hours}
              onClick={() => setHours(w.hours)}
              className={`min-h-10 min-w-12 border-edge px-3 font-mono text-xs tracking-[0.08em] transition-colors not-first:border-l ${
                hours === w.hours
                  ? "bg-accent font-bold text-bg"
                  : "text-ink-soft hover:bg-panel-2 hover:text-ink"
              }`}
            >
              {w.label}
            </button>
          ))}
        </nav>
        {refreshedAt ? (
          <span className="font-mono text-[11px] text-ink-faint">
            refreshed {refreshedAt.toLocaleTimeString()} · polls every 10s
          </span>
        ) : null}
      </PageHeader>

      <section
        className="grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-5"
        aria-label="Key metrics"
      >
        <Kpi
          label="Spend · window"
          value={fmtUsd(t.cost)}
          hint={hours >= 24 ? `last ${hours / 24}d` : `last ${hours}h`}
          accent
        />
        <Kpi label="Input tokens" value={fmtTok(t.tin)} hint="prompt side" />
        <Kpi
          label="Output tokens"
          value={fmtTok(t.tout)}
          hint="completion side"
        />
        <Kpi
          label="LLM calls"
          value={fmtInt(t.calls)}
          hint={`${Object.keys(data.byAgent).length} agents active`}
        />
        <Kpi
          label="Avg tokens / call"
          value={t.calls ? fmtTok(Math.round((t.tin + t.tout) / t.calls)) : "0"}
          hint="in + out"
        />
      </section>

      <Panel
        title="Daily budget guard"
        hint="report-only · deterministic"
        className="mt-4"
      >
        <div className="flex flex-wrap items-center gap-3.5">
          <BudgetPill state={data.budget.status} />
          <div
            className="h-3 min-w-[220px] flex-1 overflow-hidden rounded-full border border-edge bg-bg-grid"
            role="progressbar"
            aria-label="Budget consumption"
            aria-valuemin={0}
            aria-valuemax={100}
            aria-valuenow={Math.round(budgetPct)}
          >
            <div
              className={`h-full rounded-full transition-[width] duration-500 ${
                data.budget.status === "ok"
                  ? "bg-gradient-to-r from-accent to-cyan"
                  : data.budget.status === "warn"
                    ? "bg-gradient-to-r from-amber to-amber/80"
                    : "bg-gradient-to-r from-red to-red/80"
              }`}
              style={{ width: `${budgetPct.toFixed(1)}%` }}
            />
          </div>
          <span className="font-mono text-[13px] whitespace-nowrap text-ink-soft">
            <strong className="text-ink">{fmtUsd(data.budget.spent_usd)}</strong>{" "}
            / {fmtUsd(data.budget.budget_usd)} · {budgetPct.toFixed(1)}% of
            daily budget ({data.budget.window_hours}h window)
          </span>
        </div>
      </Panel>

      <section className="mt-4 grid grid-cols-1 gap-4 xl:grid-cols-[2fr_1fr]">
        <Panel title="Spend over time" hint="cost + calls per bucket">
          <AreaChart
            points={data.series.points}
            anomalyIndices={anomalies.map((a) => a.index)}
          />
          <div className="mt-2.5 flex flex-wrap gap-4">
            <span className="inline-flex items-center gap-2 font-mono text-xs text-ink-soft">
              <span className="h-2.5 w-2.5 rounded-[3px] bg-accent" /> cost usd
              / bucket
            </span>
            <span className="inline-flex items-center gap-2 font-mono text-xs text-ink-soft">
              <span className="h-2.5 w-2.5 rounded-[3px] bg-violet" /> calls /
              bucket
            </span>
            <span className="inline-flex items-center gap-2 font-mono text-xs text-ink-soft">
              <span className="h-2.5 w-2.5 rounded-full bg-red" /> spend anomaly
              (z ≥ 2.5)
            </span>
          </div>
        </Panel>
        <Panel title="Cost share by model">
          <Donut byModel={data.byModel} />
        </Panel>
      </section>

      <section className="mt-4 grid grid-cols-1 gap-4 xl:grid-cols-2">
        <Panel
          title="Anomaly callouts"
          hint="client-side z-score · deterministic, no LLM"
        >
          {anomalies.length === 0 ? (
            <p className="font-mono text-[13px] text-ink-faint">
              no spend anomalies in window — buckets within 2.5σ of the mean
            </p>
          ) : (
            <ul className="flex flex-col gap-2.5">
              {anomalies.slice(0, 4).map((a) => (
                <li
                  key={a.point.t}
                  className="flex items-start gap-3 rounded-[10px] border border-red/40 bg-red/5 px-3 py-2.5 text-sm"
                >
                  <span
                    aria-hidden="true"
                    className="mt-1 h-2 w-2 shrink-0 rounded-full bg-red"
                  />
                  <span>
                    <span className="font-mono font-bold text-red">
                      {fmtTime(a.point.t)}
                    </span>{" "}
                    — bucket spend {fmtUsd(a.point.cost_usd)} at{" "}
                    <span className="font-mono">z = {a.zScore.toFixed(1)}</span>{" "}
                    ({fmtInt(a.point.calls)} calls,{" "}
                    {fmtTok(a.point.input_tokens + a.point.output_tokens)} tok).
                    Check the change timeline for a prompt or retrieval
                    regression in this window.
                  </span>
                </li>
              ))}
            </ul>
          )}
        </Panel>
        <Panel title="Top consumers" hint="across agents, models, services">
          <ul className="flex flex-col gap-2">
            {topConsumers.map((r) => (
              <li
                key={`${r.dim}:${r.name}`}
                className="flex items-center gap-3 font-mono text-[13px]"
              >
                <span className="w-16 shrink-0 rounded-md border border-edge px-1.5 py-0.5 text-center text-[10px] tracking-[0.08em] text-ink-faint uppercase">
                  {r.dim}
                </span>
                <span className="w-40 truncate sm:w-52" title={r.name}>
                  {r.name}
                </span>
                <div className="h-1.5 flex-1 rounded-full bg-bg-grid">
                  <div
                    aria-hidden="true"
                    className="h-full rounded-full bg-cyan opacity-80"
                    style={{
                      width: `${((r.cost / maxConsumerCost) * 100).toFixed(1)}%`,
                    }}
                  />
                </div>
                <span className="w-20 text-right tabular-nums">
                  {fmtUsd(r.cost)}
                </span>
              </li>
            ))}
          </ul>
        </Panel>
      </section>

      <section className="mt-4 grid grid-cols-1 gap-4 xl:grid-cols-2">
        <Panel title="Agents · token & cost breakdown">
          <BarList aggregate={data.byAgent} label="Per-agent usage" />
        </Panel>
        <Panel title="Services · token & cost breakdown">
          <BarList aggregate={data.byService} label="Per-service usage" />
        </Panel>
      </section>

      <section className="mt-4 grid grid-cols-1 gap-4 xl:grid-cols-2">
        <Panel title="Models · token & cost breakdown">
          <BarList aggregate={data.byModel} label="Per-model usage" />
        </Panel>
        <Panel title="Optimization tips" hint="deterministic heuristics from /os/tips">
          <ul className="flex flex-col gap-2.5">
            {data.tips.map((tip) => (
              <li
                key={tip}
                className="flex items-start gap-3 rounded-[10px] border border-edge bg-bg-grid px-3 py-2.5 text-sm"
              >
                <span
                  aria-hidden="true"
                  className="mt-1 h-2 w-2 shrink-0 rounded-full bg-amber"
                />
                {tip}
              </li>
            ))}
          </ul>
        </Panel>
      </section>
    </div>
  );
}
