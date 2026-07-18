"""Credentials in Settings are SecretStr — masked everywhere they can leak.

repr/str/model_dump of a Settings object must never echo a live key into a
log line, traceback, or pytest assertion diff (the PR #45 failure mode, now
closed at the type level instead of per-test).

Every instantiation here passes _env_file=None: hermetic against the
ambient developer .env, so these tests see only what they set themselves.
"""

from __future__ import annotations

import pytest

from peterpan.config import Settings

_KEY_ENV_VARS = (
    "ANTHROPIC_API_KEY",
    "PINECONE_API_KEY",
    "VOYAGE_API_KEY",
    "LANGFUSE_SECRET_KEY",
)
_SENTINEL = "test-key-should-never-appear-in-output"


def _clear_key_env(monkeypatch: pytest.MonkeyPatch) -> None:
    for var in _KEY_ENV_VARS:
        monkeypatch.delenv(var, raising=False)
        monkeypatch.delenv(f"PP_{var}", raising=False)


def test_keys_are_masked_in_repr_str_and_dump(monkeypatch: pytest.MonkeyPatch) -> None:
    for var in _KEY_ENV_VARS:
        monkeypatch.setenv(var, _SENTINEL)
    settings = Settings(_env_file=None)

    exposed = repr(settings) + str(settings) + str(settings.model_dump())
    exposed += settings.model_dump_json()
    assert _SENTINEL not in exposed

    # the real value is still retrievable at the client-construction boundary
    assert settings.anthropic_api_key is not None
    assert settings.anthropic_api_key.get_secret_value() == _SENTINEL
    assert settings.pinecone_api_key is not None
    assert settings.pinecone_api_key.get_secret_value() == _SENTINEL
    assert settings.voyage_api_key is not None
    assert settings.voyage_api_key.get_secret_value() == _SENTINEL
    assert settings.langfuse_secret_key is not None
    assert settings.langfuse_secret_key.get_secret_value() == _SENTINEL


def test_no_key_state_resolves_to_none(monkeypatch: pytest.MonkeyPatch) -> None:
    _clear_key_env(monkeypatch)
    settings = Settings(_env_file=None)
    assert settings.anthropic_api_key is None
    assert settings.pinecone_api_key is None
    assert settings.voyage_api_key is None
    assert settings.langfuse_secret_key is None
