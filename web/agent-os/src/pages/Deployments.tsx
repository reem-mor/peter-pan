/**
 * Deployments — synthetic change feed typed against the shared Deployment
 * schema, with correlated-incident badges (the change timeline is how the
 * agent answers "what changed?").
 */

import { fmtDate } from "../lib/format";
import { FIXTURE_DEPLOYMENTS } from "../fixtures/deployments";
import { PageHeader } from "../components/PageHeader";

export function Deployments() {
  return (
    <div className="p-6">
      <PageHeader
        title="Deployments"
        subtitle="Synthetic change feed — deploys the agent correlates with incidents carry a badge."
      >
        <span className="rounded-full border border-edge px-3 py-1 font-mono text-[11px] tracking-[0.1em] text-ink-soft uppercase">
          synthetic feed
        </span>
      </PageHeader>

      <div className="overflow-x-auto rounded-xl border border-edge bg-panel">
        <table className="w-full border-collapse font-mono text-[13px]">
          <caption className="sr-only">
            Recent deployments with incident correlation
          </caption>
          <thead>
            <tr>
              {["When", "Service", "Version", "Summary", "Author", "Correlation"].map(
                (h) => (
                  <th
                    key={h}
                    scope="col"
                    className="border-b border-edge px-4 py-3 text-left text-[10.5px] font-semibold tracking-[0.12em] text-ink-faint uppercase"
                  >
                    {h}
                  </th>
                ),
              )}
            </tr>
          </thead>
          <tbody>
            {FIXTURE_DEPLOYMENTS.map(({ deployment: d, correlatedIncident }) => (
              <tr key={d.id} className="hover:bg-panel-2">
                <td className="border-b border-bg-grid px-4 py-3 whitespace-nowrap text-ink-soft">
                  {fmtDate(d.deployed_at)}
                </td>
                <td className="border-b border-bg-grid px-4 py-3">{d.service}</td>
                <td className="border-b border-bg-grid px-4 py-3 text-cyan">
                  {d.version}
                </td>
                <td className="border-b border-bg-grid px-4 py-3 font-display text-sm text-ink">
                  {d.summary}
                  <span className="mt-1 block font-mono text-[10.5px] text-ink-faint">
                    {Object.entries(d.labels)
                      .map(([k, v]) => `${k}=${v}`)
                      .join(" · ")}
                  </span>
                </td>
                <td className="border-b border-bg-grid px-4 py-3 whitespace-nowrap text-ink-soft">
                  {d.author}
                </td>
                <td className="border-b border-bg-grid px-4 py-3">
                  {correlatedIncident ? (
                    <span className="inline-flex items-center gap-1.5 rounded-full border border-amber/50 bg-amber/10 px-2.5 py-0.5 text-[11px] font-bold tracking-[0.08em] text-amber uppercase">
                      <span
                        aria-hidden="true"
                        className="h-1.5 w-1.5 rounded-full bg-amber"
                      />
                      {correlatedIncident}
                    </span>
                  ) : (
                    <span className="text-[11px] text-ink-faint">clean</span>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
