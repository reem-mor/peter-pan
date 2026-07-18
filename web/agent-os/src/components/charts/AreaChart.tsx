/**
 * Hand-rolled SVG area/line chart for the spend series.
 *
 * Hand-rolled over a chart library on purpose: zero new dependencies
 * (fixture-first, offline build), full control of the design tokens, and
 * it matches the proven approach of the design-v2 dashboard
 * (ui/os_dashboard.html). ~120 lines buys everything Recharts would.
 */

import { useRef, useState } from "react";
import type { SeriesPoint } from "../../lib/os";
import { fmtInt, fmtTime, fmtTok, fmtUsd } from "../../lib/format";

const W = 760;
const H = 240;
const PAD_L = 48;
const PAD_R = 14;
const PAD_T = 14;
const PAD_B = 30;
const IW = W - PAD_L - PAD_R;
const IH = H - PAD_T - PAD_B;

export function AreaChart({
  points,
  anomalyIndices,
}: {
  points: SeriesPoint[];
  anomalyIndices: number[];
}) {
  const hostRef = useRef<HTMLDivElement>(null);
  const [hover, setHover] = useState<{
    index: number;
    px: number;
    py: number;
  } | null>(null);

  if (points.length === 0) {
    return (
      <p className="font-mono text-[13px] text-ink-faint">no data in window</p>
    );
  }

  const maxCost = Math.max(...points.map((p) => p.cost_usd), 1e-9);
  const maxCalls = Math.max(...points.map((p) => p.calls), 1);
  const denom = Math.max(points.length - 1, 1);
  const x = (i: number) => PAD_L + (i / denom) * IW;
  const yCost = (v: number) => PAD_T + IH - (v / maxCost) * IH;
  const yCalls = (v: number) => PAD_T + IH - (v / maxCalls) * IH;

  let area = `M ${x(0)} ${PAD_T + IH}`;
  let line = "";
  let callLine = "";
  points.forEach((p, i) => {
    area += ` L ${x(i)} ${yCost(p.cost_usd)}`;
    line += `${i ? " L" : "M"} ${x(i)} ${yCost(p.cost_usd)}`;
    callLine += `${i ? " L" : "M"} ${x(i)} ${yCalls(p.calls)}`;
  });
  area += ` L ${x(points.length - 1)} ${PAD_T + IH} Z`;

  const anomalySet = new Set(anomalyIndices);

  const onMove = (ev: React.MouseEvent<SVGSVGElement>) => {
    const box = ev.currentTarget.getBoundingClientRect();
    const px = (ev.clientX - box.left) * (W / box.width);
    const i = Math.max(
      0,
      Math.min(points.length - 1, Math.round(((px - PAD_L) / IW) * denom)),
    );
    const hostBox = hostRef.current?.getBoundingClientRect();
    setHover({
      index: i,
      px: hostBox ? ev.clientX - hostBox.left : 0,
      py: hostBox ? ev.clientY - hostBox.top : 0,
    });
  };

  const hovered = hover ? points[hover.index] : null;
  const total = points.reduce((s, p) => s + p.cost_usd, 0);

  return (
    <div ref={hostRef} className="relative w-full overflow-x-auto">
      <svg
        viewBox={`0 0 ${W} ${H}`}
        className="min-w-[520px]"
        width="100%"
        role="img"
        aria-label={`Spend over time: ${points.length} buckets, ${fmtUsd(
          total,
        )} total, peak bucket ${fmtUsd(maxCost)}${
          anomalySet.size
            ? `, ${anomalySet.size} anomalous bucket${anomalySet.size > 1 ? "s" : ""} flagged`
            : ""
        }.`}
        onMouseMove={onMove}
        onMouseLeave={() => setHover(null)}
      >
        <defs>
          <linearGradient id="costFill" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor="var(--color-accent)" stopOpacity="0.35" />
            <stop offset="100%" stopColor="var(--color-accent)" stopOpacity="0.02" />
          </linearGradient>
        </defs>
        {[0.25, 0.5, 0.75, 1].map((f) => {
          const y = PAD_T + IH - f * IH;
          return (
            <g key={f}>
              <line
                x1={PAD_L}
                y1={y}
                x2={W - PAD_R}
                y2={y}
                stroke="var(--color-edge)"
                strokeDasharray="3 5"
              />
              <text
                x={PAD_L - 8}
                y={y + 4}
                textAnchor="end"
                fontSize="10"
                fill="var(--color-ink-faint)"
                fontFamily="var(--font-mono)"
              >
                ${(maxCost * f).toFixed(3)}
              </text>
            </g>
          );
        })}
        <path d={area} fill="url(#costFill)" />
        <path
          d={line}
          fill="none"
          stroke="var(--color-accent)"
          strokeWidth="2"
          strokeLinejoin="round"
        />
        <path
          d={callLine}
          fill="none"
          stroke="var(--color-violet)"
          strokeWidth="1.4"
          strokeDasharray="4 4"
          strokeLinejoin="round"
          opacity="0.85"
        />
        {points.map((p, i) =>
          anomalySet.has(i) ? (
            <circle
              key={p.t}
              cx={x(i)}
              cy={yCost(p.cost_usd)}
              r="4.5"
              fill="var(--color-red)"
              stroke="var(--color-bg)"
              strokeWidth="1.5"
            />
          ) : null,
        )}
        {hover ? (
          <line
            x1={x(hover.index)}
            y1={PAD_T}
            x2={x(hover.index)}
            y2={PAD_T + IH}
            stroke="var(--color-edge-hi)"
            strokeWidth="1"
          />
        ) : null}
        {[0, Math.floor(points.length / 2), points.length - 1].map((i) => (
          <text
            key={i}
            x={x(i)}
            y={H - 8}
            textAnchor="middle"
            fontSize="10"
            fill="var(--color-ink-faint)"
            fontFamily="var(--font-mono)"
          >
            {fmtTime(points[i].t)}
          </text>
        ))}
      </svg>
      {hovered && hover ? (
        <div
          className="pointer-events-none absolute z-10 rounded-lg border border-edge-hi bg-panel-2 px-3 py-2 font-mono text-xs whitespace-nowrap"
          style={{
            left: Math.min(
              hover.px + 14,
              (hostRef.current?.clientWidth ?? W) - 190,
            ),
            top: hover.py - 10,
          }}
        >
          <div className="text-[10.5px] text-ink-soft">
            {fmtTime(hovered.t)}
            {anomalySet.has(hover.index) ? (
              <span className="ml-2 font-bold text-red">anomaly</span>
            ) : null}
          </div>
          <div>
            <span className="text-ink-soft">cost</span> {fmtUsd(hovered.cost_usd)}{" "}
            · <span className="text-ink-soft">calls</span> {fmtInt(hovered.calls)}
          </div>
          <div>
            <span className="text-ink-soft">tok</span> {fmtTok(hovered.input_tokens)}{" "}
            in / {fmtTok(hovered.output_tokens)} out
          </div>
        </div>
      ) : null}
    </div>
  );
}
