## What

<!-- One paragraph: what changed and why. -->

## Invariants check

- [ ] No product invariant weakened (citation trail, ActionPreview gate,
      deterministic floors, bounded loops, confidence < 1.0, metered usage)
- [ ] Fixture-first: demo path still runs with zero external accounts
- [ ] No secrets in the diff; `.env.example` still key-less
- [ ] Contract changes (schemas.py / endpoint shapes) called out explicitly

## Evidence

<!-- Paste the real gate output: pytest / ruff / mypy. "It should pass" doesn't count. -->

```
pytest:
ruff:
mypy:
```
