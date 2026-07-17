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
- Before activating: run once with pinned test data in the n8n editor; never
  `test_workflow` on it after activation (deregisters the live webhook).

## Conventions (hard rules)
- Exports here carry **credential names only, never values**; `PP_SERVICES_BASE`
  comes from n8n environment variables, so the same flow runs against
  localhost, Docker, or EC2.
- Never run `test_workflow` against a live webhook-triggered flow — it
  deregisters the production webhook. Import as **inactive**, test with
  pinned data, then activate.
- Modify live flows via the n8n MCP `update_workflow` operations path;
  re-export every approved change back to this file (git is the source of
  truth, the n8n instance is a deployment target).

## Local test
1. `docker compose up -d` (services on 8001–8005).
2. Import the JSON into n8n (inactive), set `PP_SERVICES_BASE` to your host
   (e.g. `http://host.docker.internal`), map ports per service — or front the
   services with one gateway path.
3. POST a fixture from `../data/synthetic/alerts.jsonl` to the webhook test
   URL; expect an IncidentStory JSON back, or `{rejected: true}` for a
   guardrail-failing input.
