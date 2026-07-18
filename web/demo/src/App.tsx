import type { ReactNode } from "react";
import type { Alert } from "@peterpan/types";

/** Synthetic placeholder alert — real data arrives via SSE in a later workstream. */
const PLACEHOLDER_ALERT: Alert = {
  id: "alrt-demo-0001",
  source: "grafana",
  title: "checkout-api p99 latency above threshold",
  description: "Synthetic demo alert. No real incident data.",
  severity: "P2",
  received_at: "2026-01-01T00:00:00Z",
  labels: { service: "checkout-api", env: "mirage" },
};

function PanelShell({
  title,
  hint,
  children,
}: {
  title: string;
  hint: string;
  children?: ReactNode;
}) {
  return (
    <section className="flex min-h-0 flex-col rounded-xl border border-edge bg-surface-raised">
      <header className="border-b border-edge px-4 py-3">
        <h2 className="text-sm font-semibold">{title}</h2>
        <p className="text-xs text-ink-soft">{hint}</p>
      </header>
      <div className="flex-1 overflow-y-auto p-4">{children}</div>
    </section>
  );
}

export default function App() {
  return (
    <div className="flex h-screen flex-col bg-surface font-display text-ink">
      <header className="flex items-center justify-between border-b border-edge px-6 py-3">
        <h1 className="text-sm font-semibold tracking-widest uppercase">
          PETER PAN <span className="text-ink-soft">/ live demo</span>
        </h1>
        <span className="rounded-full border border-edge px-3 py-1 text-xs text-ink-soft">
          env: mirage (synthetic)
        </span>
      </header>

      <main className="grid min-h-0 flex-1 grid-cols-1 gap-4 p-4 lg:grid-cols-[minmax(0,1fr)_minmax(0,1.2fr)_minmax(0,1fr)]">
        <PanelShell
          title="Incident timeline"
          hint="Alerts and evidence as they arrive"
        >
          <div className="rounded-lg border border-edge p-3">
            <div className="flex items-center justify-between">
              <span className="text-xs font-semibold text-signal">
                {PLACEHOLDER_ALERT.severity}
              </span>
              <span className="text-xs text-ink-soft">
                {PLACEHOLDER_ALERT.source}
              </span>
            </div>
            <p className="mt-1 text-sm">{PLACEHOLDER_ALERT.title}</p>
          </div>
          <p className="mt-4 text-xs text-ink-soft">
            Timeline entries render here. (Placeholder.)
          </p>
        </PanelShell>

        <PanelShell
          title="Agent reasoning"
          hint="Live reasoning stream — SSE wiring lands in a later workstream"
        >
          <p className="text-xs text-ink-soft italic">
            Waiting for a run… (intentionally empty)
          </p>
        </PanelShell>

        <PanelShell
          title="Incident story"
          hint="What changed, probable cause, evidence, repair options"
        >
          <p className="text-xs text-ink-soft">
            The explained IncidentStory renders here, every claim cited.
            (Placeholder.)
          </p>
        </PanelShell>
      </main>
    </div>
  );
}
