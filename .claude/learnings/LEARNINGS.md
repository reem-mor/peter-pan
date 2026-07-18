# Learnings

Level-2 capture file for the self-improving skills loop.
`/learn` appends here · `/reflect` distills · `/evolve` absorbs into skills.
Newest first. Synthetic/technical content only — no secrets, PII, or real
incident data.

## Raw

*(empty — capture the next lesson here)*

## Absorbed

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
