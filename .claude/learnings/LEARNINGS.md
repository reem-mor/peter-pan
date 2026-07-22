# Learnings

Level-2 capture file for the self-improving skills loop.
`/learn` appends here · `/reflect` distills · `/evolve` absorbs into skills.
Newest first. Synthetic/technical content only — no secrets, PII, or real
incident data.

## Raw

### 2026-07-21 · checkout-ran-in-wrong-worktree-cwd-persistence
- **Context:** PR #51 first attempt — `git checkout -b feat/... origin/main` ran while Bash cwd was still C:\dev\peter-pan (persisted from earlier graphify queries), so MAIN worktree switched branches while edits+commit landed in the session worktree on a stale base (7c666de); push shipped an empty branch pointer and `gh pr create` said "No commits between".
- **Lesson:** Bash cwd persists across turns; a branch command without an explicit `cd <worktree> &&` prefix can run in whichever worktree was last visited — and `git log -1` printing the expected SHA does not prove WHICH worktree/branch moved.
- **Candidate rule:** Every branch-mutating git command starts with explicit `cd <intended-worktree> &&`, and is followed by `git branch --show-current` in the SAME command; treat a "[graphify] Branch switched" line from an unexpected path as a stop signal.
- **Target:** CLAUDE.md hard-won conventions
- **Status:** raw

## Absorbed

### 2026-07-18 · quality-gate-missing-diff-cover
- **Context:** PR #46 (SecretStr + lt=1.0 confidence): local quality-gate fully green, CI `test` job failed on `diff-cover --fail-under=80` — new `.get_secret_value()` lines in lazy optional-extra client factories (pinecone_store, dashboard._llm_spec) had 0% diff coverage.
- **Lesson:** The quality-gate skill runs plain `pytest -q` while CI additionally gates changed-line coverage; a green local gate does not predict the CI coverage verdict, especially for lazy-import paths no test imports.
- **Candidate rule:** Add to quality-gate SKILL.md: `pytest -q --cov=src/peterpan --cov-report=xml` then `git fetch origin main && diff-cover coverage.xml --compare-branch origin/main --fail-under=80` — same commands CI runs.
- **Target:** quality-gate skill (repo)
- **Status:** absorbed → quality-gate (PR #50)

### 2026-07-18 · design-skill-canonical-pointer-stale
- **Context:** PR #47 retired `ui/os_dashboard.html` (+ `/os/dashboard` route); `web/agent-os` is now the only operator console.
- **Lesson:** peter-pan-design SKILL.md names the deleted file as its "canonical implementation" — the design system's reference artifact must live somewhere that survives surface retirements.
- **Candidate rule:** Repoint SKILL.md canonical implementation to `web/agent-os` (tokens in `web/agent-os/src/index.css`) and state that retiring a UI surface requires an /evolve follow-up when a skill references it.
- **Target:** peter-pan-design skill (via /evolve)
- **Status:** absorbed → peter-pan-design (PR #49)

### 2026-07-18 · parallel-agents-verify-cross-file-imports-after-merge
- **Context:** Three fixer agents + orchestrator edited src/ concurrently (no worktrees); an import added to llm.py/dashboard.py for the new usage.model_rates was missing after the agents converged — caught by a fixer's full-repo mypy run, not by any single agent's scoped check.
- **Lesson:** Scoped per-agent gates all pass while the combined tree is broken; cross-file imports are the seam parallel edits break at.
- **Candidate rule:** After parallel agents finish on a shared tree, run the FULL gate (pytest + mypy on everything) before commit — never trust the union of scoped green runs; for wider overlaps use worktree isolation.
- **Target:** CLAUDE.md
- **Status:** absorbed → CLAUDE.md hard-won conventions (evolve/parallel-agents-gate)

*(rules that graduated into skills — entry kept as the evidence trail)*

### 2026-07-18 · check-pr-head-before-stacking-commits
- **Context:** Pushed follow-up commits to `feat/os-dashboard` while PR #27 was open; Re'em had already merged it, so the commits landed on a merged branch and needed a follow-up PR (#28).
- **Lesson:** A PR's head can be merged by the human at any moment; pushed commits after merge silently miss main.
- **Candidate rule:** Before pushing additional commits to a PR branch, check `gh pr view <n> --json state` — if MERGED, branch fresh from main and open a new PR.
- **Target:** CLAUDE.md
- **Status:** absorbed → CLAUDE.md (founding PR)

### 2026-07-18 · dark-theme-muted-colors-fail-wcag-silently
- **Context:** `--faint #4a5f6d` on `#070b0e` looked fine but measured 2.96:1 — below the 4.5:1 floor; shipped in PR #27, fixed in PR #29.
- **Lesson:** Eyeballed low-emphasis colors on dark backgrounds routinely fail WCAG; perceived legibility on a bright dev monitor is not evidence.
- **Candidate rule:** Any new color token pair must have its contrast ratio computed (WCAG relative luminance) before shipping; record the ratio in the design skill.
- **Target:** peter-pan-design
- **Status:** absorbed → peter-pan-design (founding PR)

### 2026-07-18 · polling-ui-needs-stale-response-guard
- **Context:** Dashboard 30s poll raced the time-window switch: a stale 1H response rendered over fresh 24H data (empty KPIs while budget bar showed spend).
- **Lesson:** Any auto-refreshing UI with user-switchable queries will interleave responses; last-write-wins renders stale state.
- **Candidate rule:** Every polled fetch cycle carries a sequence token; a completed cycle renders only if its token is still current.
- **Target:** peter-pan-design
- **Status:** absorbed → peter-pan-design (founding PR)

### 2026-07-18 · fastapi-union-response-needs-response-model-none
- **Context:** `/os/dashboard` returning `HTMLResponse | JSONResponse` crashed app import: "Invalid args for response field".
- **Lesson:** FastAPI cannot build a response model from a Response-class union; the whole test collection fails, not just the route.
- **Candidate rule:** Routes returning Response subclasses (or unions of them) declare `response_model=None` in the decorator.
- **Target:** CLAUDE.md
- **Status:** absorbed → CLAUDE.md (founding PR)

### 2026-07-18 · dockerfile-assets-must-track-new-runtime-dirs
- **Context:** `/os/dashboard` served fine locally but would 404 in-container — Dockerfile never copied `ui/`; caught in production-polish pass, not by tests.
- **Lesson:** Tests run from repo root and mask missing COPY lines; every new runtime-read directory is a silent container regression.
- **Candidate rule:** When a service starts reading a new repo directory at runtime, the same PR must update the Dockerfile COPY list and compose env (e.g. PP_MESH-style wiring).
- **Target:** quality-gate
- **Status:** absorbed → quality-gate (founding PR)

## Dropped

### 2026-07-18 · verify-ui-numerically-when-screenshots-flake
- **Context:** Browser-pane screenshot capture hung after design fixes; JS execution still worked, so contrast ratios, target sizes, and ARIA states were verified via in-page script.
- **Lesson:** Visual verification has a numeric fallback that is often stronger than the screenshot it replaces.
- **Candidate rule:** none
- **Target:** none
- **Status:** dropped — informational, no checkable rule
