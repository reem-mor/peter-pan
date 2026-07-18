import type { StepEvent, StreamState } from "../lib/stream";
import { EmptyState, Panel } from "./ui";

function StepRow({ step, index }: { step: StepEvent; index: number }) {
  const time = step.ts.slice(11, 19); // HH:MM:SS from the ISO timestamp
  return (
    <li className="stream-in flex gap-3 border-b border-edge py-2.5 last:border-b-0">
      <span className="font-mono text-[11px] text-faint tabular-nums" aria-hidden="true">
        {String(index + 1).padStart(2, "0")}
      </span>
      <div className="min-w-0 flex-1">
        <div className="flex items-baseline justify-between gap-2">
          <span className="font-mono text-xs font-semibold tracking-wider text-ink uppercase">
            {step.name}
          </span>
          <time className="font-mono text-[11px] text-faint tabular-nums" dateTime={step.ts}>
            {time}
          </time>
        </div>
        <p className="mt-0.5 text-sm text-muted">{step.detail}</p>
      </div>
    </li>
  );
}

export function ReasoningPanel({ state }: { state: StreamState }) {
  return (
    <Panel title="Agent reasoning" hint="Planner steps as they stream in">
      {/* aria-live so streamed steps are announced without stealing focus */}
      <div aria-live="polite">
        {state.steps.length === 0 ? (
          <EmptyState>
            {state.phase === "connecting"
              ? "connecting to agent stream…"
              : "no run yet — pick an alert above"}
          </EmptyState>
        ) : (
          <ol className="list-none">
            {state.steps.map((step, i) => (
              <StepRow key={`${step.name}-${i}`} step={step} index={i} />
            ))}
          </ol>
        )}
        {state.phase === "streaming" && state.steps.length > 0 ? (
          <p className="mt-3 font-mono text-[11px] text-faint">
            <span aria-hidden="true" className="status-dot-live mr-1.5 inline-block size-[7px] rounded-full bg-accent align-middle" />
            streaming…
          </p>
        ) : null}
        {state.phase === "done" ? (
          <p className="mt-3 font-mono text-[11px] text-faint">run complete</p>
        ) : null}
      </div>
    </Panel>
  );
}
