"""Guardrails service — deterministic floors with final say over any LLM.

Input rail: is this a genuine ops signal (not spam/injection)?
Output rail: does a generated story/report avoid fabricated guarantees?

The regex floor is intentionally simple and ALWAYS wins — NeMo Guardrails or
an LLM judge can be layered on top, but can never override a floor rejection.
"""

from __future__ import annotations

import re

from fastapi import FastAPI
from pydantic import BaseModel

from peterpan.schemas import GuardrailVerdict

app = FastAPI(title="peter-pan-guardrails")

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
    flags = [flag for pattern, flag in _OUTPUT_BLOCK if re.search(pattern, text)]
    return GuardrailVerdict(
        passed=not flags,
        flags=flags,
        reason="flagged for human review: " + "; ".join(flags) if flags else "",
    )


class TextIn(BaseModel):
    text: str


@app.get("/healthz")
def healthz() -> dict[str, str]:
    return {"service": "guardrails", "status": "ok"}


@app.post("/check/input")
def check_input_route(body: TextIn) -> GuardrailVerdict:
    return check_input(body.text)


@app.post("/check/output")
def check_output_route(body: TextIn) -> GuardrailVerdict:
    return check_output(body.text)
