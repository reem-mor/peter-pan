# Prompt Engineering Log — template

The prompt log is a graded deliverable (25%). One log per prompt surface,
five surfaces minimum, five iterations each. Prompts themselves live as
versioned files under `prompts/` — the log references them by path, never
pastes untracked prompt text.

## Surfaces (planned for PETER PAN)

| # | Surface | Where |
|---|---|---|
| 1 | Information extraction from alert text | n8n extractor node |
| 2 | Incident-agent system prompt + tool descriptions | LangGraph agent |
| 3 | RAG context injection + citation instructions | RAG service |
| 4 | Guardrail topic-detection + output-audit prompts | Guardrails service |
| 5 | Ollama conversational assistant grounding | WebUI sidebar |

## Per-surface log format

```markdown
# Surface N — <name>
Prompt file: prompts/<surface>.md   (git history = version history)
Test set: evaluation/prompts/<surface>_cases.jsonl (min 10 cases)

## v1 — baseline
What I wrote, without overthinking. Pass rate: X/10.

## v2..v3 — targeted iterations
Failure mode observed (one sentence) → change made → new pass rate →
regressions?

## v4..v5 — refinement
Same structure. By v5: what did I learn about how this model responds —
which phrasings work, what consistently fails?

## Final
Final prompt (link), justification per design decision, pass rate.
```

## Workflow tip

The `/critic-loop` skill automates the iterate-and-judge cycle: generate →
`critic` subagent scores against the test cases → revise. Use it per surface;
the log then documents what the loop found at each version.
