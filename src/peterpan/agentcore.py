"""Amazon Bedrock AgentCore Runtime adapter — opt-in, fail-safe.

The EC2 ``agent`` service remains the stable application adapter. When
``PP_AGENT_PROVIDER=agentcore`` and ``PP_AGENTCORE_RUNTIME_ARN`` is set, this
module invokes the managed runtime via boto3 ``bedrock-agentcore`` and maps
the response into ``IncidentStory``. Any failure raises ``AgentCoreError`` so
callers fall back to the local story path and label ``local-fallback``.

This is NOT Bedrock Agents Classic. AgentCore is not installed on EC2 —
only invoked remotely through IAM.
"""

from __future__ import annotations

import json
import uuid
from typing import Any

from peterpan.config import Settings
from peterpan.schemas import Alert, IncidentStory, ProviderReport


class AgentCoreError(Exception):
    """Any AgentCore-path failure. Callers must fall back to local synthesis."""


def _session_id(alert: Alert) -> str:
    # AgentCore requires runtimeSessionId length >= 33.
    return f"pp-{alert.id}-{uuid.uuid4().hex}"[:64].ljust(33, "0")


def _payload(alert: Alert) -> bytes:
    body = {
        "input": {
            "prompt": (
                f"Investigate alert {alert.id}: {alert.title}. {alert.description}. "
                "Return a JSON IncidentStory with probable_cause, confidence<1, "
                "evidence[], repair_options[]."
            ),
            "alert": alert.model_dump(mode="json"),
        }
    }
    return json.dumps(body).encode("utf-8")


def _parse_story(raw: bytes | str, alert: Alert) -> IncidentStory:
    text = raw.decode("utf-8") if isinstance(raw, (bytes, bytearray)) else raw
    data: Any = json.loads(text)
    # Tolerate common AgentCore wrappers: {output:{...}}, {story:{...}}, flat.
    if isinstance(data, dict):
        for key in ("story", "output", "result", "data"):
            nested = data.get(key)
            if isinstance(nested, dict) and ("probable_cause" in nested or "alert" in nested):
                data = nested
                break
            if isinstance(nested, dict) and "message" in nested:
                # message may itself be a JSON string
                msg = nested["message"]
                if isinstance(msg, str) and msg.strip().startswith("{"):
                    data = json.loads(msg)
                    break
        if "alert" not in data:
            data = {**data, "alert": alert.model_dump(mode="json")}
    story = IncidentStory.model_validate(data)
    # Never trust the remote payload's provider claim — we know we used AgentCore.
    return story.model_copy(
        update={
            "providers": ProviderReport(
                llm=story.providers.llm if story.providers.llm != "off" else "bedrock",
                configured_llm=story.providers.configured_llm,
                llm_fallback=False,
                rag_backend=story.providers.rag_backend,
                rag_fallback=story.providers.rag_fallback,
                rag_fallback_reason=story.providers.rag_fallback_reason,
                predictor=story.providers.predictor,
                predictor_model_version=story.providers.predictor_model_version,
                agent_provider="agentcore",
            )
        }
    )


def invoke_story(alert: Alert, settings: Settings) -> IncidentStory:
    """Invoke AgentCore Runtime. Raises AgentCoreError on any failure."""
    arn = (settings.agentcore_runtime_arn or "").strip()
    if not arn:
        raise AgentCoreError("PP_AGENTCORE_RUNTIME_ARN is not configured")

    try:
        import boto3  # lazy: optional `aws` extra
    except ImportError as exc:
        raise AgentCoreError("boto3 not installed (pip install -e '.[aws]')") from exc

    # Timeouts are enforced by the caller / SDK defaults; we avoid importing
    # botocore.config stubs (not always present under mypy).
    client = boto3.client("bedrock-agentcore", region_name=settings.aws_region)
    _ = settings.agentcore_timeout_s  # reserved for future Config wiring
    try:
        response = client.invoke_agent_runtime(
            agentRuntimeArn=arn,
            runtimeSessionId=_session_id(alert),
            qualifier=settings.agentcore_qualifier,
            payload=_payload(alert),
            contentType="application/json",
            accept="application/json",
        )
        stream = response.get("response")
        if stream is None:
            raise AgentCoreError("agentcore response missing body")
        raw = stream.read() if hasattr(stream, "read") else b"".join(stream)
        return _parse_story(raw, alert)
    except AgentCoreError:
        raise
    except Exception as exc:  # noqa: BLE001 — collapse SDK/network/parse to fallback
        raise AgentCoreError(f"agentcore invoke failed: {type(exc).__name__}") from exc
