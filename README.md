# PETER PAN — Predictive, Agentic Navigator

During an incident the information already exists — it's just scattered:
metrics in Grafana, logs elsewhere, deploys elsewhere, runbooks in documents,
past incidents in separate systems. The engineer connects clues by hand,
under pressure. PETER PAN collects the evidence behind the scenes, connects
metrics ↔ logs ↔ deploys ↔ runbooks ↔ past incidents, and renders a **Dynamic
Incident Dashboard** that explains the story: what changed, the probable
cause, the evidence (always cited), the confidence, and the repair options.

**Risky actions are never executed automatically.** Every mutating action
becomes an **Action Preview** that requires explicit human approval — who
approved, and when, is recorded.

## Product invariants (enforced in code, tested)

1. **Citation trail** — every piece of evidence carries a `source`. No source, no claim.
2. **Action Preview gate** — HIGH-risk actions require named human approval; in
   `production` env, *all* mutating actions do.
3. **Deterministic floors override the LLM** — guardrail regexes and the
   predictor's severity floor have final say; a model may refine, never bypass.
4. **Never certainty** — an incident story's confidence is capped below 1.0.
5. **Bounded agents** — every agent loop has an explicit step budget.
6. **Every LLM call is metered** — `peterpan.usage.log_usage` feeds PETER PAN OS.

## Three environments

| Env | Purpose | Actions |
|---|---|---|
| `mirage` | Secure simulation — fixtures, demos, prompt iteration | stubs only |
| `staging` | Workflow validation — real wiring, synthetic data | allowed with previews |
| `production` | Live | read-only; every mutation needs approval |

Set via `PP_ENV` (see `.env.example`).

## Services

| Service | Port | Endpoints |
|---|---|---|
| predictor | 8001 | `/healthz`, `POST /predict` |
| rag | 8002 | `/healthz`, `POST /query` |
| guardrails | 8003 | `/healthz`, `POST /check/input`, `POST /check/output` |
| agent | 8004 | `/healthz`, `POST /story` |
| **PETER PAN OS** | 8005 | `/healthz`, `/os/usage`, `/os/agents`, `/os/tips` |

**PETER PAN OS** is the ops console for the AI system itself: token/cost per
agent, recent runs, and improvement tips (context-bloat detection, model-tier
routing suggestions).

## Quick start

```powershell
python -m venv .venv
.\.venv\Scripts\python -m pip install -e ".[dev,ui]"
.\.venv\Scripts\python -m pytest -q          # all tests
.\.venv\Scripts\python -m streamlit run ui/app.py   # WebUI
docker compose up --build                     # all five services
```

## Architecture (MVP → target)

The MVP is fixture-first: every service runs with zero external accounts, so
the demo path never depends on a live LLM. Each fixture sits behind the same
interface its production replacement implements:

| MVP (this repo) | Target |
|---|---|
| keyword floor in `predictor.py` | PyTorch classifier (floor stays as override) |
| lexical fixture corpus in `rag.py` | LangChain + vector store (Chroma/pgvector/Pinecone) + GGUF via Llama.cpp |
| regex rails in `guardrails.py` | NeMo Guardrails layered on top (floor keeps final say) |
| deterministic pipeline in `agent.py` | LangGraph planner → tools → synthesiser |
| in-process UI calls | n8n orchestration between WebUI and services |
| mermaid sketch in "Draw me the problem" | LLM-generated dynamic dashboard panels |

Deployment target: Docker on AWS EC2, n8n as the orchestration spine,
Ollama for the local conversational model. See `docs/`.

## Reference products

Positioning and UX patterns studied (adapt patterns, never copy):
[resolve.ai](https://resolve.ai) · [incident.io](https://incident.io) ·
[HolmesGPT](https://github.com/HolmesGPT/holmesgpt) (open-source — closest
technical relative) · [cytactic](https://cytactic.com). See
`docs/REFERENCES.md`.

## License

MIT
