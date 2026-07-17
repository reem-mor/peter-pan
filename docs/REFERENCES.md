# Reference products

Patterns studied for positioning and UX. Adapt patterns; never copy assets,
copy, or branding (see the `ui-sniping` guidance: patterns aren't copyright,
pixels and prose are).

| Product | What to learn from it | Where it shows up in PETER PAN |
|---|---|---|
| [resolve.ai](https://resolve.ai) | "AI production engineer" positioning; investigation that ends in a human-readable story, not a wall of signals | The IncidentStory schema — what changed / probable cause / evidence / confidence |
| [incident.io](https://incident.io) | Incident lifecycle UX, status pages, crisp severity language; strong opinionated defaults | Severity model (P1–P4), dashboard information hierarchy |
| [HolmesGPT](https://github.com/HolmesGPT/holmesgpt) | Open source, closest technical relative: toolset-based evidence collection, runbook grounding, K8s-native checks | Evidence `kind` taxonomy; tool-per-source design for the LangGraph agent — read their toolset abstractions before building ours |
| [cytactic](https://cytactic.com) | Crisis-management framing: preparedness + response as one product; roles and approval workflows | ActionPreview approval gate; the human-in-the-loop escalation framing |

## Differentiators to protect

1. **The story, not the signals** — the dashboard explains, it doesn't just aggregate.
2. **"Draw me the problem"** — on-demand, LLM-designed dashboard for the question the user actually asked.
3. **PETER PAN OS** — the AI system monitors itself (tokens, agents, quality) with the same seriousness it monitors production.
4. **Mirage** — a first-class simulation environment, not a demo hack: safe to show, safe to iterate prompts in.

## Related internal tooling

- [graphify](https://github.com/reem-mor/graphify) — turn the codebase +
  schemas + infra into a queryable knowledge graph. Planned integration:
  index this repo and the runbook corpus so the agent can answer
  "what talks to what" questions with a citation into the graph.
