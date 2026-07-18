import { useEffect } from "react";
import { DEMO_ALERTS } from "./lib/alerts";
import { useAgentStream } from "./lib/stream";
import { EvidencePanel } from "./components/EvidencePanel";
import { IncidentGraph } from "./components/IncidentGraph";
import { ReasoningPanel } from "./components/ReasoningPanel";
import { StoryPanel } from "./components/StoryPanel";

/** Live / replay indicator — status is always color + word, never hue alone. */
function ModeBadge({ mode, phase }: { mode: "live" | "replay"; phase: string }) {
  if (phase === "idle") return null;
  if (mode === "replay") {
    return (
      <span className="inline-flex items-center gap-1.5 rounded-full border border-edge px-3 py-1 font-mono text-[11px] font-semibold text-warn uppercase">
        <span aria-hidden="true" className="size-[7px] rounded-full bg-warn" />
        replay · fixture
      </span>
    );
  }
  return (
    <span className="inline-flex items-center gap-1.5 rounded-full border border-edge px-3 py-1 font-mono text-[11px] font-semibold text-accent uppercase">
      <span
        aria-hidden="true"
        className={`size-[7px] rounded-full bg-accent ${phase === "streaming" || phase === "connecting" ? "status-dot-live" : ""}`}
      />
      live stream
    </span>
  );
}

export default function App() {
  const { state, start } = useAgentStream();

  // Auto-run the first catalog alert so the page opens mid-story instead of
  // empty. StrictMode double-invokes this effect in dev; the hook's sequence
  // token discards the first run's frames, so no ref guard (a guard would
  // leave the stream closed after StrictMode's simulated unmount).
  useEffect(() => {
    start(DEMO_ALERTS[0].id);
  }, [start]);

  return (
    <div className="flex min-h-screen flex-col bg-surface font-sans text-ink">
      <header className="flex flex-wrap items-center justify-between gap-3 border-b border-edge px-6 py-3">
        <h1 className="font-mono text-[17px] font-bold tracking-[0.06em]">
          PETER PAN <span className="font-normal text-muted">/ live demo</span>
        </h1>
        <div className="flex items-center gap-2">
          <ModeBadge mode={state.mode} phase={state.phase} />
          <span className="rounded-full border border-edge px-3 py-1 font-mono text-[11px] text-muted uppercase">
            env: mirage · synthetic
          </span>
        </div>
      </header>

      {/* Alert picker — selecting an alert starts (or restarts) its stream. */}
      <nav
        aria-label="Demo alert picker"
        className="flex flex-wrap items-center gap-2 border-b border-edge px-6 py-3"
      >
        <span className="mr-1 font-mono text-[11px] font-semibold tracking-[0.18em] text-muted uppercase">
          Incident
        </span>
        {DEMO_ALERTS.map((alert) => {
          const active = state.alertId === alert.id;
          return (
            <button
              key={alert.id}
              type="button"
              onClick={() => start(alert.id)}
              aria-pressed={active}
              className={`min-h-11 cursor-pointer rounded-lg border px-3 py-1.5 text-left transition-colors duration-200 focus-visible:ring-2 focus-visible:ring-s2 focus-visible:outline-none ${
                active
                  ? "border-accent bg-accent/10 text-ink"
                  : "border-edge bg-panel text-muted hover:border-edge-hi hover:text-ink"
              }`}
            >
              <span
                className={`mr-2 font-mono text-[11px] font-bold ${alert.severity === "P1" ? "text-danger" : "text-muted"}`}
              >
                {alert.severity}
              </span>
              <span className="text-sm">{alert.title}</span>
            </button>
          );
        })}
      </nav>

      <main className="flex min-h-0 flex-1 flex-col gap-4 p-4">
        <div className="grid min-h-0 grid-cols-1 gap-4 lg:grid-cols-[minmax(0,1fr)_minmax(0,1.15fr)_minmax(0,1fr)] lg:[&>section]:max-h-[52vh]">
          <ReasoningPanel state={state} />
          <StoryPanel state={state} />
          <EvidencePanel state={state} />
        </div>
        <IncidentGraph story={state.story} />
      </main>
    </div>
  );
}
