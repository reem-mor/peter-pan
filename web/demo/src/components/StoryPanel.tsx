import type { StreamState } from "../lib/stream";
import { ConfidenceMeter, EmptyState, Panel, SectionLabel, SeverityBadge } from "./ui";

export function StoryPanel({ state }: { state: StreamState }) {
  const story = state.story;
  return (
    <Panel title="Incident story" hint="What changed, probable cause, repair options">
      {story === null ? (
        <EmptyState>
          {state.phase === "streaming" || state.phase === "connecting"
            ? "synthesizing story…"
            : "no story yet — run an alert"}
        </EmptyState>
      ) : (
        <article className="stream-in flex flex-col gap-4">
          <div className="flex items-center justify-between gap-2">
            <SeverityBadge severity={story.alert.severity} />
            <span className="font-mono text-[11px] text-faint">
              {story.alert.source} · {story.alert.id}
            </span>
          </div>

          <div>
            <SectionLabel>What changed</SectionLabel>
            <p className="mt-1 text-sm leading-relaxed text-ink">{story.what_changed}</p>
            <p className="mt-1 text-sm text-muted">{story.alert.description}</p>
          </div>

          <div>
            <SectionLabel>Probable cause</SectionLabel>
            <p className="mt-1 font-mono text-lg font-bold text-ink">
              {story.probable_cause}
            </p>
          </div>

          <div>
            <SectionLabel>Confidence</SectionLabel>
            <div className="mt-1.5">
              <ConfidenceMeter
                value={story.confidence}
                tone="accent"
                label="story confidence"
              />
            </div>
            <p className="mt-1 text-[11px] text-faint">
              bounded — the agent never claims certainty
            </p>
          </div>

          <div>
            <SectionLabel>Repair options</SectionLabel>
            <ol className="mt-1.5 flex list-none flex-col gap-1.5">
              {story.repair_options.map((option, i) => (
                <li key={option} className="flex gap-2 text-sm text-ink">
                  <span className="font-mono text-[11px] text-faint tabular-nums">
                    {String(i + 1).padStart(2, "0")}
                  </span>
                  {option}
                </li>
              ))}
            </ol>
            <p className="mt-2 text-[11px] text-faint">
              proposals only — mutating actions require human approval
            </p>
          </div>
        </article>
      )}
    </Panel>
  );
}
