"use client";

import { useEffect, useState } from "react";

type HealthRow = {
  name: string;
  status: string;
  latency_ms: number;
  body?: Record<string, unknown>;
  error?: string;
};

export default function OsPage() {
  const [rows, setRows] = useState<HealthRow[]>([]);
  const [info, setInfo] = useState<Record<string, unknown> | null>(null);
  const [state, setState] = useState<"loading" | "success" | "degraded" | "upstream failure">("loading");

  useEffect(() => {
    let cancelled = false;
    async function load() {
      try {
        const [healthResp, infoResp] = await Promise.all([
          fetch("/api/health"),
          fetch("/api/os/info"),
        ]);
        const health = await healthResp.json();
        const infoJson = infoResp.ok ? await infoResp.json() : null;
        if (cancelled) return;
        setRows(health.services ?? []);
        setInfo(infoJson);
        setState(health.ok ? "success" : "degraded");
      } catch {
        if (!cancelled) setState("upstream failure");
      }
    }
    void load();
    const id = setInterval(() => void load(), 15000);
    return () => {
      cancelled = true;
      clearInterval(id);
    };
  }, []);

  return (
    <div className="mx-auto max-w-6xl px-6 py-10">
      <h1 className="font-[family-name:var(--font-mono)] text-sm tracking-[0.2em] text-teal-300 uppercase">
        PETER PAN OS
      </h1>
      <p className="mt-2 text-slate-400">
        Control plane · state <span className="text-slate-100">{state}</span>
      </p>

      <div className="mt-8 grid gap-4 md:grid-cols-5">
        {rows.map((row) => (
          <div key={row.name} className="rounded-lg border border-slate-800 bg-slate-900/60 p-4">
            <p className="font-[family-name:var(--font-mono)] text-xs uppercase text-slate-500">{row.name}</p>
            <p className={`mt-2 text-lg ${row.status === "up" ? "text-teal-300" : "text-rose-300"}`}>
              {row.status}
            </p>
            <p className="text-xs text-slate-500">{row.latency_ms} ms</p>
          </div>
        ))}
      </div>

      {info ? (
        <pre className="mt-8 overflow-auto rounded-lg border border-slate-800 bg-slate-900/60 p-4 font-[family-name:var(--font-mono)] text-xs text-slate-300">
          {JSON.stringify(info, null, 2)}
        </pre>
      ) : null}
    </div>
  );
}
