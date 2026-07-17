# n8n — orchestration spine

`workflows/peter-pan-triage.json` is the versioned scaffold of the triage
flow: **Webhook → Guardrails input → IF → Build Story → Guardrails output →
Respond** (reject path responds with the guardrail reason).

## Live instance

Imported 2026-07-17 via the n8n MCP (SDK code path), **inactive** until the
services are reachable from n8n cloud:

- Workflow: `PETER PAN — Triage v2 (MVP services)` · id `Ibo84O4MC4w0ODYt`
- URL: https://reemmor.app.n8n.cloud/workflow/Ibo84O4MC4w0ODYt
- 10 nodes — adds a **Normalize Alert** step (webhook payload hygiene) and a
  third response path: output-rail failure → `flagged_for_human_review`.
- The three HTTP nodes carry placeholder URLs on purpose — fill them with the
  EC2 public host (or a tunnel to localhost) before activating. No
  credentials are stored in the flow.
- Before activating: run once with pinned test data in the n8n editor. Once
  a flow is live, prefer editing a duplicate and swapping, over experimenting
  on the flow that owns the production webhook URL.

## Conventions (PETER PAN's own rules, from the product invariants)

- **Git is the source of truth; the n8n instance is a deployment target.**
  Any change made in the n8n editor gets exported back into this directory
  in the same PR that approves it — an unexported live edit is drift.
- **No secret values ever leave n8n.** Exports carry credential *names* and
  placeholder URLs only. Endpoints come from n8n environment variables
  (`PP_SERVICES_BASE`-style), so one flow definition serves localhost,
  Docker, and EC2.
- **New flows land inactive.** Same idea as the ActionPreview gate: nothing
  goes live without a human explicitly activating it after a pinned-data
  test run in the editor.
- **The flow never bypasses the rails.** Guardrails input check is the first
  call after normalization; output check is the last before responding.
  Re-wiring around either is an invariant violation (see CLAUDE.md), not a
  flow optimization.
- **Fail visible, not silent.** Every branch terminates in an explicit
  response (story / flagged-for-review / rejected) — no path drops an alert
  without telling the caller what happened.

## Local test
1. `docker compose up -d` (services on 8001–8005).
2. Import the JSON into n8n (inactive), set `PP_SERVICES_BASE` to your host
   (e.g. `http://host.docker.internal`), map ports per service — or front the
   services with one gateway path.
3. POST a fixture from `../data/synthetic/alerts.jsonl` to the webhook test
   URL; expect an IncidentStory JSON back, or `{rejected: true}` for a
   guardrail-failing input.
