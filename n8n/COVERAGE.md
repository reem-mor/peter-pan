# n8n endpoint coverage — mesh contract map

Every HTTP-reachable endpoint across the five services, the n8n flow that
exercises it, and where its contract is asserted. Two assertion layers:

- **Flow-level** — IF nodes inside the workflow check schema fields on the
  live response (runs when the flow runs).
- **Repo-level** — `tests/test_n8n_contracts.py` parses the workflow JSON and
  asserts it against `peterpan.schemas` and the live FastAPI route tables
  (runs in CI on every push; the real gate, since CI has no n8n).

Flows: **Triage** = `workflows/peter-pan-triage.json` ·
**Mesh** = `workflows/peter-pan-mesh-exercise.json`

## predictor (:8001 · `PP_PREDICTOR_BASE`)

| Endpoint | Flow | Contract assertion |
| --- | --- | --- |
| `GET /healthz` | Mesh (`Predictor Healthz`) | Reachability gate; error branch → 502 `Respond Unreachable` |
| `POST /predict` | Mesh (`Predict`) | IF `Prediction Shape?`: `incident_class` + `severity` present, `confidence < 1.0` |

## rag (:8002 · `PP_RAG_BASE`)

| Endpoint | Flow | Contract assertion |
| --- | --- | --- |
| `GET /healthz` | Mesh (`Rag Healthz`) | Reachability gate; error branch → 502 |
| `POST /query` | Mesh (`Rag Query`) | IF `RagResult Shape?`: `query`, `matches[]`, `insight` present |
| `POST /memory` | — not covered (deliberate) | Mutating knowledge-base write; feeding synthetic incidents from an exercise flow would pollute the corpus. Covered by `tests/test_memory_feed.py`. |

## guardrails (:8003 · `PP_GUARDRAILS_BASE`)

| Endpoint | Flow | Contract assertion |
| --- | --- | --- |
| `GET /healthz` | Mesh (`Guardrails Healthz`) | Reachability gate; error branch → 502 |
| `POST /check/input` | Triage (`Guardrails Input`) + Mesh (`Guardrails Check`) | Triage: IF `Input Passed?` gates the pipeline (rails-first). Mesh: IF `Verdict Shape?`: `passed == true` for the ops fixture, `flags[]` present |
| `POST /check/output` | Triage (`Guardrails Output`) | IF `Output Passed?`; false → `flagged_for_human_review` response (fail-visible) |

## agent (:8004 · `PP_AGENT_BASE`)

| Endpoint | Flow | Contract assertion |
| --- | --- | --- |
| `GET /healthz` | Mesh (`Agent Healthz`) | Reachability gate; error branch → 502 |
| `POST /story` | Triage (`Build Story`) + Mesh (`Agent Story`) | Triage: response echoed verbatim as the webhook's 200 body (IncidentStory in = IncidentStory out; repo-level test posts the Normalize-Alert shape and validates with `IncidentStory.model_validate`). Mesh: IF `Story Shape?`: `probable_cause`, non-empty `evidence[]` (citation trail), `repair_options[]`, `confidence < 1.0` |
| `POST /dashboard` | — not covered (deliberate) | Superset of `/story` (story pipeline + `DashboardSpec` render); exercising it from n8n would double every story-path failure mode for one extra field. Covered by `tests/test_dashboard.py`. |
| `GET /agent/stream` | — not covered (deliberate) | SSE; n8n's HTTP Request node buffers the body, so it cannot assert frame-by-frame contract. Covered by `tests/test_agent_stream.py`. |

## ppos (:8005 · `PP_PPOS_BASE`)

| Endpoint | Flow | Contract assertion |
| --- | --- | --- |
| `GET /healthz` | Mesh (`Ppos Healthz`) | Reachability gate; error branch → 502 |
| `GET /os/info` | Mesh (`Ppos Info`) | IF `Info Shape?`: `service`, `env` present, `daily_budget_usd > 0` |
| `GET /os/usage` | — not covered (deliberate) | Read-only console aggregates; shape depends on log contents, so a flow-level field assertion would be flaky-by-design. Covered by `tests/test_ppos_usage.py`. |
| `GET /os/usage/series` | — not covered (deliberate) | Same as `/os/usage`. Covered by `tests/test_ppos_dashboard.py`. |
| `GET /os/budget` | — not covered (deliberate) | Same family. Covered by `tests/test_ppos_budget.py`. |
| `GET /os/tips` | — not covered (deliberate) | Same family. Covered by `tests/test_ppos_usage.py`. |
| `GET /os/agents` | — not covered (deliberate) | Static roster. Covered by `tests/test_ppos_usage.py`. |
| `GET /os/services` | — not covered (deliberate) | Server-side health sweep — the Mesh flow *is* the n8n-side equivalent; probing the prober adds no signal. |

## Repo-level assertions (`tests/test_n8n_contracts.py`)

Applied to **every** workflow JSON in `workflows/`:

1. Valid n8n shape — `nodes` + `connections`, unique node names, every
   connection endpoint references an existing node.
2. Every HTTP node URL is env-templated (`={{ $env.PP_*_BASE }}/path`) — no
   hardcoded IPs, hosts, or ports (one flow definition serves localhost,
   Docker, and EC2).
3. Every templated URL's path exists on the FastAPI app the env var points
   at, with a matching method (flow ↔ route table cross-check).
4. Webhook input/output contract — the triage Normalize Alert node emits
   exactly Alert-schema fields (all required ones included), and the payload
   it builds round-trips through `POST /story` into a valid `IncidentStory`.
5. No credentials embedded — no `credentials` blocks, no secret-shaped
   strings anywhere in the export.
6. Fail-visible — every terminal node is a Respond node; webhook nodes
   require header auth; HTTP nodes carry an error branch.
