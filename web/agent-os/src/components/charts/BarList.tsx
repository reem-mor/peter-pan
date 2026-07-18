/** Cost-share breakdown table with inline bars — agents / models / services. */

import type { UsageAggregate } from "../../lib/os";
import { fmtInt, fmtTok, fmtUsd } from "../../lib/format";
import { PALETTE } from "./Donut";

export function BarList({
  aggregate,
  label,
}: {
  aggregate: UsageAggregate;
  label: string;
}) {
  const entries = Object.entries(aggregate).sort(
    (a, b) => b[1].cost_usd - a[1].cost_usd,
  );
  if (entries.length === 0) {
    return (
      <p className="font-mono text-[13px] text-ink-faint">
        no usage in window
      </p>
    );
  }
  const maxCost = Math.max(...entries.map(([, r]) => r.cost_usd), 1e-9);

  return (
    <div className="overflow-x-auto">
      <table className="w-full border-collapse font-mono text-[13px]">
        <caption className="sr-only">{label}</caption>
        <thead>
          <tr>
            {["Name", "Calls", "Tok in", "Tok out", "Cost", "Share"].map(
              (h, i) => (
                <th
                  key={h}
                  scope="col"
                  className={`border-b border-edge px-2.5 py-2 text-[10.5px] font-semibold tracking-[0.12em] text-ink-faint uppercase ${
                    i === 0 || i === 5 ? "text-left" : "text-right"
                  }`}
                >
                  {h}
                </th>
              ),
            )}
          </tr>
        </thead>
        <tbody>
          {entries.map(([name, r], i) => (
            <tr key={name} className="hover:bg-panel-2">
              <td className="border-b border-bg-grid px-2.5 py-2">
                <span className="flex items-center gap-2">
                  <span
                    aria-hidden="true"
                    className="h-2 w-2 shrink-0 rounded-[2px]"
                    style={{ background: PALETTE[i % PALETTE.length] }}
                  />
                  {name}
                </span>
              </td>
              <td className="border-b border-bg-grid px-2.5 py-2 text-right tabular-nums">
                {fmtInt(r.calls)}
              </td>
              <td className="border-b border-bg-grid px-2.5 py-2 text-right tabular-nums">
                {fmtTok(r.input_tokens)}
              </td>
              <td className="border-b border-bg-grid px-2.5 py-2 text-right tabular-nums">
                {fmtTok(r.output_tokens)}
              </td>
              <td className="border-b border-bg-grid px-2.5 py-2 text-right tabular-nums">
                {fmtUsd(r.cost_usd)}
              </td>
              <td className="w-[22%] border-b border-bg-grid px-2.5 py-2">
                <div
                  aria-hidden="true"
                  className="h-1 min-w-[2px] rounded-sm bg-accent opacity-70"
                  style={{ width: `${((r.cost_usd / maxCost) * 100).toFixed(1)}%` }}
                />
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
