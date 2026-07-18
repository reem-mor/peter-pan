# Frozen contracts — Phase 0

Source of truth for cross-workstream interfaces. Parallel workstreams build
against these; changing one is a deliberate contract change (PR must call it
out, `contract-reviewer` runs on it).

## 1. Typed schemas (`src/peterpan/schemas.py`)

`schemas.py` is the single source of truth. Every service request/response is
one of these models; the web surfaces consume the same shapes via
`packages/types` (TypeScript mirror — regenerate on schema change, never edit
to diverge).

Event models:

| Event | Model | Producer | Consumers |
|---|---|---|---|
| Alert ingest | `Alert` | n8n webhook / demo app | predictor, agent |
| Incident story | `IncidentStory` | agent (8004) | UI, demo app, agent-os |
| Deployment | `Deployment` | fixtures / GitHub (live path) | agent, "draw me the problem" |
| Action proposal | `ActionPreview` | agent | UI approval gate |
| Guardrail verdict | `GuardrailVerdict` | guardrails (8003) | agent, n8n rails |
| Feedback | `Feedback` | UI / agent-os | learning loop (keyed by `trace_id`) |

## 2. Service ports (unchanged)

predictor 8001 · rag 8002 · guardrails 8003 · agent 8004 · ppos 8005.
OpenAPI served by each FastAPI app at `/docs` / `/openapi.json`; contract
tests in `tests/` assert schema + status codes.

## 3. Vector-store schema (Pinecone — opt-in live backend)

Fixture-first invariant holds: lexical retrieval over `knowledge/` is the
default; `PP_RAG_BACKEND=pinecone` enables the semantic backend, falling back
to lexical on failure.

- **Embedding model:** `voyage-3.5-lite` (`PP_VOYAGE_MODEL`) — **1024 dims**.
  Index dimension must match; changing the model means a new index.
- **Index:** `peter-pan-knowledge` (`PP_PINECONE_INDEX`), cosine metric.
- **Namespaces:** `runbooks`, `past-incidents`, `memory` (operator-fed docs),
  `docs`. One domain per namespace; queries filter by namespace first.
- **Metadata per vector:** `doc_id`, `kind` (runbook | past_incident |
  document | memory), `title`, `source` (citation trail — never empty),
  `fed_at` (memory docs).
- **Ingestion:** batched upserts (100/batch), idempotent by `doc_id`
  (re-upsert overwrites), retry with exponential backoff on 5xx/429.
- **Retrieval:** dense + metadata filter (hybrid keyword ranking stays in the
  lexical backend; the two backends are compared by the retrieval eval, not
  merged).

## 4. Env keys (documented here; `.env.example` stays key-less)

| Key | Used by | Purpose |
|---|---|---|
| `PP_ENV` | all | mirage / staging / production behavior |
| `PP_LLM` | agent | `anthropic` enables LLM synthesis |
| `PP_RAG_BACKEND` | rag | `lexical` (default) / `pinecone` |
| `PINECONE_API_KEY`, `VOYAGE_API_KEY` | rag, memory | live retrieval |
| `PP_PINECONE_INDEX`, `PP_VOYAGE_MODEL` | rag | index + embedder |
| `PP_DAILY_BUDGET_USD` | ppos | budget guard |
| `PP_MESH` | ppos | healthz sweep targets |
| `PP_REDIS_URL` | services (WS11) | cache/queue (see ADR-0001) |
| `LANGFUSE_PUBLIC_KEY`, `LANGFUSE_SECRET_KEY`, `LANGFUSE_HOST` | observability (WS6) | tracing (opt-in; fixture path runs without) |
| `PP_PROMPT_LOG_PATH` | observability (WS6) | structured prompt/completion JSONL (hashes + scrubbed preview only) |
| `GRAPHIFY_API_KEY` | agent-os graph serve | MCP HTTP auth |

## 5. Streaming contract (demo app, WS9)

`GET /agent/stream?alert_id=…` — SSE. Event types: `step` (reasoning step,
`{"name", "detail", "ts"}`), `evidence` (an `Evidence` JSON), `story`
(final `IncidentStory` JSON), `done`. Deterministic fixture path emits the
same event sequence with synthetic timing — the demo never needs a live LLM.
