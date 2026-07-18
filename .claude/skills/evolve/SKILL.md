---
name: evolve
description: "Level 4 of the self-improving skills loop: apply approved /reflect proposals to the skill files themselves (peter-pan-design, quality-gate, learn/reflect/evolve, CLAUDE.md), then gate and ship the change like any other code. Use after /reflect has produced proposals and the user approved them (or standing auto-merge policy applies). The only skill allowed to edit skills."
---

# evolve — apply skill changes (Level 4)

Skills are law; this is the amendment process. Skill edits ship exactly like
code: branch → diff → gate → PR → merge. Never edit skills on main directly.

## Procedure

1. Take the approved proposal list from `/reflect` (same session or pasted).
   No proposals → stop; run `/reflect` first.
2. Branch: `evolve/<short-topic>`.
3. Apply each proposal's exact change to its target file. Keep each skill's
   existing voice and format; a rule lands in the section where a reader
   would look for it, not appended at the bottom.
4. In `LEARNINGS.md`, move the source entries from `Raw` to `## Absorbed`
   with `Status: absorbed → <target file> (PR #N)` once the PR number exists.
5. Run the full quality gate (`/quality-gate`). Skill files are prose, but the
   gate still proves the repo is green at the commit that changes the law.
6. Commit (conventional, `Co-Authored-By` trailer), push, open PR titled
   `evolve: <what rule changed>` with the proposals + evidence in the body.
7. Merge per the standing policy (auto-merge when green and non-invariant);
   otherwise leave for review.

## Hard limits (the constitution — not amendable by this loop)

- Never weaken: product invariants, tests, rails, eval thresholds,
  the secrets scan, or these hard limits themselves. A proposal that does so
  is rejected back to `/reflect` with the reason.
- Never grant any skill autonomy over: merging red PRs, production mutations,
  secret handling, or bypassing the Action Preview gate.
- Skill diffs stay small — one PR per coherent rule-set, ≤3 files touched
  (learnings file excluded from the count).
- Every absorbed rule keeps its evidence trail (learning entry stays in
  `Absorbed`, never deleted) — future sessions must be able to ask "why does
  this rule exist?"
