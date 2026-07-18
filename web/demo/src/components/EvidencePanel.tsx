import type { Evidence } from "@peterpan/types";
import type { StreamState } from "../lib/stream";
import { ConfidenceMeter, EmptyState, Panel } from "./ui";

function EvidenceCard({ evidence }: { evidence: Evidence }) {
  return (
    <li className="stream-in rounded-lg border border-edge bg-well p-3 transition-colors duration-200 hover:border-edge-hi">
      <span className="inline-block rounded-full border border-edge px-2 py-0.5 font-mono text-[10.5px] font-semibold tracking-wider text-muted uppercase">
        {evidence.kind}
      </span>
      <p className="mt-2 text-sm leading-relaxed text-ink">{evidence.summary}</p>
      {/* Citation trail — every claim renders with its source (invariant). */}
      <p className="mt-2 truncate font-mono text-[11px] text-faint" title={evidence.source}>
        <span className="mr-1 text-muted">src</span>
        {evidence.source}
      </p>
      <div className="mt-2">
        <ConfidenceMeter
          value={evidence.confidence}
          label={`evidence confidence for ${evidence.kind}`}
        />
      </div>
    </li>
  );
}

export function EvidencePanel({ state }: { state: StreamState }) {
  return (
    <Panel title="Evidence" hint="Collected context, every claim cited">
      {state.evidence.length === 0 ? (
        <EmptyState>
          {state.phase === "streaming" || state.phase === "connecting"
            ? "collecting evidence…"
            : "no evidence in window"}
        </EmptyState>
      ) : (
        <ul className="flex list-none flex-col gap-3">
          {state.evidence.map((e, i) => (
            <EvidenceCard key={`${e.source}-${i}`} evidence={e} />
          ))}
        </ul>
      )}
    </Panel>
  );
}
