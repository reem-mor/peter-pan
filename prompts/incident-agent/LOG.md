# Prompt log — Surface 2: incident-agent synthesis

Format per docs/PROMPT-LOG-TEMPLATE.md. Test set: data/eval/story_cases.jsonl
via `evals/run_llm_judge.py` + the code-level invariant guards in
`peterpan.llm` (fabricated-citation allowlist, class-contradiction check,
confidence cap).

## v1 — baseline (`system-v1.txt`)
First attempt: principles + JSON contract, citation rule stated as "only use
sources from the provided evidence list."

**Observed failure (first live call, caught by the code guard, not by eye):**
model cited `grafana` — the alert's *origin system* — as an evidence source.
`LlmSynthesisError: fabricated citations rejected: ['grafana']`. The rule
named the right behavior but didn't define what counts as a source, so the
model treated any provenance-ish string as one.

## v2 — targeted fix (`system-v2.txt`, current)
Changes: (1) "source MUST be copied VERBATIM from the source values in the
provided evidence list", with the explicit counter-example ("not the alert's
origin system (e.g. grafana)"); (2) "copy probable_cause exactly from
deterministic_classification.incident_class" — same verbatim-copy pattern
applied preemptively to the class-contradiction guard.

**Result:** still rejected — same `grafana` citation. Reading the raw output
showed why: the model was citing *the alert itself* as evidence ("checkout
pod restarted twice in 10m" ← source grafana). That is correct analyst
behavior — the alert IS evidence — and no prompt wording was going to
suppress it reliably.

## v3 — fix the contract, not the model (code change, prompt unchanged)
The evidence payload now includes the alert as a first-class citable item
with source `alert:<origin>` (e.g. `alert:grafana`), and the allowlist
accepts it. The v2 verbatim-copy rule stands unchanged — the list the model
copies from simply became complete.

**Result:** live synthesis passes all guards; see judge output in the PR.
Lessons: (1) make constraints mechanical (copy-verbatim beats choose-wisely);
(2) when a capable model keeps "violating" a rule the same way, check whether
the rule is wrong before hammering the prompt — here the model understood
the domain better than the contract did.

## Judge run on v2+contract-v3 (10 cases, full LLM pipeline)
7/10 grounded. All 3 refutations are the same failure family: the model
describes weak retrieval matches (confidence 0.1-0.25) as established
patterns/precedents ("as a past incident showed...") instead of stating
their low relevance. v4 target: add "when citing evidence with confidence
below 0.3, you must qualify it as weak/possibly unrelated - never present
it as precedent."

## v4 — weak-evidence qualification (`system-v4.txt`, current)
Implements the v4 target: new principle — evidence items with confidence
below 0.3 MUST be qualified as weak/possibly unrelated in the summary,
"as a past incident showed" explicitly forbidden for them, and they may
not raise overall confidence. (No `system-v3.txt` exists: v3 was the
contract/code change above, prompt unchanged.)

**Judge run (10 cases, full LLM pipeline): 8/10 grounded.** The v3 failure
family is gone — zero weak-precedent refutations. The two remaining
refutations are a *different* family, both overconfidence-shaped:
- eval-03: availability impact stated as confirmed ("already confirmed by
  the alert - overconfidence").
- eval-07: inferential conclusion stated as fact ("pool is fully
  saturated...") + predictor's incident_class narrated as an established
  root cause + a precise confidence figure the judge deemed non-derivable.

Note: single judge run, judge is nondeterministic — treat 8/10 as the
recorded result, not a guarantee. v5 candidate target: separate "what the
evidence shows" from "what we infer" (mark inferences as hypotheses), and
mirror the honest-confidence rule with "never state impact as confirmed
unless an evidence item states it."
