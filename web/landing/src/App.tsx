import { LeadForm } from "./components/LeadForm";
import { PipelineFlow } from "./components/PipelineFlow";

/**
 * PETER PAN marketing landing page. All copy, icons, and visuals are this
 * project's own design (docs/product-research/original-design-system.md);
 * public incident-tooling sites are pattern references only.
 */

interface Feature {
  title: string;
  body: string;
  /** 24x24 stroke-icon path data — drawn for this project. */
  iconPaths: string[];
}

const FEATURES: Feature[] = [
  {
    title: "Citation trail",
    body: "Every claim in an incident story links back to a metric, log, deploy, or runbook. No orphan assertions — if it can't cite a source, it doesn't ship.",
    iconPaths: [
      "M10.5 13.5a3.5 3.5 0 0 0 5 0l3-3a3.5 3.5 0 0 0-5-5l-1.5 1.5",
      "M13.5 10.5a3.5 3.5 0 0 0-5 0l-3 3a3.5 3.5 0 0 0 5 5l1.5-1.5",
    ],
  },
  {
    title: "ActionPreview gate",
    body: "High-risk remediation renders like a code review — what will run, blast radius, evidence — and never auto-executes. A human approves, recorded with who and when.",
    iconPaths: ["M12 3l7 3v5c0 4.4-2.9 7.4-7 9-4.1-1.6-7-4.6-7-9V6l7-3z", "M9 12l2 2 4-4"],
  },
  {
    title: "Deterministic floors",
    body: "The model explains; it never decides alone. Classification, scoring, and thresholds stay deterministic, unit-tested code that no prompt can talk its way past.",
    iconPaths: ["M12 4l8 4-8 4-8-4 8-4z", "M4 12l8 4 8-4", "M4 16l8 4 8-4"],
  },
  {
    title: "Metered by design",
    body: "Every LLM call logs tokens and cost. PETER PAN OS — the built-in ops console — shows spend per agent, budget status, and tuning tips.",
    iconPaths: ["M5 19a8 8 0 1 1 14 0", "M12 14l3.5-3.5", "M12 14h.01"],
  },
  {
    title: "Fixture-first demo",
    body: "The full demo path runs offline with zero external accounts. Real backends slot in behind the same interfaces when you're ready — nothing to re-architect.",
    iconPaths: ["M12 3l8 4.5v9L12 21l-8-4.5v-9L12 3z", "M4 7.5l8 4.5 8-4.5", "M12 12v9"],
  },
  {
    title: "Bounded agents",
    body: "Tool loops have hard iteration caps and fail loud on errors. Confidence is always below 100% — honesty about uncertainty is a type-level guarantee.",
    iconPaths: ["M20 12a8 8 0 1 1-2.34-5.66", "M20 3v4h-4"],
  },
];

// Clearly synthetic logo placeholders — invented names, drawn as monograms.
const PLACEHOLDER_LOGOS = [
  { initials: "AC", name: "Acme Cloud" },
  { initials: "EC", name: "Example Corp" },
  { initials: "SS", name: "Sample Systems" },
  { initials: "FL", name: "Fixture Labs" },
  { initials: "PI", name: "Placeholder Inc" },
  { initials: "DI", name: "Demo Industries" },
];

function FeatureIcon({ paths }: { paths: string[] }) {
  return (
    <svg
      aria-hidden="true"
      focusable="false"
      viewBox="0 0 24 24"
      className="h-6 w-6 text-accent-strong"
      fill="none"
      stroke="currentColor"
      strokeWidth={1.8}
      strokeLinecap="round"
      strokeLinejoin="round"
    >
      {paths.map((d) => (
        <path key={d} d={d} />
      ))}
    </svg>
  );
}

function LogoBadge({ initials, name }: { initials: string; name: string }) {
  return (
    <li className="flex items-center gap-3 text-ink-soft">
      <svg
        aria-hidden="true"
        focusable="false"
        viewBox="0 0 40 40"
        className="h-10 w-10 shrink-0"
      >
        <rect
          x="1.5"
          y="1.5"
          width="37"
          height="37"
          rx="9"
          fill="none"
          stroke="currentColor"
          strokeWidth="1.5"
        />
        <text
          x="20"
          y="25.5"
          textAnchor="middle"
          fontSize="14"
          fontWeight="700"
          fill="currentColor"
        >
          {initials}
        </text>
      </svg>
      <span className="text-sm font-semibold">{name}</span>
    </li>
  );
}

export default function App() {
  return (
    <div className="min-h-screen bg-surface font-display text-ink">
      <a
        href="#main"
        className="sr-only focus:not-sr-only focus:absolute focus:top-3 focus:left-3 focus:z-50 focus:rounded-lg focus:bg-surface-raised focus:px-4 focus:py-2 focus:font-semibold"
      >
        Skip to content
      </a>

      <header className="border-b border-ink/10">
        <nav
          aria-label="Main"
          className="mx-auto flex max-w-6xl items-center justify-between gap-4 px-6 py-4"
        >
          <a href="#main" className="text-sm font-bold tracking-widest uppercase">
            Peter Pan
          </a>
          <div className="flex items-center gap-6">
            <a
              href="#how-it-works"
              className="hidden text-sm font-semibold text-ink-soft hover:text-ink sm:block"
            >
              How it works
            </a>
            <a
              href="#features"
              className="hidden text-sm font-semibold text-ink-soft hover:text-ink sm:block"
            >
              Features
            </a>
            <a
              href="#get-a-demo"
              className="rounded-lg bg-accent-strong px-4 py-2 text-sm font-semibold text-white transition-colors hover:bg-accent-deep"
            >
              Get a demo
            </a>
          </div>
        </nav>
      </header>

      <main id="main">
        {/* Hero */}
        <section
          aria-labelledby="hero-heading"
          className="mx-auto max-w-5xl px-6 pt-20 pb-16 text-center sm:pt-24"
        >
          <p className="text-sm font-semibold tracking-widest text-accent-strong uppercase">
            Peter Pan — Predictive, Agentic Navigator
          </p>
          <h1 id="hero-heading" className="mt-4 text-4xl font-bold tracking-tight sm:text-5xl">
            Incidents explained, with the evidence attached.
          </h1>
          <p className="mx-auto mt-6 max-w-2xl text-lg leading-relaxed text-ink-soft">
            PETER PAN turns a raw alert into a story your on-call can trust: what changed, the
            probable cause, and every claim cited back to its source. Remediation is proposed,
            previewed, and runs only after a human approves.
          </p>
          <div className="mt-10 flex flex-wrap items-center justify-center gap-4">
            <a
              href="#get-a-demo"
              className="rounded-lg bg-accent-strong px-6 py-3 font-semibold text-white transition-colors hover:bg-accent-deep"
            >
              Get a demo
            </a>
            <a
              href="#how-it-works"
              className="rounded-lg border border-ink/20 px-6 py-3 font-semibold transition-colors hover:border-ink/40"
            >
              See how it works
            </a>
          </div>
        </section>

        {/* Product story */}
        <section
          id="how-it-works"
          aria-labelledby="how-heading"
          className="border-y border-ink/10 bg-surface-raised/60"
        >
          <div className="mx-auto max-w-6xl px-6 py-16 sm:py-20">
            <h2 id="how-heading" className="text-center text-3xl font-bold tracking-tight">
              From page to plan, in five auditable steps
            </h2>
            <p className="mx-auto mt-4 max-w-2xl text-center text-ink-soft">
              One pipeline from alert to approved fix — every step leaves a trail you can review
              afterwards.
            </p>
            <div className="mt-12">
              <PipelineFlow />
            </div>
          </div>
        </section>

        {/* Feature grid */}
        <section
          id="features"
          aria-labelledby="features-heading"
          className="mx-auto max-w-6xl px-6 py-16 sm:py-20"
        >
          <h2 id="features-heading" className="text-center text-3xl font-bold tracking-tight">
            Guardrails as product, not fine print
          </h2>
          <p className="mx-auto mt-4 max-w-2xl text-center text-ink-soft">
            The invariants below are enforced in code and tests — they are what make an AI
            incident copilot safe to put on-call.
          </p>
          <ul className="mt-12 grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
            {FEATURES.map((feature) => (
              <li
                key={feature.title}
                className="rounded-xl border border-ink/10 bg-surface-raised p-6"
              >
                <FeatureIcon paths={feature.iconPaths} />
                <h3 className="mt-4 font-semibold">{feature.title}</h3>
                <p className="mt-2 text-sm leading-relaxed text-ink-soft">{feature.body}</p>
              </li>
            ))}
          </ul>
        </section>

        {/* Social proof placeholders */}
        <section
          aria-labelledby="social-proof-heading"
          className="border-y border-ink/10 bg-surface-raised/60"
        >
          <div className="mx-auto max-w-6xl px-6 py-14 text-center">
            <h2
              id="social-proof-heading"
              className="text-sm font-semibold tracking-widest text-ink-soft uppercase"
            >
              Trusted by teams like yours
            </h2>
            <ul className="mt-8 flex flex-wrap items-center justify-center gap-x-10 gap-y-6">
              {PLACEHOLDER_LOGOS.map((logo) => (
                <LogoBadge key={logo.initials} initials={logo.initials} name={logo.name} />
              ))}
            </ul>
            <p className="mt-6 text-xs text-ink-soft">
              Illustrative placeholders — synthetic brands, not real customers.
            </p>
          </div>
        </section>

        {/* Lead form */}
        <section
          id="get-a-demo"
          aria-labelledby="demo-heading"
          className="mx-auto max-w-3xl px-6 py-16 sm:py-20"
        >
          <h2 id="demo-heading" className="text-center text-3xl font-bold tracking-tight">
            Get a demo
          </h2>
          <p className="mx-auto mt-4 max-w-xl text-center text-ink-soft">
            Tell us a little about your on-call setup and we&apos;ll walk you through the demo
            path — fixture-first, so it runs without touching your systems.
          </p>
          <div className="mt-10">
            <LeadForm />
          </div>
        </section>
      </main>

      <footer className="border-t border-ink/10">
        <div className="mx-auto flex max-w-6xl flex-col items-center gap-4 px-6 py-8 text-center text-sm text-ink-soft sm:flex-row sm:justify-between sm:text-left">
          <p>
            PETER PAN — synthetic demo content only. No real incidents, no real data.
          </p>
          <nav aria-label="Footer">
            <ul className="flex items-center gap-6">
              <li>
                <a href="#how-it-works" className="hover:text-ink">
                  How it works
                </a>
              </li>
              <li>
                <a href="#features" className="hover:text-ink">
                  Features
                </a>
              </li>
              <li>
                <a href="#get-a-demo" className="hover:text-ink">
                  Get a demo
                </a>
              </li>
            </ul>
          </nav>
        </div>
      </footer>
    </div>
  );
}
