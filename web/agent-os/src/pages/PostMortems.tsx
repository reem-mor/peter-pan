/**
 * Post-mortems — synthetic write-ups bundled as fixtures in the exact
 * style of knowledge/incidents/*.md (the same corpus the RAG service
 * retrieves from). Blameless by construction.
 */

import { FIXTURE_POSTMORTEMS } from "../fixtures/postmortems";
import { PageHeader } from "../components/PageHeader";
import { SeverityPill } from "../components/Pill";

function Section({ label, body }: { label: string; body: string }) {
  return (
    <div className="mt-3">
      <h4 className="font-mono text-[10.5px] font-semibold tracking-[0.16em] text-ink-faint uppercase">
        {label}
      </h4>
      <p className="mt-1 text-sm leading-relaxed text-ink-soft">{body}</p>
    </div>
  );
}

export function PostMortems() {
  return (
    <div className="p-6">
      <PageHeader
        title="Post-mortems"
        subtitle="Blameless write-ups from the synthetic incident corpus — the same documents the RAG service cites in incident stories."
      >
        <span className="rounded-full border border-edge px-3 py-1 font-mono text-[11px] tracking-[0.1em] text-ink-soft uppercase">
          synthetic corpus
        </span>
      </PageHeader>

      <div className="flex flex-col gap-4">
        {FIXTURE_POSTMORTEMS.map((pm) => (
          <article
            key={pm.id}
            className="rounded-xl border border-edge bg-panel p-5 transition-colors hover:border-edge-hi"
          >
            <header className="flex flex-wrap items-center gap-2.5">
              <SeverityPill severity={pm.severity} />
              <span className="font-mono text-xs text-ink-faint">{pm.id}</span>
              <span className="font-mono text-xs text-ink-faint">{pm.date}</span>
              <span className="font-mono text-xs text-ink-faint">
                {pm.durationMin} min
              </span>
              <span className="rounded-md border border-edge px-2 py-0.5 font-mono text-[10.5px] tracking-[0.08em] text-ink-faint">
                class: {pm.incidentClass}
              </span>
            </header>
            <h3 className="mt-2 text-base font-semibold text-ink">{pm.title}</h3>

            <Section label="What happened" body={pm.whatHappened} />
            <Section label="Detection" body={pm.detection} />
            <Section label="Resolution" body={pm.resolution} />

            <div className="mt-3">
              <h4 className="font-mono text-[10.5px] font-semibold tracking-[0.16em] text-ink-faint uppercase">
                Lessons
              </h4>
              <ul className="mt-1.5 flex flex-col gap-1.5">
                {pm.lessons.map((lesson) => (
                  <li
                    key={lesson}
                    className="flex items-start gap-2.5 text-sm leading-relaxed text-ink-soft"
                  >
                    <span
                      aria-hidden="true"
                      className="mt-2 h-1.5 w-1.5 shrink-0 rounded-full bg-accent"
                    />
                    {lesson}
                  </li>
                ))}
              </ul>
            </div>

            <footer className="mt-4 border-t border-edge pt-2.5 font-mono text-[10.5px] text-ink-faint italic">
              Synthetic incident — demo data, no real systems.
            </footer>
          </article>
        ))}
      </div>
    </div>
  );
}
