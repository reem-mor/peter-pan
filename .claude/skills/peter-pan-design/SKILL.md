---
name: peter-pan-design
description: PETER PAN's private design system. Use before building or reviewing ANY UI in this repo — dashboards, Streamlit panels, HTML pages, charts, emails, decks. Defines the brand tokens, typography, component patterns, chart rules, and a numeric pre-delivery checklist. The canonical implementation is the web/agent-os React app.
---

# PETER PAN Design System

Dark ops-room aesthetic for an agentic incident-intelligence platform.
An APM console pointed at the LLM layer — technical, calm, evidence-first.
Design for the SRE at 3am: zero decoration that must be parsed, one accent
that always means "signal".

Per repo CLAUDE.md: public products (incident.io, resolve.ai, Grafana) are
pattern references only. Never copy screens, branding, copy, or icons —
PETER PAN has its own design system. This file **is** that system.

**Canonical implementation:** the `web/agent-os` React app — tokens live in
`web/agent-os/src/index.css` (mirrored in `web/demo/src/index.css`). When in
doubt, open it and match it. The token block below stays authoritative over
any implementation drift. Retiring a UI surface that a skill names as its
reference requires an /evolve follow-up in the same cycle (PR #47 lesson). Broader research-backed rules (responsive, a11y, performance,
forms): `~/.claude/skills/power-design/principles/web-principles.md` — the
20 web rules apply here wherever this file doesn't override them.

---

## 1. Tokens (copy verbatim — never invent new hex)

```css
:root {
  /* surfaces */
  --bg: #070b0e;          /* page — near-black, blue-green cast */
  --bg-grid: #0c1216;     /* inset wells, skeleton base */
  --panel: #0d141a;       /* cards */
  --panel-2: #101a21;     /* raised: row hover, chips */
  --border: #1b2831;      /* resting borders */
  --border-hi: #29414f;   /* hover/active borders */

  /* text */
  --text: #e6f1f3;        /* primary — never pure #fff (halation) */
  --muted: #7c93a3;       /* labels, hints */
  --faint: #6b8296;       /* axis ticks, footers ONLY — never body text; holds 4.5:1 on --bg */

  /* the one accent */
  --accent: #2fe6b0;      /* signal green: live, active, primary series */
  --accent-dim: rgba(47, 230, 176, 0.12);

  /* status */
  --warn: #fbbf24;        /* budget warn, demo mode */
  --danger: #f87171;      /* exceeded, unreachable, sev-1 */

  /* chart series order (after accent) */
  --s2: #4cc9f0; --s3: #b794f6; --s4: #60a5fa; --s5: #f472b6;

  /* type */
  --mono: 'JetBrains Mono', ui-monospace, Consolas, monospace;
  --sans: 'Inter', system-ui, 'Segoe UI', sans-serif;

  /* shape */
  --radius: 12px;         /* panels */
  --radius-ctl: 8px;      /* buttons, inputs */

  /* z-scale — only these */
  --z-header: 30; --z-tooltip: 50;
}
```

Hard rules:
- **One accent.** Green means signal/live/act. Warn and danger are status, not
  decoration. Accent coverage ≤10% of any view.
- **No shadows.** Dark-theme elevation = border + lighter surface
  (`--panel` → `--panel-2`, `--border` → `--border-hi`).
- **Dark-only product.** No light theme; don't half-build one.
- **Component CSS references tokens, never raw hex.** Charts may use the
  series hex directly inside generated SVG.

## 2. Typography

| Role | Spec |
|---|---|
| Wordmark / H1 | 17px mono 700, letter-spacing 0.06em |
| Section label | 11px mono 600, UPPERCASE, letter-spacing 0.18em, `--muted` |
| KPI value | 30px mono 700 (accent KPI gets `text-shadow: 0 0 18px rgba(47,230,176,.35)`) |
| Body | 16px sans, line-height ≥1.5 |
| Tables / meta | 13px mono, `font-variant-numeric: tabular-nums` |
| Micro (units, hints) | 11–12.5px mono, `--faint`/`--muted` |

- Numbers are **always mono + tabular-nums** — columns must not wiggle on refresh.
- Data/labels = mono; prose = sans. Never mix within one element.
- ALL-CAPS only at ≤12px label size with +0.12em tracking or more.

## 3. Component patterns (match `web/agent-os`)

- **Panel:** `--panel` bg, 1px `--border`, radius 12, padding 18. Hover →
  `--border-hi`. Titled by a section label with a 14px accent-colored SVG icon.
- **KPI tile:** label (section-label style) → value (30px mono) → hint
  (`--faint`, mono). One accent-glow KPI max per row — the headline number.
- **Badge/pill:** mono 11px uppercase, 999px radius, 1px border. Status dot
  7–8px with a matching glow (`box-shadow: 0 0 8px <color>`).
- **Status colors always pair with a second cue** (dot + word, icon + text) —
  never hue alone.
- **Segmented control** (time windows): joined buttons, active = accent bg +
  `--bg` text + 700 weight. Min target 44×36px.
- **Table:** th = section-label style at 10.5px; row hover = `--panel-2`;
  numeric columns right-aligned; inline bar = 4px accent `rowbar` for share
  columns. Wrap in `overflow-x: auto`.
- **Buttons/links:** `cursor: pointer`, `:hover` (color/border shift 150–300ms),
  `:focus-visible` 2px `--s2` ring. Never scale-on-hover (layout shift).
- **Empty / loading / error states designed for every data region.** Empty =
  quiet mono `--faint` line ("no usage in window"). Failure = amber DEMO badge +
  fixture data, never a blank page (fixture-first invariant applies to UI too).
- **Polled / refetching UI carries a sequence token.** Every fetch cycle takes
  `++state.seq`; a completed cycle renders only if its token is still current.
  Auto-refresh + user-switchable queries WILL interleave otherwise (stale 1H
  response once rendered over fresh 24H data — see LEARNINGS 2026-07-18).
- **Icons:** inline SVG (Lucide-style, 24 viewBox, stroke 2), 14–16px in
  labels. **No emoji icons.** Consistent set — don't mix families.

## 4. Charts (hand-rolled SVG; no chart libraries)

- Series order: `--accent` first, then `--s2…--s5`. Direct label or legend
  swatch + text for every series.
- Area fills: vertical gradient accent 0.35 → 0.02 opacity. Lines 2px,
  secondary series dashed 1.4px.
- Gridlines: `--border` dashed `3 5`; axis text 10px mono `--faint`.
- Donuts: stroke-dasharray segments, total value centered (20px mono 700).
- Keep zero/empty buckets — axes stay continuous; missing data must look
  missing, not absent.
- Every chart node gets `role="img"` + `aria-label`, or a table twin.
- Interactive charts respect `prefers-reduced-motion`.

## 5. Motion

- 150–300ms, `transition-colors`/opacity/transform only.
- Pulse/glow animations wrapped in `@media (prefers-reduced-motion: no-preference)`.
- Nothing flashes >3×/s. No parallax, no scroll-jacking — ops tool, not a promo.

## 6. Voice

- Tone: SRE runbook register. Precise, honest about uncertainty, no hype,
  no exclamation marks.
- Labels name the mechanism: "Daily budget guard · report-only · deterministic".
- Confidence shown < 1.0 always; every claim traceable to evidence (product
  invariant — the UI must surface citations, not hide them).

## 7. Pre-delivery checklist (numeric, non-negotiable)

- [ ] Tokens only — no new hex outside this file's palette
- [ ] Text contrast ≥4.5:1 — **computed** (WCAG relative luminance), never
      eyeballed; a new token pair ships with its measured ratio noted here.
      (`#4a5f6d` looked fine, measured 2.96:1 — LEARNINGS 2026-07-18.)
      Current floors: text/panel 16.1 · muted/panel 5.8 · faint/bg 4.95 ·
      faint/panel 4.65 · accent/bg 12.3 · warn/panel 11.1 · danger/panel 6.7
- [ ] One accent-glow element max per viewport; accent coverage ≤10%
- [ ] All numbers mono + tabular-nums; columns stable across refresh
- [ ] Status = color + second cue (dot/icon/word)
- [ ] `cursor: pointer` + hover + `:focus-visible` on every interactive element; targets ≥44px
- [ ] Empty, loading, and error/demo states designed for every data region
- [ ] No emoji icons; SVG set consistent
- [ ] `prefers-reduced-motion` respected; transitions 150–300ms
- [ ] Responsive 375 / 768 / 1024 / 1440 — no horizontal page scroll (tables scroll inside their own container)
- [ ] Wide content wrapped in `overflow-x: auto`
- [ ] Zero JS dependencies for repo HTML pages; charts hand-rolled SVG
- [ ] Fixture-first: page renders meaningfully with every backend down

## 8. When generating new surfaces

For decks or marketing-style pages about PETER PAN, invoke the
**power-design** skill and pick the `peter-pan` brand from its library
(`~/.claude/skills/power-design/brands/peter-pan/brand-style.md`) — it carries
these same tokens. For anything inside the product, this file wins.
