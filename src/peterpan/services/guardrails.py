"""Guardrails service — deterministic floors with final say over any LLM.

Input rail: is this a genuine ops signal (not spam/injection)?
Output rail: does a generated story/report avoid fabricated guarantees?

The regex floor is intentionally simple and ALWAYS wins. NeMo Guardrails
(PP_GUARDRAILS=nemo, see peterpan.nemo_rails and guardrails_config/) is
layered on top as purely additive screening:

- a floor fail is final — NeMo is never even consulted
- a floor pass may be turned into a fail by NeMo, flagged with a "nemo:"
  prefix so the origin is always visible in `GuardrailVerdict.flags`
- NeMo can never turn a floor fail into a pass, and any NeMo-path failure
  (package missing, config error, ...) falls back to the floor's own
  verdict — the additive layer breaking must never break availability
"""

from __future__ import annotations

import re

from fastapi import FastAPI
from pydantic import BaseModel

from peterpan import nemo_rails
from peterpan.auth import install_api_auth
from peterpan.config import GuardrailsBackend, Settings
from peterpan.schemas import GuardrailVerdict

app = FastAPI(title="peter-pan-guardrails")
_settings = Settings()
install_api_auth(app, _settings)

# Input floor: obvious non-ops / injection markers.
_INPUT_BLOCK: list[tuple[str, str]] = [
    (r"ignore (all )?(previous|prior) instructions", "prompt_injection"),
    (r"(?i)buy now|limited offer|crypto giveaway", "spam"),
    (r"(?i)disregard your (rules|guidelines)", "prompt_injection"),
]

# Output floor: fabricated certainty an incident report must never contain.
_OUTPUT_BLOCK: list[tuple[str, str]] = [
    (r"(?i)guaranteed (fix|resolution|uptime)", "false_guarantee"),
    (r"(?i)will definitely (resolve|fix)", "false_guarantee"),
    (r"(?i)no (further )?action (is )?needed.{0,40}(certain|100%)", "overconfidence"),
]


def check_input(text: str) -> GuardrailVerdict:
    if not text.strip():
        return GuardrailVerdict(passed=False, flags=["empty"], reason="empty input")
    flags = [flag for pattern, flag in _INPUT_BLOCK if re.search(pattern, text, re.IGNORECASE)]
    return GuardrailVerdict(passed=not flags, flags=flags, reason="; ".join(flags) if flags else "")


def check_output(text: str) -> GuardrailVerdict:
    if not text.strip():
        # Fail closed like the input rail: an empty story/report is never a
        # pass — it means synthesis produced nothing to review.
        return GuardrailVerdict(passed=False, flags=["empty"], reason="empty output")
    flags = [flag for pattern, flag in _OUTPUT_BLOCK if re.search(pattern, text)]
    return GuardrailVerdict(
        passed=not flags,
        flags=flags,
        reason="flagged for human review: " + "; ".join(flags) if flags else "",
    )


def _apply_nemo(floor: GuardrailVerdict, nemo_flags: list[str]) -> GuardrailVerdict:
    """Merge NeMo's additive flags into an already-passed floor verdict. The
    floor's pass is only ever turned into a fail here — never the reverse."""
    if not nemo_flags:
        return floor
    flags = [f"nemo:{flag}" for flag in nemo_flags]
    return GuardrailVerdict(
        passed=False,
        flags=flags,
        reason="flagged by NeMo Guardrails: " + "; ".join(flags),
    )


def check_input_full(text: str, settings: Settings) -> GuardrailVerdict:
    """Floor verdict, optionally screened further by NeMo Guardrails. The
    floor always wins: a floor fail is returned as-is, NeMo is never
    consulted, and any NeMo-path failure falls back to the floor's pass."""
    floor = check_input(text)
    if not floor.passed or settings.guardrails is not GuardrailsBackend.NEMO:
        return floor
    try:
        nemo_flags = nemo_rails.scan_input(text, settings)
    except nemo_rails.NemoCheckError:
        return floor  # additive layer failing must not break the base verdict
    return _apply_nemo(floor, nemo_flags)


def check_output_full(text: str, settings: Settings) -> GuardrailVerdict:
    """Floor verdict, optionally screened further by NeMo Guardrails. Same
    floor-always-wins contract as check_input_full."""
    floor = check_output(text)
    if not floor.passed or settings.guardrails is not GuardrailsBackend.NEMO:
        return floor
    try:
        nemo_flags = nemo_rails.scan_output(text, settings)
    except nemo_rails.NemoCheckError:
        return floor
    return _apply_nemo(floor, nemo_flags)


class TextIn(BaseModel):
    text: str


@app.get("/healthz")
def healthz() -> dict[str, object]:
    return {
        "service": "guardrails",
        "status": "ok",
        "backend": _settings.guardrails.value,
        "auth_required": _settings.api_token is not None,
    }


@app.post("/check/input")
def check_input_route(body: TextIn) -> GuardrailVerdict:
    return check_input_full(body.text, Settings())


@app.post("/check/output")
def check_output_route(body: TextIn) -> GuardrailVerdict:
    return check_output_full(body.text, Settings())
