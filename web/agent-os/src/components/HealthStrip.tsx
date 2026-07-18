/**
 * Global repo/system health strip: live mesh healthz sweep (/os/services)
 * plus the last eval-suite scores (fixture — the eval harness has no HTTP
 * feed yet). Renders on every page under the header.
 */

import { useLiveData } from "../hooks/useLiveData";
import { fetchServices, type ServiceHealth } from "../lib/os";
import {
  FIXTURE_EVAL_SCORES,
  FIXTURE_SERVICES,
} from "../fixtures/health";

const POLL_MS = 30_000;

// Module scope: stable references so useLiveData's effect never re-arms.
const loadServices = async (signal: AbortSignal): Promise<ServiceHealth[]> =>
  (await fetchServices(signal)).services;

function ServiceDot({ svc }: { svc: ServiceHealth }) {
  const up = svc.status === "up";
  return (
    <span className="inline-flex items-center gap-1.5 font-mono text-[11px] text-ink-soft">
      <span
        aria-hidden="true"
        className={`h-[7px] w-[7px] rounded-full ${
          up ? "bg-accent shadow-[0_0_6px_var(--color-accent)]" : "bg-red"
        }`}
      />
      {svc.name}
      <span className={up ? "text-ink-faint" : "font-bold text-red"}>
        {up
          ? svc.latency_ms != null
            ? `${svc.latency_ms}ms`
            : "up"
          : "down"}
      </span>
    </span>
  );
}

export function HealthStrip() {
  const { data: services, live } = useLiveData(
    loadServices,
    FIXTURE_SERVICES,
    POLL_MS,
  );

  return (
    <div
      className="flex flex-wrap items-center gap-x-5 gap-y-2 border-b border-edge bg-panel/60 px-6 py-2"
      role="region"
      aria-label="System health"
    >
      <span className="font-mono text-[10px] tracking-[0.16em] text-ink-faint uppercase">
        mesh {live ? "· live" : "· fixture"}
      </span>
      {services.map((svc) => (
        <ServiceDot key={svc.name} svc={svc} />
      ))}
      <span
        aria-hidden="true"
        className="hidden h-4 w-px bg-edge-hi sm:inline-block"
      />
      <span className="font-mono text-[10px] tracking-[0.16em] text-ink-faint uppercase">
        last evals · fixture
      </span>
      {FIXTURE_EVAL_SCORES.map((e) => {
        const pass = e.score >= e.threshold;
        return (
          <span
            key={e.suite}
            className="inline-flex items-center gap-1.5 font-mono text-[11px] text-ink-soft"
            title={`threshold ${e.threshold.toFixed(2)}`}
          >
            {e.suite}
            <span className={pass ? "text-accent" : "font-bold text-red"}>
              {e.score.toFixed(2)}
              {pass ? "" : " ✗"}
            </span>
          </span>
        );
      })}
    </div>
  );
}
