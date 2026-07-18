/** Small shared pieces of the demo UI — all styled per the design system
 * (.claude/skills/peter-pan-design): tokens only, mono for data, status =
 * color + a second cue, confidence always < 100%. */
import type { ReactNode } from "react";
import type { Severity } from "@peterpan/types";

export function SectionLabel({ children }: { children: ReactNode }) {
  return (
    <span className="font-mono text-[11px] font-semibold tracking-[0.18em] text-muted uppercase">
      {children}
    </span>
  );
}

export function Panel({
  title,
  hint,
  children,
}: {
  title: string;
  hint: string;
  children: ReactNode;
}) {
  return (
    <section className="flex min-h-0 flex-col rounded-xl border border-edge bg-panel transition-colors duration-200 hover:border-edge-hi">
      <header className="border-b border-edge px-4 py-3">
        <h2>
          <SectionLabel>{title}</SectionLabel>
        </h2>
        <p className="mt-0.5 text-xs text-faint">{hint}</p>
      </header>
      <div className="min-h-0 flex-1 overflow-y-auto p-4">{children}</div>
    </section>
  );
}

/** Quiet mono line for regions with nothing to show yet. */
export function EmptyState({ children }: { children: ReactNode }) {
  return <p className="font-mono text-xs text-faint">{children}</p>;
}

export function SeverityBadge({ severity }: { severity: Severity }) {
  // Severity by weight before color; P1 additionally carries danger.
  const color = severity === "P1" ? "text-danger" : "text-ink";
  return (
    <span
      className={`inline-flex items-center gap-1.5 rounded-full border border-edge px-2 py-0.5 font-mono text-[11px] font-bold uppercase ${color}`}
    >
      {severity === "P1" ? (
        <span aria-hidden="true" className="size-[7px] rounded-full bg-danger" />
      ) : null}
      {severity}
    </span>
  );
}

/** Bounded confidence indicator — never renders as certainty. */
export function ConfidenceMeter({
  value,
  tone = "s2",
  label,
}: {
  value: number;
  tone?: "accent" | "s2";
  label: string;
}) {
  const pct = Math.min(Math.round(value * 100), 99); // invariant: < 1.0
  const bar = tone === "accent" ? "bg-accent" : "bg-s2";
  return (
    <div
      role="meter"
      aria-label={label}
      aria-valuemin={0}
      aria-valuemax={1}
      aria-valuenow={value}
      aria-valuetext={`${pct}%`}
      className="flex items-center gap-2"
    >
      <div className="h-1 flex-1 overflow-hidden rounded-full bg-well">
        <div className={`h-full rounded-full ${bar}`} style={{ width: `${pct}%` }} />
      </div>
      <span className="font-mono text-[11px] text-muted tabular-nums">{pct}%</span>
    </div>
  );
}
