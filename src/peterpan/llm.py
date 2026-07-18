"""Claude-backed story synthesis — opt-in, invariant-guarded, metered.

The LLM refines the narrative; it never gets to break the invariants:
- prompt comes from the versioned file at _PROMPT_PATH (see prompts/versions.yaml
  and prompts/incident-agent/LOG.md for the current version + eval trail)
- output is pydantic-validated; every cited source must be in the allowlist
  of evidence actually collected (fabricated citations => rejection)
- confidence is capped below 1.0; class/severity come from the predictor
- every call logs tokens + cost to PETER PAN OS via peterpan.usage
- ANY failure (API, parse, validation) raises LlmSynthesisError so the
  caller falls back to the deterministic path — fail-safe by construction.
"""

from __future__ import annotations

import json
from pathlib import Path

from pydantic import BaseModel, Field, ValidationError

from peterpan.cache import DEFAULT_TTL_S, cache_get, cache_key, cache_set
from peterpan.config import Settings
from peterpan.schemas import Alert, Evidence, IncidentStory, Prediction, RagResult
from peterpan.usage import log_usage, make_event, model_rates

_PROMPT_PATH = Path(__file__).parent.parent.parent / "prompts" / "incident-agent" / "system-v6.txt"


class LlmSynthesisError(Exception):
    """Any LLM-path failure. Callers must catch this and fall back."""


class _LlmStoryDraft(BaseModel):
    """The exact JSON contract the prompt demands from the model."""

    what_changed: str
    probable_cause: str
    confidence: float = Field(ge=0.0, le=1.0)
    evidence: list[Evidence]
    repair_options: list[str]


def load_system_prompt() -> str:
    return _PROMPT_PATH.read_text(encoding="utf-8")


def _validate_draft(
    draft: _LlmStoryDraft, prediction: Prediction, allowed_sources: set[str]
) -> None:
    fabricated = [e.source for e in draft.evidence if e.source not in allowed_sources]
    if fabricated:
        raise LlmSynthesisError(f"fabricated citations rejected: {fabricated}")
    if not draft.evidence:
        raise LlmSynthesisError("story without evidence rejected")
    if draft.probable_cause != prediction.incident_class:
        raise LlmSynthesisError(
            f"LLM contradicted the deterministic class "
            f"({draft.probable_cause!r} != {prediction.incident_class!r})"
        )


def synthesize(
    alert: Alert,
    prediction: Prediction,
    rag: RagResult,
    settings: Settings,
) -> IncidentStory:
    """Real-LLM synthesis. Raises LlmSynthesisError on any failure."""
    if not settings.anthropic_api_key:
        raise LlmSynthesisError("no ANTHROPIC_API_KEY configured")

    try:
        import anthropic  # lazy: optional `llm` extra
    except ImportError as exc:
        raise LlmSynthesisError("anthropic SDK not installed (pip install -e '.[llm]')") from exc

    # The alert itself is first-class, citable evidence (source alert:<origin>)
    # — v2 prompt-log finding: the model rightly kept citing it, so it belongs
    # in the contract rather than being fought in the prompt.
    alert_source = f"alert:{alert.source}"
    allowed = {
        alert_source,
        "predictor:/predict",
        *(m.source for m in rag.matches if m.confidence > 0),
    }
    evidence_payload = [
        {
            "kind": "alert",
            "summary": f"{alert.title} — {alert.description}",
            "source": alert_source,
            "confidence": 0.6,
        },
        {
            "kind": "metric",
            "summary": f"classified as {prediction.incident_class} at {prediction.severity}",
            "source": "predictor:/predict",
            "confidence": prediction.confidence,
        },
        *[m.model_dump() for m in rag.matches if m.confidence > 0],
    ]
    user_content = json.dumps(
        {
            "alert": {
                "title": alert.title,
                "description": alert.description,
                "source": alert.source,
                "severity": alert.severity,
            },
            "deterministic_classification": prediction.model_dump(),
            "evidence": evidence_payload,
        },
        default=str,
    )

    # Response cache (ADR-0001): key = sha256(model + system prompt + user
    # payload), so a hit only ever replays a completion for the exact same
    # model+prompt+evidence. A hit skips the priced API call entirely — no
    # log_usage entry — but is still counted via cache.cache_stats().
    system_prompt = load_system_prompt()
    key = cache_key(settings.anthropic_model, system_prompt + user_content)
    raw = cache_get(key)

    if raw is None:
        try:
            client = anthropic.Anthropic(api_key=settings.anthropic_api_key)
            response = client.messages.create(
                model=settings.anthropic_model,
                max_tokens=1500,
                system=system_prompt,
                messages=[{"role": "user", "content": user_content}],
            )
        except Exception as exc:
            raise LlmSynthesisError(f"anthropic API failure: {type(exc).__name__}") from exc

        log_usage(
            make_event(
                service="agent",
                agent="incident-agent",
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

        raw = "".join(block.text for block in response.content if block.type == "text").strip()
        cache_set(key, raw, ttl_s=DEFAULT_TTL_S)

    try:
        draft = _LlmStoryDraft.model_validate_json(raw)
    except ValidationError as exc:
        raise LlmSynthesisError(
            f"LLM output failed schema validation: {exc.error_count()} errors"
        ) from exc

    _validate_draft(draft, prediction, allowed)

    return IncidentStory(
        alert=alert,
        what_changed=draft.what_changed,
        probable_cause=prediction.incident_class,  # floor's verdict, always
        confidence=min(draft.confidence, 0.9),  # never certainty
        evidence=draft.evidence,
        repair_options=draft.repair_options,
    )
