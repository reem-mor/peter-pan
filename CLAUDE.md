# CLAUDE.md — PETER PAN (MVP)

Working memory for Claude Code on this repo. Read before acting.

## What this is
PETER PAN — Predictive, Agentic Navigator. Incident intelligence: evidence
collection → explained incident story → human-approved remediation.
This repo is the production-style MVP: fixture-first, fully tested, zero
external accounts needed to run the demo path.

## Golden rules
1. **Product invariants are enforced in code and tests** (see README) —
   citation trail, ActionPreview gate, deterministic floors, bounded loops,
   confidence < 1.0, metered LLM calls. Never route around one to make a
   change pass; changing an invariant is a deliberate contract change.
2. **Fixture-first.** The demo path must never depend on a live LLM or an
   external API. Real backends slot in behind existing interfaces
   (`predict()`, `search()`, `check_*()`, `build_story()`).
3. **Synthetic data only.** No real incidents, PII, or secrets — in code,
   fixtures, commits, or logs.
4. **Env model is product behavior:** mirage/staging/production via `PP_ENV`.
   Production is read-only + approvals. Don't special-case around it.
5. **Every LLM call logs usage** via `peterpan.usage.log_usage` — PETER PAN OS
   is only as good as the metering.
6. Branch flow: feature branch → PR → merge on green CI.

## Commands
- Test: `python -m pytest -q`
- Lint: `ruff check . && ruff format --check .`
- Types: `mypy src`
- UI: `streamlit run ui/app.py`
- Full stack: `docker compose up --build`

## Definition of done (per change)
- Typed schemas for any new request/response; tests for the new behavior.
- `pytest -q`, `ruff`, `mypy src` all green.
- No secrets in the diff; `.env.example` stays key-less.
- Invariant-touching changes call it out explicitly in the PR description.
