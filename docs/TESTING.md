# Testing and Evaluation

PETER PAN uses a layered test strategy for services, contracts, workflows, guardrails, prompts, retrieval, and agent execution.

## Create the Virtual Environment

```bash
python -m venv .venv
```

Activate it on Linux or macOS:

```bash
source .venv/bin/activate
```

Activate it on Windows PowerShell:

```powershell
.\.venv\Scripts\Activate.ps1
```

## Install Development and UI Dependencies

```bash
python -m pip install --upgrade pip
pip install -e ".[dev,ui]"
```

## Run the Test Suite

```bash
python -m pytest -v
```

## Evaluation Infrastructure

The evaluation layer is organized around the following responsibilities:

- **`prompts/`** - Versioned system instructions and prompt templates, separated from application logic.
- **`data/`** - Recorded or synthetic historical incident fixtures used for deterministic tests.
- **`evals/`** - Ragas evaluations, prompt regressions, retrieval checks, and quality thresholds.
- **Agent graph validation** - Ensures tools are selected correctly and execution cannot enter infinite iterative states.
- **Contract validation** - Ensures all services exchange stable, schema-valid request and response objects.
- **Safety validation** - Confirms that mutation attempts, unsupported confidence values, uncited claims, and unsafe inputs are blocked.
