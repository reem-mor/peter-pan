/**
 * Synthetic post-mortems, bundled as fixtures in the exact content style of
 * knowledge/incidents/*.md (the RAG corpus). Copied here rather than
 * fetched so the page renders with zero backends (fixture-first).
 * All incidents are synthetic — no real systems or people.
 */

export interface PostMortem {
  id: string;
  title: string;
  date: string;
  severity: "P1" | "P2" | "P3" | "P4";
  durationMin: number;
  incidentClass: string;
  whatHappened: string;
  detection: string;
  resolution: string;
  lessons: string[];
}

export const FIXTURE_POSTMORTEMS: PostMortem[] = [
  {
    id: "INC-2456",
    title: "Internal DNS resolution failure after policy change",
    date: "2026-07-14",
    severity: "P1",
    durationMin: 23,
    incidentClass: "connectivity",
    whatHappened:
      "Services began failing with host-not-found errors between namespaces at 11:47, immediately after a network-policy change tightened egress rules. The change accidentally blocked UDP/53 to the in-cluster DNS resolver, so every new name lookup timed out while existing connections kept working — which made the blast radius look random until the pattern was clear. Checkout and search, which open fresh upstream connections per request, were hit hardest.",
    detection:
      "Connection-error alerts across multiple services (T+2m); the change-timeline flagged the network-policy deploy in the same window.",
    resolution:
      "Reverted the egress policy to restore UDP/53 to the resolver (T+20m); resolution recovered immediately and error rates cleared.",
    lessons: [
      "Distinguish refused (target down) from timeout (path/policy) first — the DNS runbook's step 1 saved triage time here.",
      "Network-policy changes now carry an explicit allow-rule for cluster DNS and a from-inside-the-namespace resolution smoke test in the deploy pipeline.",
      "Resolve-by-name from the affected namespace is the fastest confirming probe.",
    ],
  },
  {
    id: "INC-2412",
    title: "Expired TLS certificate on the payments gateway",
    date: "2026-06-22",
    severity: "P1",
    durationMin: 27,
    incidentClass: "availability",
    whatHappened:
      "The payments gateway started rejecting all inbound TLS handshakes at 02:00 with certificate-expired errors. The leaf certificate had a 90-day lifetime and the automated renewal job had silently failed nine days earlier when its ACME account key rotated — no alert fired on the failed renewal, so the expiry was the first visible symptom. Every downstream service calling the gateway saw connection failures, not slowness.",
    detection:
      "Synthetic-probe TLS handshake failure (T+1m); the certificate expiry monitor had a 7-day warning threshold that never fired because the metric exporter was scraping the wrong endpoint.",
    resolution:
      "Issued and deployed a fresh certificate manually (T+24m), then repaired the renewal job's account key.",
    lessons: [
      "Alert on renewal-job failure, not just on days-to-expiry — a broken renewer is the leading indicator.",
      "Certificate expiry monitoring must probe the live listener, not a config file.",
      "See the cert-rotation runbook; the manual re-issue path held up under pressure.",
    ],
  },
  {
    id: "INC-2401",
    title: "Checkout DB connection pool exhaustion",
    date: "2026-06-18",
    severity: "P1",
    durationMin: 34,
    incidentClass: "resource_exhaustion",
    whatHappened:
      "The checkout service began returning 503s at 09:14 as its database connection pool saturated at 100% utilization. A background reconciler deployed that morning opened a connection per order row and never released it on the error path, so a burst of retryable payment failures leaked the pool dry within minutes. Healthy request threads then blocked on connection-acquire timeouts and cascaded into upstream latency.",
    detection:
      "Pool-utilization alert (T+3m) and a connection-acquire timeout spike on the checkout dashboard.",
    resolution:
      "Rolled back the reconciler deploy and raised the pool ceiling temporarily (T+31m); utilization drained and 503s cleared within four minutes of rollback.",
    lessons: [
      "The leak lived on an error path with no test coverage — added a pool-usage assertion to the reconciler's integration suite.",
      "Connection-acquire timeouts now page before the pool hits 100%, not after.",
      "Reused the db-connection-pool runbook; the \"compare pool size to recent deploys\" step pointed straight at the culprit.",
    ],
  },
];
