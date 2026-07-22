import Link from "next/link";

export default function LandingPage() {
  return (
    <section className="relative overflow-hidden">
      <div
        aria-hidden
        className="pointer-events-none absolute inset-0 bg-[radial-gradient(ellipse_at_top,_rgba(45,212,191,0.18),_transparent_55%),linear-gradient(180deg,#020617_0%,#0f172a_100%)]"
      />
      <div className="relative mx-auto flex min-h-[80vh] max-w-6xl flex-col justify-center px-6 py-20">
        <p className="font-[family-name:var(--font-mono)] text-xs tracking-[0.28em] text-teal-300 uppercase">
          AI Observability Intelligence
        </p>
        <h1 className="mt-4 max-w-3xl font-[family-name:var(--font-sans)] text-5xl font-semibold tracking-tight text-white md:text-6xl">
          PETER PAN
        </h1>
        <p className="mt-4 max-w-xl text-lg text-slate-300">From Alert to Insight, Faster.</p>
        <p className="mt-6 max-w-2xl text-slate-400">
          Canonical product UI: investigate incidents in{" "}
          <span className="text-slate-200">/app</span>, operate the control plane in{" "}
          <span className="text-slate-200">/os</span>. Streamlit remains an optional internal tool only.
        </p>
        <div className="mt-10 flex flex-wrap gap-4">
          <Link
            href="/app"
            className="rounded-md bg-teal-400 px-5 py-3 font-[family-name:var(--font-mono)] text-sm font-semibold text-slate-950 hover:bg-teal-300"
          >
            Open workspace
          </Link>
          <Link
            href="/os"
            className="rounded-md border border-slate-600 px-5 py-3 font-[family-name:var(--font-mono)] text-sm text-slate-200 hover:border-teal-400/60"
          >
            PETER PAN OS
          </Link>
        </div>
      </div>
    </section>
  );
}
