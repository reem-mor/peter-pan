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
.\.venv\Scripts\python -m pytest -q
.\.venv\Scripts\python -m ruff check .
.\.venv\Scripts\python -m ruff format --check .
.\.venv\Scripts\python -m mypy src
.\.venv\Scripts\python evals\run_story_eval.py
docker compose config --quiet
```

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

## Report format
One line per step: `step — PASS/FAIL (real numbers: N tests, N files)`.
If anything fails: the failing output verbatim, then the fix plan — never
weaken a test, rail, or eval threshold to pass the gate.
