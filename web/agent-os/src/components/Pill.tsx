import type { Severity } from "@peterpan/types";
import type { BudgetState } from "../lib/os";
import type { IncidentStatus } from "../fixtures/incidents";

const PILL_BASE =
  "inline-flex items-center gap-1.5 rounded-full border px-2.5 py-0.5 font-mono text-[11px] tracking-[0.1em] uppercase whitespace-nowrap";

/* Severity is communicated by weight and label before color
   (colorblind-safe): P1/P2 are bold, and the label always carries the
   level. */
const SEVERITY_STYLE: Record<Severity, string> = {
  P1: "border-red/50 bg-red/10 text-red font-bold",
  P2: "border-amber/50 bg-amber/10 text-amber font-bold",
  P3: "border-blue/45 bg-blue/10 text-blue",
  P4: "border-edge-hi bg-panel-2 text-ink-soft",
};

export function SeverityPill({ severity }: { severity: Severity }) {
  return (
    <span className={`${PILL_BASE} ${SEVERITY_STYLE[severity]}`}>
      {severity}
    </span>
  );
}

const STATUS_STYLE: Record<IncidentStatus, string> = {
  investigating: "border-amber/50 bg-amber/10 text-amber",
  mitigated: "border-cyan/50 bg-cyan/10 text-cyan",
  resolved: "border-accent/40 bg-accent-dim text-accent",
};

export function StatusPill({ status }: { status: IncidentStatus }) {
  return <span className={`${PILL_BASE} ${STATUS_STYLE[status]}`}>{status}</span>;
}

const BUDGET_STYLE: Record<BudgetState, string> = {
  ok: "border-accent/40 bg-accent-dim text-accent",
  warn: "border-amber/50 bg-amber/10 text-amber",
  exceeded: "border-red/50 bg-red/10 text-red",
};

export function BudgetPill({ state }: { state: BudgetState }) {
  return <span className={`${PILL_BASE} ${BUDGET_STYLE[state]}`}>{state}</span>;
}

/** Live-vs-fixture provenance badge. aria-live so screen readers hear a
 * backend dropout without hunting for the badge. */
export function SourceBadge({ live }: { live: boolean }) {
  return (
    <span
      role="status"
      aria-live="polite"
      className={`${PILL_BASE} ${
        live
          ? "border-accent/45 text-accent"
          : "border-amber/45 text-amber"
      }`}
    >
      <span
        aria-hidden="true"
        className={`h-[7px] w-[7px] rounded-full ${
          live
            ? "bg-accent shadow-[0_0_8px_var(--color-accent)]"
            : "bg-amber shadow-[0_0_8px_var(--color-amber)]"
        }`}
      />
      {live ? "live data" : "synthetic fixture — backend offline"}
    </span>
  );
}
