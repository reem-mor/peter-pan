/**
 * On-call — synthetic escalation chain and service ownership. Every name
 * is deliberately fake (synthetic-data invariant; surnames are test-infra
 * words on purpose).
 */

import { FIXTURE_ESCALATION, FIXTURE_OWNERS } from "../fixtures/oncall";
import { PageHeader } from "../components/PageHeader";
import { Panel } from "../components/Panel";

export function OnCall() {
  return (
    <div className="p-6">
      <PageHeader
        title="On-call"
        subtitle="Escalation chain and service ownership — synthetic roster, all names are fake by design."
      >
        <span className="rounded-full border border-edge px-3 py-1 font-mono text-[11px] tracking-[0.1em] text-ink-soft uppercase">
          synthetic roster
        </span>
      </PageHeader>

      <div className="grid grid-cols-1 gap-4 xl:grid-cols-[1fr_1.4fr]">
        <Panel title="Escalation chain" hint="who gets paged, in order">
          <ol className="flex flex-col gap-3">
            {FIXTURE_ESCALATION.map((step) => (
              <li
                key={step.level}
                className="flex items-center gap-4 rounded-[10px] border border-edge bg-bg-grid px-4 py-3"
              >
                <span
                  aria-hidden="true"
                  className="grid h-9 w-9 shrink-0 place-items-center rounded-full border border-accent/45 bg-accent-dim font-mono text-sm font-bold text-accent"
                >
                  L{step.level}
                </span>
                <div className="min-w-0">
                  <p className="truncate text-sm font-semibold text-ink">
                    {step.person}
                  </p>
                  <p className="font-mono text-[11.5px] text-ink-soft">
                    {step.role}
                  </p>
                </div>
                <div className="ml-auto text-right font-mono text-[11.5px] text-ink-faint">
                  <p>respond &lt; {step.respondWithin}</p>
                  <p className="uppercase">{step.channel}</p>
                </div>
              </li>
            ))}
          </ol>
        </Panel>

        <Panel title="Service owners" hint="team + primary + runbook">
          <div className="overflow-x-auto">
            <table className="w-full border-collapse font-mono text-[13px]">
              <caption className="sr-only">Service ownership</caption>
              <thead>
                <tr>
                  {["Service", "Team", "Primary", "Runbook"].map((h) => (
                    <th
                      key={h}
                      scope="col"
                      className="border-b border-edge px-3 py-2.5 text-left text-[10.5px] font-semibold tracking-[0.12em] text-ink-faint uppercase"
                    >
                      {h}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {FIXTURE_OWNERS.map((o) => (
                  <tr key={o.service} className="hover:bg-panel-2">
                    <td className="border-b border-bg-grid px-3 py-2.5 text-ink">
                      {o.service}
                    </td>
                    <td className="border-b border-bg-grid px-3 py-2.5 text-ink-soft">
                      {o.team}
                    </td>
                    <td className="border-b border-bg-grid px-3 py-2.5 text-ink-soft">
                      {o.primary}
                    </td>
                    <td className="border-b border-bg-grid px-3 py-2.5 text-[11.5px] text-cyan">
                      {o.runbook}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </Panel>
      </div>
    </div>
  );
}
