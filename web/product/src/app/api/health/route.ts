import { NextResponse } from "next/server";
import { meshFetch } from "@/lib/backend";

export const runtime = "nodejs";

const SERVICES = ["predictor", "rag", "guardrails", "agent", "ppos"] as const;

export async function GET() {
  const results = await Promise.all(
    SERVICES.map(async (name) => {
      const started = Date.now();
      try {
        const resp = await meshFetch(name, "/healthz");
        const body = await resp.json();
        return {
          name,
          status: resp.ok ? "up" : "down",
          latency_ms: Date.now() - started,
          body,
        };
      } catch (err) {
        return {
          name,
          status: "down",
          latency_ms: Date.now() - started,
          error: err instanceof Error ? err.message : "unreachable",
        };
      }
    }),
  );
  const allUp = results.every((r) => r.status === "up");
  return NextResponse.json(
    { ok: allUp, services: results },
    { status: allUp ? 200 : 503 },
  );
}
