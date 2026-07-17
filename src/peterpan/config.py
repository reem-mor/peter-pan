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

from pydantic import AliasChoices, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Env(StrEnum):
    MIRAGE = "mirage"
    STAGING = "staging"
    PRODUCTION = "production"


class LlmProvider(StrEnum):
    OFF = "off"  # fixture-first default: demo path never depends on a live LLM
    ANTHROPIC = "anthropic"


class RagBackend(StrEnum):
    LEXICAL = "lexical"  # fixture-first default: token overlap over knowledge/
    PINECONE = "pinecone"  # semantic: Voyage embeddings + Pinecone index


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="PP_", env_file=".env", extra="ignore")

    env: Env = Field(default=Env.MIRAGE)
    service_name: str = Field(default="peter-pan")
    usage_log_path: str = Field(default="usage.jsonl")

    # LLM synthesis is opt-in (PP_LLM=anthropic); any failure falls back to
    # the deterministic path so the demo never hard-depends on a live model.
    llm: LlmProvider = Field(default=LlmProvider.OFF)
    anthropic_model: str = Field(default="claude-sonnet-5")
    anthropic_api_key: str | None = Field(
        default=None,
        validation_alias=AliasChoices("ANTHROPIC_API_KEY", "PP_ANTHROPIC_API_KEY"),
    )

    # Retrieval backend — lexical by default; pinecone is the semantic upgrade
    # and falls back to lexical on any failure.
    rag_backend: RagBackend = Field(default=RagBackend.LEXICAL)
    pinecone_index: str = Field(default="peter-pan-knowledge")
    pinecone_api_key: str | None = Field(
        default=None,
        validation_alias=AliasChoices("PINECONE_API_KEY", "PP_PINECONE_API_KEY"),
    )
    voyage_model: str = Field(default="voyage-3.5-lite")
    voyage_api_key: str | None = Field(
        default=None,
        validation_alias=AliasChoices("VOYAGE_API_KEY", "PP_VOYAGE_API_KEY"),
    )

    @property
    def actions_allowed(self) -> bool:
        """Mutating actions may only auto-execute outside production."""
        return self.env is not Env.PRODUCTION
