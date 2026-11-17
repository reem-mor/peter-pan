# Testing and Evaluation

PETER PAN validates service contracts, agent execution, retrieval, policy guardrails, and local deployment. The default CI is fixture-based and does not require paid external LLM services.

## Reproduce locally

```bash
python -m venv .venv
source .venv/bin/activate
# Windows PowerShell: .\.venv\Scripts\Activate.ps1
python -m pip install -e ".[dev,llm,agents]"
ruff check .
ruff format --check .
mypy src
python -m pytest -q
```

## Deterministic evaluations

```bash
python evals/run_story_eval.py
python evals/run_retrieval_eval.py
python evals/run_feedback_eval.py
```

These scripts check story generation, lexical retrieval and feedback against configured fixture expectations. `evals/run_llm_judge.py` is an optional model-dependent evaluation; it is not part of the no-key CI guarantee. Passing fixtures is not evidence of measured production accuracy, live connector performance, or MTTR reduction.

## Docker smoke test

```bash
docker compose config --quiet
docker compose up --build -d
curl http://localhost:8004/healthz
curl http://localhost:8005/healthz
docker compose down -v
```

The CI workflow additionally exercises a structured story response and feedback persistence inside containers. See [the CI configuration](../.github/workflows/ci.yml) and [GitHub Actions runs](https://github.com/reem-mor/peter-pan/actions/workflows/ci.yml) for independent evidence.

## What CI verifies

| Job | Checks |
|---|---|
| `test` | Ruff lint/format, strict mypy, pytest with coverage and Compose configuration |
| `evals` | Deterministic story, retrieval, and feedback checks |
| `security` | Gitleaks secret scanning and pip-audit dependency scanning |
| `docker-smoke` | Container startup, health endpoints, incident story, and feedback |
| `web` (separate workflow) | Typechecking, linting, and building web workspaces |

**Coverage clarification:** Changed-line coverage has an 80% pull request gate; this is not an assertion of 80% overall repository coverage. Test counts change as the code evolves, so the current workflow run is the source of truth.

## Reviewing reliability controls

- See `tests/test_guardrails.py`, `tests/test_confidence_bounds.py`, and `tests/test_production_gate.py` for policy and safety tests.
- See `tests/test_langgraph_and_evals.py` and `tests/test_agent_and_actions.py` for graph, agent, and action semantics.
- See `tests/test_retrieval_eval.py` and `evals/` for retrieval and evaluation checks.
- See `tests/test_feedback_store.py` and `tests/test_feedback_endpoint.py` for feedback storage.

External model and cloud backends require their own configured credentials and should be assessed separately from synthetic CI. For the actual versus proposed architecture, see [ARCHITECTURE.md](ARCHITECTURE.md).
