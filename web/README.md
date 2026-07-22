# PETER PAN — web surfaces

## Canonical product UI (required)

| App | Path | Routes |
| --- | --- | --- |
| **Product** | `web/product` | Next.js App Router — `/` landing, `/app` incident workspace, `/os` PETER PAN OS |

```sh
npm ci
npm run dev -w web/product
```

Server-side BFF routes under `web/product/src/app/api/*` hold `PP_API_TOKEN` and
proxy to the five FastAPI services. Browser JavaScript never receives mesh
secrets.

Environment (server only):

```text
PP_PREDICTOR_BASE=http://127.0.0.1:8001
PP_RAG_BASE=http://127.0.0.1:8002
PP_GUARDRAILS_BASE=http://127.0.0.1:8003
PP_AGENT_BASE=http://127.0.0.1:8004
PP_PPOS_BASE=http://127.0.0.1:8005
PP_API_TOKEN=   # optional locally; required against hardened EC2
```

## Legacy Vite shells (migration sources — not the demo path)

| App | Path | Notes |
| --- | --- | --- |
| Landing | `web/landing` | Content source for `/` |
| Demo | `web/demo` | Incident SSE / graph — migrating into `/app` |
| Agent OS | `web/agent-os` | Token/budget console — migrating into `/os` |

## Streamlit

`ui/app.py` is an **optional internal development tool**. It is not the
canonical product UI and must not be presented as the main demo surface.
