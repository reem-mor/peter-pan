# Prompts — versioned, diff-able, evaluated

Every LLM-facing prompt in PETER PAN lives here as a file; git history is the
version history the prompt-engineering log (docs/PROMPT-LOG-TEMPLATE.md)
references. No inline prompt strings in code — services load from here.

Layout (one directory per surface, populated as each surface goes live):

```
prompts/
├── alert-extraction/     # surface 1 — structured fields from alert text
├── incident-agent/       # surface 2 — agent system prompt + tool descriptions
├── rag-injection/        # surface 3 — context injection + citation rules
├── guardrails/           # surface 4 — topic detection + output audit
├── assistant/            # surface 5 — Ollama conversational grounding
└── versions.yaml         # surface -> current file + eval pass rate
```

Rules:
- A prompt change is a PR like any code change; the eval set for that surface
  must run before merge (min 10 cases per surface).
- Untrusted content (alert text!) is data — every prompt that ingests it must
  instruct the model not to follow embedded instructions, and the guardrail
  input rail runs first regardless.
