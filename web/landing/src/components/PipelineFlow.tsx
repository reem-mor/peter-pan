/**
 * The product story as a five-step flow: ingest → reason → retrieve →
 * propose → approve. Rendered as a real ordered list (screen readers get
 * the sequence for free); connector arrows are decorative SVG.
 */

const STEPS = [
  {
    title: "Ingest",
    body: "An alert lands from monitoring — pager, webhook, dashboard. It is treated as untrusted input: data to explain, never instructions to follow.",
  },
  {
    title: "Reason",
    body: "Deterministic floors classify and score first; the model adds the explanation on top. Thresholds stay unit-tested code, not vibes.",
  },
  {
    title: "Retrieve",
    body: "Runbooks, past incidents, and deploy history are pulled in as evidence — every item carries the source it came from.",
  },
  {
    title: "Propose",
    body: "Remediation arrives as an ActionPreview: what will run, its blast radius, and the evidence supporting it — laid out like a code review.",
  },
  {
    title: "Approve",
    body: "A human signs off before anything mutating executes. In production the gate is absolute: read-only until someone approves.",
  },
];

function ConnectorArrow() {
  return (
    <svg
      aria-hidden="true"
      focusable="false"
      viewBox="0 0 24 24"
      className="absolute top-1/2 -right-5 hidden h-5 w-5 -translate-y-1/2 text-accent lg:block"
      fill="none"
      stroke="currentColor"
      strokeWidth={2}
      strokeLinecap="round"
      strokeLinejoin="round"
    >
      <path d="M3 12h17M14 6l6 6-6 6" />
    </svg>
  );
}

export function PipelineFlow() {
  return (
    <ol className="grid gap-6 sm:grid-cols-2 lg:grid-cols-5 lg:gap-7">
      {STEPS.map((step, index) => (
        <li
          key={step.title}
          className="relative rounded-xl border border-ink/10 bg-surface-raised p-5"
        >
          <span
            aria-hidden="true"
            className="inline-flex h-8 w-8 items-center justify-center rounded-full border border-accent/40 text-sm font-bold text-accent-strong"
          >
            {index + 1}
          </span>
          <h3 className="mt-3 font-semibold">{step.title}</h3>
          <p className="mt-2 text-sm leading-relaxed text-ink-soft">{step.body}</p>
          {index < STEPS.length - 1 && <ConnectorArrow />}
        </li>
      ))}
    </ol>
  );
}
