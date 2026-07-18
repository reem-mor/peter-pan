/** Hand-rolled SVG donut — cost share per model (see AreaChart for the
 * no-chart-library rationale). */

import type { UsageAggregate } from "../../lib/os";
import { fmtUsd } from "../../lib/format";

export const PALETTE = [
  "var(--color-accent)",
  "var(--color-cyan)",
  "var(--color-violet)",
  "var(--color-amber)",
  "var(--color-red)",
  "var(--color-blue)",
] as const;

const C = 100;
const R = 74;
const SW = 26;

export function Donut({ byModel }: { byModel: UsageAggregate }) {
  const entries = Object.entries(byModel).sort(
    (a, b) => b[1].cost_usd - a[1].cost_usd,
  );
  const total = entries.reduce((s, [, r]) => s + r.cost_usd, 0);
  if (total === 0) {
    return (
      <p className="font-mono text-[13px] text-ink-faint">
        no model spend in window
      </p>
    );
  }

  const circumference = 2 * Math.PI * R;
  let offset = 0;
  const segments = entries.map(([name, row], i) => {
    const frac = row.cost_usd / total;
    const seg = (
      <circle
        key={name}
        cx={C}
        cy={C}
        r={R}
        fill="none"
        stroke={PALETTE[i % PALETTE.length]}
        strokeWidth={SW}
        strokeDasharray={`${(frac * circumference).toFixed(2)} ${circumference.toFixed(2)}`}
        strokeDashoffset={(-offset * circumference).toFixed(2)}
        transform={`rotate(-90 ${C} ${C})`}
      />
    );
    offset += frac;
    return seg;
  });

  return (
    <div>
      <svg
        viewBox="0 0 200 200"
        width="200"
        className="mx-auto block"
        role="img"
        aria-label={`Cost share by model: ${entries
          .map(
            ([name, row]) =>
              `${name} ${((row.cost_usd / total) * 100).toFixed(1)}%`,
          )
          .join(", ")}. Total ${fmtUsd(total)}.`}
      >
        {segments}
        <text
          x="100"
          y="94"
          textAnchor="middle"
          fontSize="20"
          fontWeight="700"
          fill="var(--color-ink)"
          fontFamily="var(--font-mono)"
        >
          {fmtUsd(total)}
        </text>
        <text
          x="100"
          y="114"
          textAnchor="middle"
          fontSize="10"
          fill="var(--color-ink-soft)"
          fontFamily="var(--font-mono)"
        >
          TOTAL SPEND
        </text>
      </svg>
      <ul className="mt-2.5 flex flex-wrap gap-x-4 gap-y-1.5" aria-hidden="true">
        {entries.map(([name, row], i) => (
          <li
            key={name}
            className="inline-flex items-center gap-2 font-mono text-xs text-ink-soft"
          >
            <span
              className="h-2.5 w-2.5 rounded-[3px]"
              style={{ background: PALETTE[i % PALETTE.length] }}
            />
            {name} · {((row.cost_usd / total) * 100).toFixed(1)}%
          </li>
        ))}
      </ul>
    </div>
  );
}
