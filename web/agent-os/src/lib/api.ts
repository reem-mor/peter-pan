/**
 * PETER PAN OS control-plane client.
 *
 * Fixture-first contract: every page that calls these fetchers must render
 * a complete synthetic fallback when the backend is unreachable — the
 * console never shows a blank panel because :8005 is down.
 */

/**
 * Where the PETER PAN OS control plane (:8005) lives. Empty string means
 * same-origin: in dev the Vite proxy forwards /os and /healthz to :8005
 * (see vite.config.ts) so no CORS change is needed on the Python side.
 * Set VITE_API_BASE when the built console is served next to a
 * CORS-enabled deployment instead.
 */
export const API_BASE: string = import.meta.env.VITE_API_BASE ?? "";

/** Demo app (Dynamic Incident Dashboard) — incidents deep-link into it. */
export const DEMO_URL: string =
  import.meta.env.VITE_DEMO_URL ?? "http://localhost:5173";

const FETCH_TIMEOUT_MS = 8000;

export async function getJSON<T>(
  path: string,
  signal?: AbortSignal,
): Promise<T> {
  const timeout = AbortSignal.timeout(FETCH_TIMEOUT_MS);
  const res = await fetch(`${API_BASE}${path}`, {
    headers: { Accept: "application/json" },
    signal: signal ? AbortSignal.any([signal, timeout]) : timeout,
  });
  if (!res.ok) throw new Error(`${path} → ${res.status}`);
  return (await res.json()) as T;
}
