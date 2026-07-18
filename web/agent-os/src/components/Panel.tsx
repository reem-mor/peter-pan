import type { ReactNode } from "react";

/** Standard console panel — dark card with a mono uppercase heading. */
export function Panel({
  title,
  hint,
  children,
  className = "",
}: {
  title: string;
  hint?: string;
  children: ReactNode;
  className?: string;
}) {
  return (
    <section
      className={`rounded-xl border border-edge bg-panel p-[18px] transition-colors hover:border-edge-hi ${className}`}
    >
      <h2 className="mb-3.5 flex items-baseline gap-2 font-mono text-[11px] font-semibold tracking-[0.18em] text-ink-soft uppercase">
        {title}
        {hint ? (
          <span className="font-normal tracking-[0.06em] text-ink-faint normal-case">
            · {hint}
          </span>
        ) : null}
      </h2>
      {children}
    </section>
  );
}
