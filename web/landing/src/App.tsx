const FEATURES = [
  {
    title: "Evidence, always cited",
    body: "Every claim in an incident story links back to a metric, log, or deploy. Placeholder copy.",
  },
  {
    title: "Human-approved remediation",
    body: "High-risk actions never auto-execute — the approval gate is a product invariant. Placeholder copy.",
  },
  {
    title: "Deterministic safety floors",
    body: "The model explains; thresholds and scoring stay deterministic and tested. Placeholder copy.",
  },
  {
    title: "Metered by design",
    body: "Every LLM call is logged and costed — PETER PAN OS shows the spend. Placeholder copy.",
  },
  {
    title: "Fixture-first demo",
    body: "The full demo path runs with zero external accounts. Placeholder copy.",
  },
  {
    title: "Environment-aware",
    body: "Mirage, staging, production — production is read-only plus approvals. Placeholder copy.",
  },
];

export default function App() {
  return (
    <div className="min-h-screen bg-surface font-display text-ink">
      {/* Hero placeholder */}
      <header className="mx-auto max-w-5xl px-6 pt-24 pb-16 text-center">
        <p className="text-sm font-semibold tracking-widest text-accent uppercase">
          PETER PAN
        </p>
        <h1 className="mt-4 text-5xl font-bold tracking-tight">
          Predictive, Agentic Navigator
        </h1>
        <p className="mx-auto mt-6 max-w-2xl text-lg text-ink-soft">
          Incident intelligence: evidence collection, an explained incident
          story, and human-approved remediation. (Hero placeholder — final
          copy and visuals land in a later workstream.)
        </p>
        <button
          type="button"
          className="mt-10 rounded-lg bg-accent px-6 py-3 font-semibold text-white transition-colors hover:bg-accent-strong"
        >
          Get a demo
        </button>
      </header>

      {/* Feature grid placeholder */}
      <main className="mx-auto max-w-5xl px-6 pb-24">
        <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
          {FEATURES.map((feature) => (
            <div
              key={feature.title}
              className="rounded-xl border border-ink/10 bg-surface-raised p-6"
            >
              <h2 className="font-semibold">{feature.title}</h2>
              <p className="mt-2 text-sm text-ink-soft">{feature.body}</p>
            </div>
          ))}
        </div>
      </main>

      <footer className="border-t border-ink/10 py-8 text-center text-sm text-ink-soft">
        PETER PAN — synthetic demo content only. No real incidents, no real
        data.
      </footer>
    </div>
  );
}
