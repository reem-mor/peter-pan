# n8n — orchestration spine

`workflows/peter-pan-triage.json` is the versioned triage flow (v3):
**Webhook (header-auth) → Normalize Alert → Guardrails input → IF → Build
Story → Guardrails output → IF → Respond**. Four terminal responses: story
(200), `flagged_for_human_review` (200, output rail failed), `rejected`
(422, input rail failed), `error` (502, an upstream service call failed —
all three HTTP nodes carry an error branch).

`workflows/peter-pan-mesh-exercise.json` is the mesh contract exercise (v1):
**Webhook (header-auth) → Seed Alert → per service: healthz → main route →
IF shape check** across all five services (predictor `/predict`, rag
`/query`, guardrails `/check/input`, agent `/story`, ppos `/os/info`).
Three terminal responses: `mesh: ok` (200, with a per-service summary),
`contract_breach` (502, a response is missing a schema field), `unreachable`
(502, a service call failed). Endpoint → flow → assertion map:
[`COVERAGE.md`](COVERAGE.md).

**The gate is repo-level:** CI has no n8n instance, so
`tests/test_n8n_contracts.py` parses every export here and asserts the n8n
schema shape, env-templated URLs, the `peterpan.schemas` input/output
contracts, and the no-embedded-credentials rule on every push. Importing a
flow into the live instance is always a **manual step** (below).

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
  placeholder URLs only. Endpoints come from n8n environment variables —
  `PP_GUARDRAILS_BASE` (:8003) and `PP_AGENT_BASE` (:8004); guardrails and
  agent are separate services on separate ports, so one base URL cannot
  serve both — so one flow definition serves localhost, Docker, and EC2.
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

## Manual import (both flows — never automated)
1. `docker compose up -d` (services on 8001–8005).
2. Import the JSON into n8n (**inactive** — new flows always land inactive).
3. Set the base-URL env vars the flow uses (guardrails and agent are separate
   services on separate ports, so one base URL cannot serve both):
   - Triage: `PP_GUARDRAILS_BASE=http://host.docker.internal:8003`,
     `PP_AGENT_BASE=http://host.docker.internal:8004`.
   - Mesh exercise: those two **plus**
     `PP_PREDICTOR_BASE=http://host.docker.internal:8001`,
     `PP_RAG_BASE=http://host.docker.internal:8002`,
     `PP_PPOS_BASE=http://host.docker.internal:8005`.
4. Bind a Header Auth credential to the webhook node (both flows require it).
5. Run once with pinned test data in the editor before activating.

## Local test
- **Triage:** POST a fixture from `../data/synthetic/alerts.jsonl` to the
  webhook test URL with the auth header; expect an IncidentStory JSON back,
  `{rejected: true}` (422) for a rail-failing input,
  `{flagged_for_human_review: true}` when the output rail rejects, or
  `{error: true}` (502) when a service is down.
- **Mesh exercise:** POST `{}` to its webhook test URL with the auth header
  (the flow seeds its own deterministic alert); expect
  `{mesh: "ok", services: [...]}` with the prediction, guardrail verdict,
  and story confidence, or a 502 naming the failing stage
  (`contract_breach` / `unreachable`).
