"""NeMo Guardrails layer — additive screening behind the regex floor.

`peterpan.services.guardrails` owns the deterministic floor and ALWAYS wins:
a floor fail is final regardless of what NeMo says, and NeMo is never even
consulted once the floor has already failed. When the floor passes, this
module may run NeMo Guardrails on top and turn that pass into a fail (never
the other way around) — see `check_input_full`/`check_output_full` in
`services/guardrails.py`.

Two layers of detection, deliberately kept separable and independently
testable:

- `detect_*` functions below are pure regex, no `nemoguardrails` import.
  They ARE the deterministic rails' logic and are unit-tested directly,
  with no optional dependency required.
- `_build_rails`/`scan_input`/`scan_output` wire those same functions into
  an actual NeMo Guardrails `LLMRails` engine (config in guardrails_config/,
  actions in guardrails_config/actions.py) so the rails really run through
  NeMo's colang runtime, config-driven and diff-able. `nemoguardrails` is a
  lazy import behind the `nemo` extra — importing this module never requires
  it, and PP_GUARDRAILS=nemo is the only thing that triggers the import.

`topical_llm_check` is the one LLM-backed rail. It is OFF by default (see
`Settings.nemo_topical_llm`) — the fixture/demo path never depends on a live
LLM — and every call logs usage via `peterpan.usage.log_usage`, same as
`peterpan.llm.synthesize`.
"""

from __future__ import annotations

import asyncio
import re
from pathlib import Path
from typing import Any

from peterpan.config import Settings
from peterpan.usage import log_usage, make_event, model_rates

_CONFIG_DIR = Path(__file__).parent.parent.parent / "guardrails_config"


class NemoCheckError(Exception):
    """Any NeMo-path failure. Callers must catch this and fall back to the
    floor's own verdict — the additive layer breaking must never break
    availability of the base (already-passed) floor result."""


# --- deterministic detectors (pure regex, no nemoguardrails import) --------

# A broader family of injection/jailbreak phrasing than the regex floor's 3
# patterns — NeMo is additive screening, so it is expected to catch more,
# not re-check the same ground.
_INJECTION_PATTERNS: list[str] = [
    r"(?i)ignore (all |any )?(previous|prior|above|earlier) "
    r"(instructions|rules|prompts?|directives?)",
    r"(?i)disregard (all |any )?(previous|prior|above|your) "
    r"(instructions|rules|guidelines|directives?)",
    r"(?i)forget (all |any )?(previous|prior|your) (instructions|rules|training)",
    r"(?i)you are now (in )?(DAN|developer mode|unrestricted|jailbroken)",
    r"(?i)pretend (you are|to be) (an? )?(unfiltered|unrestricted|different)",
    r"(?i)reveal (your )?(system prompt|hidden instructions|internal rules)",
    r"(?i)bypass (your |all )?(safety|guardrails?|restrictions|instructions)",
    r"(?i)act as (an? )?(unrestricted|jailbroken|dan)\b",
    r"(?i)new instructions?\s*:",
    r"(?i)override (your |all )?(previous )?(instructions|configuration|rules)",
]

# Heuristic "stay on the incident domain" markers — content that is clearly
# trying to hijack the topic rather than describe an ops signal.
_TOPICAL_DRIFT_PATTERNS: list[str] = [
    r"(?i)write (me |us )?(a |an )?(poem|song|story|essay|joke)",
    r"(?i)tell me a joke",
    r"(?i)what('?s| is) the capital of",
    r"(?i)recipe for",
    r"(?i)translate (this|the following) (to|into)",
    r"(?i)as an ai language model",
]

# Citation shapes actually used elsewhere in this repo (Evidence.source /
# services/rag.py). A citation claim that looks reference-like but doesn't
# start with one of these is treated as a fabrication tell.
_KNOWN_SOURCE_PREFIXES: tuple[str, ...] = (
    "alert:",
    "predictor:/predict",
    "knowledge/",
    "kb:",
)
_CITATION_CLAIM_RE = re.compile(
    r"(?i)\b(?:source|per|according to|citing|as (?:documented|noted) in)\s*:?\s*"
    r"([\"']?)([A-Za-z][\w\-./:#]*(?:\s[A-Za-z0-9][\w\-./:#]*){0,6})\1"
)
_CITATION_LOOKS_FABRICATED_RE = re.compile(
    r"(?i)(https?://|doc(ument)?ation|runbook|wiki|postmortem|rfc|confluence|ticket|kb-?\d|#\d)"
)

_SECRET_PATTERNS: list[str] = [
    r"AKIA[0-9A-Z]{16}",  # AWS access key id
    r"-----BEGIN (RSA |EC |OPENSSH )?PRIVATE KEY-----",
    r"(?i)\bsk-[a-zA-Z0-9]{20,}\b",  # OpenAI/Anthropic-shaped secret key
    r"(?i)\b(api[_-]?key|secret|password|token)\s*[:=]\s*['\"]?[A-Za-z0-9/_+\-]{12,}",
]


def detect_injection(text: str) -> bool:
    return any(re.search(p, text) for p in _INJECTION_PATTERNS)


def detect_topical_drift(text: str) -> bool:
    return any(re.search(p, text) for p in _TOPICAL_DRIFT_PATTERNS)


def detect_fabricated_citation(text: str) -> bool:
    for match in _CITATION_CLAIM_RE.finditer(text):
        claim = match.group(2).strip()
        if not claim:
            continue
        if any(claim.lower().startswith(prefix) for prefix in _KNOWN_SOURCE_PREFIXES):
            continue  # matches a real citation shape used by this system
        if _CITATION_LOOKS_FABRICATED_RE.search(claim):
            return True
    return False


def detect_secret_leak(text: str) -> bool:
    return any(re.search(p, text) for p in _SECRET_PATTERNS)


# --- LLM-backed topical rail: OFF by default, metered when used -----------

_TOPICAL_LLM_PROMPT = (
    "You are a strict topical-scope classifier for an incident-response system. "
    "Reply with exactly one word: INSCOPE if the text concerns a software/infra "
    "operational incident, alert, or its remediation; OFFTOPIC otherwise.\n\nText:\n{text}"
)


def topical_llm_check(text: str, settings: Settings) -> bool:
    """Semantic topical check via the configured LLM. OFF by default — only
    called at all when `Settings.nemo_topical_llm` is True (see
    guardrails_config/rails/topical.co and _build_rails below). Every call
    logs usage via peterpan.usage.log_usage, mirroring peterpan.llm.synthesize.
    """
    if not settings.nemo_topical_llm:
        return False
    if not settings.anthropic_api_key:
        raise NemoCheckError("nemo_topical_llm enabled but no ANTHROPIC_API_KEY configured")

    try:
        import anthropic  # lazy: optional `llm` extra (shared with peterpan.llm)
    except ImportError as exc:
        raise NemoCheckError("anthropic SDK not installed (pip install -e '.[llm]')") from exc

    try:
        client = anthropic.Anthropic(api_key=settings.anthropic_api_key.get_secret_value())
        response = client.messages.create(
            model=settings.anthropic_model,
            max_tokens=8,
            messages=[{"role": "user", "content": _TOPICAL_LLM_PROMPT.format(text=text)}],
        )
    except Exception as exc:
        raise NemoCheckError(f"anthropic API failure: {type(exc).__name__}") from exc

    log_usage(
        make_event(
            service="guardrails",
            agent="nemo-topical-rail",
            model=settings.anthropic_model,
            input_tokens=response.usage.input_tokens,
            output_tokens=response.usage.output_tokens,
            cost_usd=round(
                response.usage.input_tokens * model_rates(settings.anthropic_model)[0]
                + response.usage.output_tokens * model_rates(settings.anthropic_model)[1],
                6,
            ),
        ),
        settings.usage_log_path,
    )

    verdict = "".join(b.text for b in response.content if b.type == "text").strip().upper()
    return verdict.startswith("OFFTOPIC")


# --- NeMo engine wiring (lazy import; only reached for PP_GUARDRAILS=nemo) -

_INPUT_RAIL_FLAGS: dict[str, str] = {
    "check prompt injection": "prompt_injection",
    "check topical drift": "topical_drift",
    "check topical drift semantic": "topical_drift_llm",
}
_OUTPUT_RAIL_FLAGS: dict[str, str] = {
    "check fabricated citation": "fabricated_citation",
    "check secret leakage": "secret_leakage",
}


def _build_rails(settings: Settings) -> Any:
    """Load guardrails_config/ into an LLMRails engine. Raises NemoCheckError
    on any failure (package missing, config broken, ...)."""
    try:
        from nemoguardrails import LLMRails, RailsConfig
    except ImportError as exc:
        raise NemoCheckError("nemoguardrails not installed (pip install -e '.[nemo]')") from exc

    try:
        config = RailsConfig.from_path(str(_CONFIG_DIR))
        if settings.nemo_topical_llm:
            flow = "check topical drift semantic"
            if flow not in config.rails.input.flows:
                config.rails.input.flows.append(flow)
        return LLMRails(config)
    except Exception as exc:
        raise NemoCheckError(f"failed to build NeMo rails: {type(exc).__name__}") from exc


def _run_rails(rails: Any, messages: list[dict[str, str]], rail: str) -> dict[str, object]:
    try:
        from nemoguardrails.rails.llm.options import GenerationOptions
    except ImportError as exc:
        raise NemoCheckError("nemoguardrails not installed (pip install -e '.[nemo]')") from exc

    try:
        response = asyncio.run(
            rails.generate_async(
                messages=messages,
                options=GenerationOptions(rails=[rail], output_vars=True),
            )
        )
    except Exception as exc:
        raise NemoCheckError(f"NeMo {rail} scan failed: {type(exc).__name__}") from exc
    return dict(response.output_data or {})


def scan_input(text: str, settings: Settings) -> list[str]:
    """Run the NeMo input rails. Returns flags (empty = nothing flagged).
    Raises NemoCheckError on any failure; the caller falls back to the
    floor's own (already-passed) verdict."""
    rails = _build_rails(settings)
    output_data = _run_rails(rails, [{"role": "user", "content": text}], "input")
    triggered = output_data.get("triggered_input_rail")
    if not triggered:
        return []
    return [_INPUT_RAIL_FLAGS.get(str(triggered), str(triggered))]


def scan_output(text: str, settings: Settings) -> list[str]:
    """Run the NeMo output rails against already-generated text. Returns
    flags (empty = nothing flagged). Raises NemoCheckError on any failure."""
    rails = _build_rails(settings)
    messages = [
        {"role": "user", "content": ""},
        {"role": "assistant", "content": text},
    ]
    output_data = _run_rails(rails, messages, "output")
    triggered = output_data.get("triggered_output_rail")
    if not triggered:
        return []
    return [_OUTPUT_RAIL_FLAGS.get(str(triggered), str(triggered))]
