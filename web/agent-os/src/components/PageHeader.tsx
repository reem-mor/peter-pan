import type { ReactNode } from "react";

/** Consistent page masthead: title, subtitle, and right-aligned controls. */
export function PageHeader({
  title,
  subtitle,
  children,
}: {
  title: string;
  subtitle: string;
  children?: ReactNode;
}) {
  return (
    <header className="mb-5 flex flex-wrap items-end justify-between gap-3">
      <div>
        <h1 className="font-mono text-lg font-bold tracking-[0.06em] text-ink">
          {title}
        </h1>
        <p className="mt-0.5 text-[13px] text-ink-soft">{subtitle}</p>
      </div>
      {children ? (
        <div className="flex flex-wrap items-center gap-3">{children}</div>
      ) : null}
    </header>
  );
}
