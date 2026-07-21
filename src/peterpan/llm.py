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
from peterpan.config import LlmProvider, Settings
from peterpan.observability import trace_run
from peterpan.schemas import Alert, Evidence, IncidentStory, Prediction, RagResult
from peterpan.usage import log_usage, make_event, model_rates

_PROMPT_PATH = Path(__file__).parent.parent.parent / "prompts" / "incident-agent" / "system-v6.txt"
_SURFACE = "incident-agent"


class LlmSynthesisError(Exception):
    """Any LLM-path failure. Callers must catch this and fall back."""


class _LlmStoryDraft(BaseModel):
    """The exact JSON contract the prompt demands from the model."""

    what_changed: str
    probable_cause: str
    # le=1.0 (not lt): this is the model's RAW draft, not a system output. A
    # draft claiming 1.0 is accepted and clamped by min(confidence, 0.9) below
    # — rejecting it here would trade a cheap cap for a full fallback.
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


def _anthropic_complete(
    system_prompt: str, user_content: str, settings: Settings
) -> tuple[str, int, int]:
    """One direct-API completion. Returns (text, input_tokens, output_tokens)."""
    if not settings.anthropic_api_key:
        raise LlmSynthesisError("no ANTHROPIC_API_KEY configured")
    try:
        import anthropic  # lazy: optional `llm` extra
    except ImportError as exc:
        raise LlmSynthesisError("anthropic SDK not installed (pip install -e '.[llm]')") from exc
    try:
        client = anthropic.Anthropic(api_key=settings.anthropic_api_key.get_secret_value())
        response = client.messages.create(
            model=settings.anthropic_model,
            max_tokens=1500,
            system=system_prompt,
            messages=[{"role": "user", "content": user_content}],
        )
    except Exception as exc:
        raise LlmSynthesisError(f"anthropic API failure: {type(exc).__name__}") from exc
    text = "".join(block.text for block in response.content if block.type == "text").strip()
    return text, response.usage.input_tokens, response.usage.output_tokens


def _bedrock_complete(
    system_prompt: str, user_content: str, settings: Settings
) -> tuple[str, int, int]:
    """One Bedrock Converse completion. Credentials come from the boto3
    chain (env vars locally, instance profile on EC2) — never Settings."""
    try:
        import boto3  # lazy: optional `aws` extra
    except ImportError as exc:
        raise LlmSynthesisError("boto3 not installed (pip install -e '.[aws]')") from exc
    try:
        client = boto3.client("bedrock-runtime", region_name=settings.aws_region)
        response = client.converse(
            modelId=settings.bedrock_model_id,
            system=[{"text": system_prompt}],
            messages=[{"role": "user", "content": [{"text": user_content}]}],
            inferenceConfig={"maxTokens": 1500},
        )
    except Exception as exc:
        raise LlmSynthesisError(f"bedrock API failure: {type(exc).__name__}") from exc
    blocks = response["output"]["message"]["content"]
    text = "".join(b["text"] for b in blocks if "text" in b).strip()
    usage = response["usage"]
    return text, int(usage["inputTokens"]), int(usage["outputTokens"])


def resolve_model(settings: Settings) -> str:
    """The model id that meters, caches, and traces this call."""
    if settings.llm is LlmProvider.BEDROCK:
        return settings.bedrock_model_id
    return settings.anthropic_model


def synthesize(
    alert: Alert,
    prediction: Prediction,
    rag: RagResult,
    settings: Settings,
) -> IncidentStory:
    """Real-LLM synthesis. Raises LlmSynthesisError on any failure."""
    model_name = resolve_model(settings)
    trace = trace_run(service="agent", model=model_name, settings=settings)

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
    key = cache_key(model_name, system_prompt + user_content)
    raw = cache_get(key)

    if raw is None:
        complete = _bedrock_complete if settings.llm is LlmProvider.BEDROCK else _anthropic_complete
        raw, input_tokens, output_tokens = complete(system_prompt, user_content, settings)

        rate_in, rate_out = model_rates(model_name)
        cost_usd = round(input_tokens * rate_in + output_tokens * rate_out, 6)

        log_usage(
            make_event(
                service="agent",
                agent="incident-agent",
                model=model_name,
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                cost_usd=cost_usd,
            ),
            settings.usage_log_path,
        )

        fresh = True
    else:
        fresh = False
        input_tokens = 0
        output_tokens = 0
        cost_usd = 0.0

    # Structured prompt/completion log (§6.6): every call — cached or fresh,
    # whether or not the completion below passes schema/floor validation —
    # gets one row keyed by trace.trace_id. Hashes + a scrubbed preview only,
    # never raw prompt/completion text.
    trace.record(
        surface=_SURFACE,
        system_prompt=system_prompt,
        input_text=user_content,
        output_text=raw,
        input_tokens=input_tokens,
        output_tokens=output_tokens,
        cost_usd=cost_usd,
        cached=not fresh,
    )

    try:
        draft = _LlmStoryDraft.model_validate_json(raw)
    except ValidationError as exc:
        raise LlmSynthesisError(
            f"LLM output failed schema validation: {exc.error_count()} errors"
        ) from exc

    _validate_draft(draft, prediction, allowed)

    # Cache only fully validated completions (schema + floor checks) — a bad
    # completion must fail once, not be replayed from the cache for 24h. The
    # key covers model + system prompt + full payload, so a hit replays the
    # exact validated context.
    if fresh:
        cache_set(key, raw, ttl_s=DEFAULT_TTL_S)

    return IncidentStory(
        alert=alert,
        what_changed=draft.what_changed,
        probable_cause=prediction.incident_class,  # floor's verdict, always
        confidence=min(draft.confidence, 0.9),  # never certainty
        evidence=draft.evidence,
        repair_options=draft.repair_options,
    )
