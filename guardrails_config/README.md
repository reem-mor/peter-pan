# guardrails_config/

NeMo Guardrails configuration for the additive screening layer described in
`src/peterpan/nemo_rails.py` and wired into
`src/peterpan/services/guardrails.py`. **The deterministic regex floor in
`services/guardrails.py` always wins** — this config can only turn a floor
*pass* into a flagged *fail*; it is never consulted once the floor has
already failed, and it can never turn a floor fail into a pass.

Enable with `PP_GUARDRAILS=nemo`. Default (`PP_GUARDRAILS=regex`, i.e. the
`nemo` extra not installed and this whole layer never imported) is
unchanged from before this layer existed — zero new required dependencies,
zero behavior change.

## Layout

| File | Purpose |
| --- | --- |
| `config.yml` | Rails config. `models: []` — deliberate, see below. |
| `actions.py` | NeMo action bindings, auto-discovered by `LLMRails`. Thin wrappers around the pure detection functions in `src/peterpan/nemo_rails.py` — no detection logic lives here. |
| `rails/input.co` | Prompt-injection/jailbreak + topical-drift input rails. |
| `rails/output.co` | Fabricated-citation + secret-leakage output rails. |
| `rails/topical.co` | Optional LLM-backed semantic topical rail. **Not** referenced by `config.yml` — see below. |

## Deterministic vs LLM-backed rails

| Rail | Flow | Backing | Default state |
| --- | --- | --- | --- |
| Prompt injection / jailbreak | `check prompt injection` (`rails/input.co`) | Pattern match (`peterpan.nemo_rails.detect_injection`) | **ON** when `PP_GUARDRAILS=nemo` |
| Topical drift (heuristic) | `check topical drift` (`rails/input.co`) | Pattern match (`detect_topical_drift`) | **ON** when `PP_GUARDRAILS=nemo` |
| Fabricated citation | `check fabricated citation` (`rails/output.co`) | Pattern match against known citation shapes (`detect_fabricated_citation`) | **ON** when `PP_GUARDRAILS=nemo` |
| Secret leakage | `check secret leakage` (`rails/output.co`) | Pattern match (`detect_secret_leak`) | **ON** when `PP_GUARDRAILS=nemo` |
| Topical drift (semantic) | `check topical drift semantic` (`rails/topical.co`) | **LLM call** (Anthropic, via `peterpan.nemo_rails.topical_llm_check`) | **OFF always**, even with `PP_GUARDRAILS=nemo` |

All four pattern-based rails run through NeMo's colang runtime with
`models: []` in `config.yml` — no LLM is configured or called to run them.
That is what keeps `PP_GUARDRAILS=nemo` on the fixture-first demo path: it
adds a config-driven rails engine, not a dependency on a live model.

The one rail that *can* call an LLM (`rails/topical.co`) is intentionally
left out of `config.yml`'s `rails:` list, so `LLMRails` never activates it.
`src/peterpan/nemo_rails.py:_build_rails` only splices
`"check topical drift semantic"` into the active input flows when
`Settings.nemo_topical_llm` is `True` — which also requires `PP_LLM=anthropic`
and a live `ANTHROPIC_API_KEY`. Every call to it logs usage via
`peterpan.usage.log_usage` (service `guardrails`, agent `nemo-topical-rail`),
the same metering contract as `peterpan.llm.synthesize`. It is never
exercised on the fixture/CI path.

## Floor-always-wins semantics

`services/guardrails.py:check_input_full` / `check_output_full`:

1. Run the regex floor (`check_input`/`check_output`). If it fails, return
   that verdict immediately — NeMo is never consulted.
2. If `PP_GUARDRAILS` isn't `nemo`, return the floor's pass as-is.
3. Otherwise run the NeMo scan. If NeMo raises (`NemoCheckError` — package
   missing, config error, runtime failure, ...), fall back to the floor's
   pass; the additive layer breaking must never break availability.
4. If NeMo flags anything, return a `GuardrailVerdict(passed=False, ...)`
   with each flag prefixed `nemo:` so the origin is always visible.

## Editing these files

These are versioned, diffable config — same expectations as any other
product config in this repo: change deliberately, and cover the change with
a test in `tests/test_guardrails.py` / `tests/test_nemo_rails.py`.
