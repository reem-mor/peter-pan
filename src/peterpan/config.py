"""Environment-based configuration.

The three-environment model is a core product invariant, not deploy trivia:

- **mirage**     — secure simulation. Everything is fixture-backed; actions run
                   against stubs. Safe for demos and prompt iteration.
- **staging**    — workflow validation. Real service wiring, synthetic data.
- **production** — read-only by default. Any mutating action must go through
                   an ActionPreview and receive explicit human approval.
"""

from __future__ import annotations

from enum import StrEnum

from pydantic import AliasChoices, Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Env(StrEnum):
    MIRAGE = "mirage"
    STAGING = "staging"
    PRODUCTION = "production"


class LlmProvider(StrEnum):
    OFF = "off"  # fixture-first default: demo path never depends on a live LLM
    ANTHROPIC = "anthropic"  # direct Anthropic API (ANTHROPIC_API_KEY)
    BEDROCK = "bedrock"  # AWS Bedrock (boto3 credential chain — no key in Settings)


class RagBackend(StrEnum):
    LEXICAL = "lexical"  # fixture-first default: token overlap over knowledge/
    PINECONE = "pinecone"  # semantic: Voyage embeddings + Pinecone index


class PredictorBackend(StrEnum):
    FLOOR = "floor"  # fixture-first default: deterministic keyword floor only
    TORCH = "torch"  # + local PyTorch classifier, guarded by the floor


class GuardrailsBackend(StrEnum):
    REGEX = "regex"  # fixture-first default: deterministic regex floor only
    NEMO = "nemo"  # + NeMo Guardrails pattern rails layered on top, floor always wins


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="PP_", env_file=".env", extra="ignore")

    env: Env = Field(default=Env.MIRAGE)
    service_name: str = Field(default="peter-pan")
    usage_log_path: str = Field(default="usage.jsonl")
    # Operator feedback on agent output — the learning loop's raw material
    # (see peterpan.feedback_store / peterpan.scoring). Same append-only
    # JSONL pattern as usage_log_path.
    feedback_log_path: str = Field(default="data/feedback.jsonl")
    # Mesh healthz targets for PETER PAN OS /os/services. Defaults match local
    # dev; in docker-compose set PP_MESH='{"predictor": "http://predictor:8001", ...}'.
    mesh: dict[str, str] = Field(
        default={
            "predictor": "http://localhost:8001",
            "rag": "http://localhost:8002",
            "guardrails": "http://localhost:8003",
            "agent": "http://localhost:8004",
        }
    )
    # Daily LLM spend budget surfaced by PETER PAN OS (/os/budget). Report-only.
    daily_budget_usd: float = Field(default=5.0, gt=0)

    # LLM synthesis is opt-in (PP_LLM=anthropic); any failure falls back to
    # the deterministic path so the demo never hard-depends on a live model.
    llm: LlmProvider = Field(default=LlmProvider.OFF)
    anthropic_model: str = Field(default="claude-sonnet-5")
    # Bedrock (PP_LLM=bedrock): model id must exist in the account/region —
    # this default is the current known-good Sonnet id on Bedrock; override
    # with PP_BEDROCK_MODEL_ID as newer Sonnets land. Credentials come from
    # the boto3 chain (env / instance profile), never from Settings.
    bedrock_model_id: str = Field(default="anthropic.claude-sonnet-4-5-20250929-v1:0")
    aws_region: str | None = Field(
        default=None,  # None -> boto3's own region resolution chain
        validation_alias=AliasChoices("AWS_REGION", "PP_AWS_REGION"),
    )
    # Credentials are SecretStr: repr/str/model_dump mask the value, so a
    # settings object landing in a log line, traceback, or pytest assertion
    # diff never echoes a live key. Call .get_secret_value() only at the
    # client-construction boundary.
    anthropic_api_key: SecretStr | None = Field(
        default=None,
        validation_alias=AliasChoices("ANTHROPIC_API_KEY", "PP_ANTHROPIC_API_KEY"),
    )

    # Predictor backend — floor by default; torch adds the local classifier
    # behind the floor's veto and falls back to floor-only on any failure.
    predictor: PredictorBackend = Field(default=PredictorBackend.FLOOR)

    # Guardrails backend — regex floor by default; nemo layers NeMo
    # Guardrails pattern rails on top. The floor always wins: nemo can only
    # turn a floor pass into a flagged fail, never a floor fail into a pass,
    # and any nemo-path failure falls back to the floor's own verdict.
    guardrails: GuardrailsBackend = Field(default=GuardrailsBackend.REGEX)
    # The one NeMo rail that calls an LLM (semantic topical check) — OFF by
    # default even when guardrails=nemo, so the fixture/demo path never
    # depends on a live model. Enabling it also requires PP_LLM=anthropic
    # and a live ANTHROPIC_API_KEY. See src/peterpan/nemo_rails.py.
    nemo_topical_llm: bool = Field(default=False)

    # Retrieval backend — lexical by default; pinecone is the semantic upgrade
    # and falls back to lexical on any failure.
    rag_backend: RagBackend = Field(default=RagBackend.LEXICAL)
    pinecone_index: str = Field(default="peter-pan-knowledge")
    pinecone_api_key: SecretStr | None = Field(
        default=None,
        validation_alias=AliasChoices("PINECONE_API_KEY", "PP_PINECONE_API_KEY"),
    )
    voyage_model: str = Field(default="voyage-3.5-lite")
    voyage_api_key: SecretStr | None = Field(
        default=None,
        validation_alias=AliasChoices("VOYAGE_API_KEY", "PP_VOYAGE_API_KEY"),
    )

    # n8n webhook notified on each landing-page lead (PP_N8N_LEAD_WEBHOOK).
    # Unset (default) disables the notification; the lead is stored regardless.
    n8n_lead_webhook: str | None = Field(default=None)

    # Cache/queue backend (ADR-0001) — opt-in Redis; unset (default) or any
    # connection failure falls back to the in-process cache/queue so the
    # fixture-first demo path never depends on a live Redis instance.
    redis_url: str | None = Field(default=None)

    # Observability (§6.6) — Langfuse tracing is opt-in; unset (default) or
    # any Langfuse failure falls back to no-op (but still uuid'd) tracing so
    # the fixture-first demo path never depends on a live Langfuse instance.
    langfuse_public_key: str | None = Field(
        default=None,
        validation_alias=AliasChoices("LANGFUSE_PUBLIC_KEY", "PP_LANGFUSE_PUBLIC_KEY"),
    )
    langfuse_secret_key: SecretStr | None = Field(
        default=None,
        validation_alias=AliasChoices("LANGFUSE_SECRET_KEY", "PP_LANGFUSE_SECRET_KEY"),
    )
    langfuse_host: str | None = Field(
        default=None,
        validation_alias=AliasChoices("LANGFUSE_HOST", "PP_LANGFUSE_HOST"),
    )
    # Structured prompt/completion log (§6.6) — hashes + scrubbed previews
    # only, never raw text. Queryable by trace_id via observability.py.
    prompt_log_path: str = Field(default="data/prompt_log.jsonl")

    @property
    def actions_allowed(self) -> bool:
        """Mutating actions may only auto-execute outside production."""
        return self.env is not Env.PRODUCTION
