# PETER PAN — original design system (working notes)

Patterns researched from incident.io, resolve.ai, HolmesGPT, and cytactic
(see docs/REFERENCES.md) get translated here into PETER PAN's **own** design
language. Patterns in, originals out — no copied source, branding, copy,
icons, illustrations, or pixel-for-pixel screens.

## Principles

1. **The story is the interface.** The primary surface is a narrative
   (what changed → probable cause → evidence → options), not a wall of
   panels. Charts support the sentence, never replace it.
2. **Evidence is always one click from its source.** Every claim renders
   with its citation; clicking opens the runbook/incident/metric it came
   from. No orphan claims.
3. **Confidence is visible and honest.** Confidence renders as a bounded
   indicator (never 100%); low confidence changes the layout (hedged
   language, more prominent alternatives), not just a number.
4. **Approval is a first-class moment.** The Action Preview is designed like
   a code review, not a confirm dialog: what will run, blast radius, evidence
   for it, who approved last time.
5. **Calm under pressure.** Incident UIs are read at 3am: high contrast,
   no decorative motion, severity communicated by position and weight before
   color (colorblind-safe), `prefers-reduced-motion` respected.

## To research per pattern area (one file each as they're studied)

- information hierarchy · incident timelines · severity presentation ·
  alert grouping · investigation panels · evidence/citation presentation ·
  suggested actions · feedback capture · dynamic dashboard workflow
