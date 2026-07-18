/**
 * Incidents — recent incidents from the synthetic demo catalog, each deep-
 * linking into the demo app's Dynamic Incident Dashboard. Fixture-only for
 * now: the live catalog endpoint lands with the demo-app workstream.
 */

import { DEMO_URL } from "../lib/api";
import { fmtDate } from "../lib/format";
import { FIXTURE_INCIDENTS } from "../fixtures/incidents";
import { PageHeader } from "../components/PageHeader";
import { SeverityPill, StatusPill } from "../components/Pill";

export function Incidents() {
  return (
    <div className="p-6">
      <PageHeader
        title="Incidents"
        subtitle="Recent incidents from the synthetic demo catalog — open one in the demo app for the full explained story."
      >
        <span className="rounded-full border border-edge px-3 py-1 font-mono text-[11px] tracking-[0.1em] text-ink-soft uppercase">
          synthetic catalog
        </span>
      </PageHeader>

      <ul className="flex flex-col gap-3">
        {FIXTURE_INCIDENTS.map((inc) => (
          <li
            key={inc.id}
            className="rounded-xl border border-edge bg-panel p-4 transition-colors hover:border-edge-hi"
          >
            <div className="flex flex-wrap items-center gap-2.5">
              <SeverityPill severity={inc.severity} />
              <StatusPill status={inc.status} />
              <span className="font-mono text-xs text-ink-faint">{inc.id}</span>
              <span className="font-mono text-xs text-ink-faint">
                {inc.service}
              </span>
              <span className="font-mono text-xs text-ink-faint">
                {fmtDate(inc.startedAt)}
                {inc.durationMin != null ? ` · ${inc.durationMin} min` : " · ongoing"}
              </span>
              <span className="ml-auto font-mono text-[11px] text-ink-faint">
                story confidence{" "}
                <span className="text-ink-soft">
                  {inc.storyConfidence.toFixed(2)}
                </span>{" "}
                (never 1.00)
              </span>
            </div>
            <h3 className="mt-2 text-[15px] font-semibold text-ink">
              {inc.title}
            </h3>
            <p className="mt-1 text-sm text-ink-soft">{inc.summary}</p>
            <div className="mt-3 flex flex-wrap items-center gap-3">
              <span className="rounded-md border border-edge px-2 py-0.5 font-mono text-[10.5px] tracking-[0.08em] text-ink-faint">
                class: {inc.incidentClass}
              </span>
              <a
                href={`${DEMO_URL}/?incident=${encodeURIComponent(inc.id)}`}
                target="_blank"
                rel="noopener noreferrer"
                className="ml-auto rounded-md border border-accent/45 bg-accent-dim px-3 py-1 font-mono text-xs font-semibold text-accent transition-colors hover:border-accent"
              >
                open in demo app ↗
              </a>
            </div>
          </li>
        ))}
      </ul>
    </div>
  );
}
