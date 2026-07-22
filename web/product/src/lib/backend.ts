/**
 * Server-only mesh client. Holds PP_API_TOKEN — never imported from Client
 * Components. Browser calls go through /api/* BFF routes in this app.
 */

const TOKEN_HEADER = "X-PP-Token";

function meshBase(service: "predictor" | "rag" | "guardrails" | "agent" | "ppos"): string {
  const envKey = {
    predictor: "PP_PREDICTOR_BASE",
    rag: "PP_RAG_BASE",
    guardrails: "PP_GUARDRAILS_BASE",
    agent: "PP_AGENT_BASE",
    ppos: "PP_PPOS_BASE",
  }[service];
  const fallback = {
    predictor: "http://127.0.0.1:8001",
    rag: "http://127.0.0.1:8002",
    guardrails: "http://127.0.0.1:8003",
    agent: "http://127.0.0.1:8004",
    ppos: "http://127.0.0.1:8005",
  }[service];
  return (process.env[envKey] ?? fallback).replace(/\/$/, "");
}

export async function meshFetch(
  service: "predictor" | "rag" | "guardrails" | "agent" | "ppos",
  path: string,
  init: RequestInit = {},
): Promise<Response> {
  const headers = new Headers(init.headers);
  headers.set("Accept", "application/json");
  const token = process.env.PP_API_TOKEN;
  if (token) {
    headers.set(TOKEN_HEADER, token);
  }
  return fetch(`${meshBase(service)}${path}`, {
    ...init,
    headers,
    cache: "no-store",
  });
}
