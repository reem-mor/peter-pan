---
name: learn
description: "Level 2 of the self-improving skills loop: capture a lesson. Use IMMEDIATELY whenever the user corrects you, a gate/CI run fails on something a rule could have caught, a bug survives review, or you discover a non-obvious repo/tool behavior the hard way. Appends one structured entry to .claude/learnings/LEARNINGS.md. Capture is cheap — when in doubt, log it."
---

# learn — capture a lesson (Level 2)

The loop: **L1 execute** (skills do work) → **L2 capture** (this) →
**L3 reflect** (`/reflect` distills) → **L4 evolve** (`/evolve` rewrites the
skills). A lesson that isn't written down is lost at context end.

## When to invoke (triggers, not vibes)

- User corrects your approach, output, or assumption
- Quality gate / CI fails for a reason a written rule could have prevented
- A bug ships past review, or verification catches what tests didn't
- A tool/library/repo behaves contrary to your expectation and costs time
- You repeat a mistake already logged (log again — repetition raises priority)

## What to do

Append ONE entry to `.claude/learnings/LEARNINGS.md` (create if missing).
Newest entries at the top, under the `## Raw` heading. Format:

```markdown
### YYYY-MM-DD · <kebab-slug>
- **Context:** what was being done (one line, concrete: file, command, PR)
- **Lesson:** what turned out to be true (one line, falsifiable)
- **Candidate rule:** the instruction that would have prevented it, phrased
  ready to paste into a skill/CLAUDE.md — or `none` if purely informational
- **Target:** which file should absorb it (peter-pan-design / quality-gate /
  CLAUDE.md / new-skill:<name> / none)
- **Status:** raw
```

## Rules

- One entry per lesson. No essays — 5 lines.
- Concrete over general: "FastAPI union return types need `response_model=None`"
  beats "be careful with FastAPI types".
- Synthetic/technical content only — never secrets, PII, or real incident data
  (repo golden rule 3).
- Do NOT edit skills here. Capture only. Distillation is `/reflect`'s job,
  application is `/evolve`'s job — separation keeps capture cheap and honest.
- Duplicate of an existing entry? Add `(repeat YYYY-MM-DD)` to the new entry
  instead of skipping — frequency is signal for `/reflect`.
