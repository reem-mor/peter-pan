import { DEMO_ALERTS } from "../lib/alerts";
import { SERVICE_DETAILS } from "../fixtures/topology";
import { SectionLabel } from "./ui";

/** Side panel for a selected graph node: synthetic owner, recent deploys
 * (typed Deployment fixtures), and related demo alerts. */
export function ServiceDetailPanel({
  serviceId,
  onClose,
}: {
  serviceId: string | null;
  onClose: () => void;
}) {
  const detail = serviceId === null ? null : (SERVICE_DETAILS[serviceId] ?? null);

  if (serviceId === null || detail === null) {
    return (
      <aside
        aria-label="Service details"
        className="border-t border-edge p-4 md:w-72 md:shrink-0 md:border-t-0 md:border-l"
      >
        <SectionLabel>Service details</SectionLabel>
        <p className="mt-2 font-mono text-xs text-faint">
          select a service node to inspect owner, deploys, and related alerts
        </p>
      </aside>
    );
  }

  const related = DEMO_ALERTS.filter((a) => detail.relatedAlerts.includes(a.id));

  return (
    <aside
      aria-label={`Details for service ${serviceId}`}
      className="overflow-y-auto border-t border-edge p-4 md:w-72 md:shrink-0 md:border-t-0 md:border-l"
    >
      <div className="flex items-center justify-between gap-2">
        <h3 className="font-mono text-[13px] font-bold text-ink">{serviceId}</h3>
        <button
          type="button"
          onClick={onClose}
          className="min-h-11 min-w-11 cursor-pointer rounded-lg border border-edge px-2 font-mono text-[11px] text-muted transition-colors duration-200 hover:border-edge-hi hover:text-ink focus-visible:ring-2 focus-visible:ring-s2 focus-visible:outline-none"
        >
          close
        </button>
      </div>

      <div className="mt-3">
        <SectionLabel>Owner</SectionLabel>
        <p className="mt-1 text-sm text-ink">{detail.owner.team}</p>
        <p className="font-mono text-[11px] text-faint">{detail.owner.oncall}</p>
      </div>

      <div className="mt-4">
        <SectionLabel>Recent deploys</SectionLabel>
        <ul className="mt-1.5 flex list-none flex-col gap-2">
          {detail.deploys.map((d) => (
            <li key={d.id} className="rounded-lg border border-edge bg-well p-2.5">
              <div className="flex items-baseline justify-between gap-2">
                <span className="font-mono text-xs font-semibold text-ink">{d.version}</span>
                <time
                  className="font-mono text-[10.5px] text-faint tabular-nums"
                  dateTime={d.deployed_at}
                >
                  {d.deployed_at.slice(0, 16).replace("T", " ")}
                </time>
              </div>
              <p className="mt-1 text-xs text-muted">{d.summary}</p>
              <p className="mt-1 font-mono text-[10.5px] text-faint">by {d.author}</p>
            </li>
          ))}
        </ul>
      </div>

      <div className="mt-4">
        <SectionLabel>Related alerts</SectionLabel>
        {related.length === 0 ? (
          <p className="mt-1 font-mono text-xs text-faint">none in the demo catalog</p>
        ) : (
          <ul className="mt-1.5 flex list-none flex-col gap-1.5">
            {related.map((a) => (
              <li key={a.id} className="flex items-baseline gap-2 text-xs">
                <span
                  className={`font-mono font-bold ${a.severity === "P1" ? "text-danger" : "text-ink"}`}
                >
                  {a.severity}
                </span>
                <span className="text-muted">{a.title}</span>
              </li>
            ))}
          </ul>
        )}
      </div>
    </aside>
  );
}
