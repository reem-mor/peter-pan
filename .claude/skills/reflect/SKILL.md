---
name: reflect
description: "Level 3 of the self-improving skills loop: distill captured lessons into concrete skill-change proposals. Use when .claude/learnings/LEARNINGS.md has 3+ raw entries, at the end of a significant work session, or when the user asks to improve the workflow/skills. Read-only analysis — proposes diffs, applies nothing."
---

# reflect — distill lessons into proposals (Level 3)

Input: `.claude/learnings/LEARNINGS.md` (Raw section) + recent evidence
(`git log --oneline -20`, merged PR descriptions, gate failures this session).
Output: a **proposal list** the user (or `/evolve`) can act on. This skill
changes nothing except entry statuses.

## Procedure

1. Read every `Status: raw` entry. Cluster duplicates and near-duplicates —
   `(repeat …)` markers and same-target entries cluster together.
2. For each cluster decide ONE disposition:
   - **promote** — a rule change with a specific target file and exact wording.
     Frequency ≥2, or single occurrence with high cost, promotes.
   - **hold** — plausibly useful, insufficient evidence. Stays raw.
   - **drop** — one-off trivia, superseded, or already covered by an existing
     rule (cite which). Mark `Status: dropped`.
3. For every **promote**, emit a proposal block:

```markdown
#### Proposal N: <title>
- **Target:** <file path>
- **Change:** exact text to add/replace (diff-style, ready to apply)
- **Evidence:** learning entries + commits/PRs that justify it
- **Risk:** what could get worse if this rule is wrong
```

4. Update processed entries: `Status: raw` → `Status: distilled → proposal N`
   (or `dropped — <reason>`).
5. Present proposals. Stop. **Do not apply** — that is `/evolve`.

## Quality bar for proposals

- Rule must be **checkable** — a number, a command, an "if X then Y". "Be more
  careful" is not a rule; refuse to emit it.
- Rule must not weaken any product invariant, test, rail, or eval threshold
  (repo golden rule 1). If a lesson suggests loosening a gate, the proposal is
  to fix the underlying cause instead.
- Prefer editing an existing skill over creating a new one. New skill only
  when ≥3 lessons share a theme no existing skill owns.
- Every proposal names its evidence. No evidence, no proposal.
