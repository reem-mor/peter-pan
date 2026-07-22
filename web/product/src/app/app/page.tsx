"use client";

import { useState } from "react";

type ProviderReport = {
  llm: string;
  llm_fallback: boolean;
  rag_backend: string;
  rag_fallback: boolean;
  rag_fallback_reason: string;
  predictor: string;
  predictor_model_version: string;
  agent_provider: string;
};

type Story = {
  probable_cause: string;
  confidence: number;
  what_changed: string;
  evidence: { kind: string; summary: string; source: string; confidence: number }[];
  repair_options: string[];
  providers?: ProviderReport;
};

type UiState = "initial" | "loading" | "success" | "fallback" | "rejected" | "upstream failure";

export default function AppWorkspacePage() {
  const [title, setTitle] = useState("checkout OOMKilled");
  const [description, setDescription] = useState("pod restarted twice, memory at limit");
  const [state, setState] = useState<UiState>("initial");
  const [story, setStory] = useState<Story | null>(null);
  const [error, setError] = useState("");

  async function investigate() {
    setState("loading");
    setError("");
    setStory(null);
    try {
      const resp = await fetch("/api/story", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          id: `ui-${Date.now()}`,
          source: "next-app",
          title,
          description,
          severity: "P2",
          received_at: new Date().toISOString(),
        }),
      });
      if (!resp.ok) {
        setState(resp.status === 422 ? "rejected" : "upstream failure");
        setError(await resp.text());
        return;
      }
      const body = (await resp.json()) as Story;
      setStory(body);
      const fallback =
        body.providers?.llm_fallback ||
        body.providers?.rag_fallback ||
        body.providers?.llm === "deterministic-fallback";
      setState(fallback ? "fallback" : "success");
    } catch (err) {
      setState("upstream failure");
      setError(err instanceof Error ? err.message : "request failed");
    }
  }

  return (
    <div className="mx-auto max-w-6xl px-6 py-10">
      <h1 className="font-[family-name:var(--font-mono)] text-sm tracking-[0.2em] text-teal-300 uppercase">
        Incident workspace
      </h1>
      <p className="mt-2 text-slate-400">
        State: <span className="text-slate-100">{state}</span>
      </p>

      <div className="mt-8 grid gap-6 md:grid-cols-2">
        <div className="space-y-4 rounded-lg border border-slate-800 bg-slate-900/60 p-5">
          <label className="block text-sm text-slate-300">
            Alert title
            <input
              className="mt-1 w-full rounded border border-slate-700 bg-slate-950 px-3 py-2"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
            />
          </label>
          <label className="block text-sm text-slate-300">
            Description
            <textarea
              className="mt-1 w-full rounded border border-slate-700 bg-slate-950 px-3 py-2"
              rows={4}
              value={description}
              onChange={(e) => setDescription(e.target.value)}
            />
          </label>
          <button
            type="button"
            onClick={investigate}
            className="rounded-md bg-teal-400 px-4 py-2 font-[family-name:var(--font-mono)] text-sm font-semibold text-slate-950"
          >
            Investigate
          </button>
          {error ? <pre className="overflow-auto text-xs text-rose-300">{error}</pre> : null}
        </div>

        <div className="rounded-lg border border-slate-800 bg-slate-900/60 p-5">
          {!story ? (
            <p className="text-slate-500">Submit an alert to build an Incident Story.</p>
          ) : (
            <div className="space-y-3 text-sm">
              <p>
                <span className="text-slate-500">Probable cause</span>
                <br />
                <span className="text-lg text-white">{story.probable_cause}</span>{" "}
                <span className="text-slate-400">({(story.confidence * 100).toFixed(0)}%)</span>
              </p>
              <p className="text-slate-300">{story.what_changed}</p>
              {story.providers ? (
                <dl className="grid grid-cols-2 gap-2 rounded border border-slate-800 p-3 font-[family-name:var(--font-mono)] text-xs">
                  <div>llm: {story.providers.llm}</div>
                  <div>rag: {story.providers.rag_backend}</div>
                  <div>predictor: {story.providers.predictor}</div>
                  <div>agent: {story.providers.agent_provider}</div>
                </dl>
              ) : null}
              <ul className="space-y-2">
                {story.evidence.map((e) => (
                  <li key={`${e.source}-${e.summary}`} className="border-l-2 border-teal-500/40 pl-3">
                    <div className="text-slate-200">{e.summary}</div>
                    <div className="font-[family-name:var(--font-mono)] text-xs text-slate-500">{e.source}</div>
                  </li>
                ))}
              </ul>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
