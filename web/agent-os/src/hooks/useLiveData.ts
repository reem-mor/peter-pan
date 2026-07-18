/**
 * Poll a control-plane loader on an interval, falling back to a synthetic
 * fixture when the backend is unreachable (fixture-first invariant).
 *
 * All-or-nothing per cycle: a loader either resolves a complete live
 * payload or the whole page renders the fixture. Mixing live budget with
 * fixture usage would be indistinguishable from real data to an operator.
 */

import { useEffect, useState } from "react";

export interface LiveData<T> {
  data: T;
  /** true = backend payload, false = bundled synthetic fixture. */
  live: boolean;
  refreshedAt: Date | null;
}

export function useLiveData<T>(
  loader: (signal: AbortSignal) => Promise<T>,
  fixture: T,
  intervalMs: number,
): LiveData<T> {
  const [state, setState] = useState<LiveData<T>>({
    data: fixture,
    live: false,
    refreshedAt: null,
  });

  useEffect(() => {
    let seq = 0;
    let aborter: AbortController | null = null;
    let disposed = false;

    const tick = async () => {
      const mySeq = ++seq;
      aborter?.abort(); // stale in-flight cycle must not pile up
      aborter = new AbortController();
      let next: LiveData<T>;
      try {
        const data = await loader(aborter.signal);
        next = { data, live: true, refreshedAt: new Date() };
      } catch {
        // Unreachable backend is a state to render, not an error to throw.
        next = { data: fixture, live: false, refreshedAt: new Date() };
      }
      if (!disposed && mySeq === seq) setState(next);
    };

    void tick();
    const timer = setInterval(() => {
      // Poll only while visible — a background ops tab shouldn't hammer
      // the control plane. visibilitychange catches up on return.
      if (!document.hidden) void tick();
    }, intervalMs);
    const onVisible = () => {
      if (!document.hidden) void tick();
    };
    document.addEventListener("visibilitychange", onVisible);

    return () => {
      disposed = true;
      aborter?.abort();
      clearInterval(timer);
      document.removeEventListener("visibilitychange", onVisible);
    };
  }, [loader, fixture, intervalMs]);

  return state;
}
