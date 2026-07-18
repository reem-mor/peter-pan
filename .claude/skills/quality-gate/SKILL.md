---
name: quality-gate
description: >-
  Run PETER PAN's full pre-merge gate — tests, lint, format, types, eval
  harness, compose config, secrets scan — and report real results. Use before
  every commit/PR on this repo, after any dependency change, and whenever
  asked "is it green?".
---

# Quality gate

Run every step; report actual output per step, PASS/FAIL summary at the end.
Never report green without running. Stop at nothing — collect all failures
in one pass so they can be fixed together.

```powershell
.\.venv\Scripts\python -m pytest -q --cov=src/peterpan --cov-report=xml
.\.venv\Scripts\python -m ruff check .
.\.venv\Scripts\python -m ruff format --check .
.\.venv\Scripts\python -m mypy src
.\.venv\Scripts\python evals\run_story_eval.py
docker compose config --quiet
git fetch origin main
.\.venv\Scripts\python -m diff_cover.diff_cover_tool coverage.xml --compare-branch origin/main --fail-under=80
```

The last two lines are CI's changed-line coverage gate, verbatim — a plain
green `pytest -q` does NOT predict it (PR #46: local gate fully green, CI
failed at 60% on uncovered lazy-import client factories). Docs-only diffs
report "No lines with coverage information" and pass.

Secrets scan (last, always). Two hard rules learned the hard way:
scan only what git will actually ship (`git grep` over tracked files — the
gitignored `.env` legitimately contains keys and must not trip the gate),
and print **filenames only** (`-l`), never matched values (a scan that
echoes a key into a log/transcript is itself a leak vector):

```bash
git grep -lIE 'AKIA[0-9A-Z]{16}|sk-(ant|proj)-|pcsk_|ghp_[A-Za-z0-9]{30,}|AIza[0-9A-Za-z_-]{30,}|-----BEGIN .*PRIVATE KEY' \
  -- . ':(exclude).claude/skills/quality-gate/SKILL.md' \
  && echo "SECRETS IN TRACKED FILES — DO NOT PUSH" || echo "secrets: clean"
```

(The exclusion is this file itself — it contains the patterns as literal
text and would otherwise self-trip the gate.)

Optional (when services/Docker changed): `docker compose up -d`, curl every
`/healthz` (ports 8001–8005), `docker compose down`.

Container-asset check (when a service starts reading a NEW repo directory at
runtime): tests run from repo root and will NOT catch a missing image asset —
confirm the Dockerfile `COPY` list and compose env cover it (`ui/` was served
fine locally but absent from the image — LEARNINGS 2026-07-18):

```bash
git diff origin/main --name-only | cut -d/ -f1 | sort -u   # dirs touched
grep -n "^COPY" Dockerfile                                  # dirs shipped
```

## Report format
One line per step: `step — PASS/FAIL (real numbers: N tests, N files)`.
If anything fails: the failing output verbatim, then the fix plan — never
weaken a test, rail, or eval threshold to pass the gate.
