"""Langfuse tracing + structured prompt/completion log (§6.6).

No live Langfuse dependency in CI: the "configured" path is exercised via a
fake module injected into sys.modules, exactly like tests/test_llm_synthesis.py
fakes `anthropic`.
"""

from __future__ import annotations

import json
import sys
import types
import uuid

import pytest

from peterpan import observability as obs_mod
from peterpan.config import Settings


@pytest.fixture(autouse=True)
def _clean_langfuse_env(monkeypatch: pytest.MonkeyPatch) -> None:
    """Every test starts unconfigured; opt-in tests set the env explicitly."""
    monkeypatch.delenv("LANGFUSE_PUBLIC_KEY", raising=False)
    monkeypatch.delenv("LANGFUSE_SECRET_KEY", raising=False)
    monkeypatch.delenv("LANGFUSE_HOST", raising=False)
    monkeypatch.delenv("PP_LANGFUSE_PUBLIC_KEY", raising=False)
    monkeypatch.delenv("PP_LANGFUSE_SECRET_KEY", raising=False)
    monkeypatch.delenv("PP_LANGFUSE_HOST", raising=False)


# --- no-op mode: unset Langfuse config -----------------------------------------


def test_trace_run_noop_mode_still_mints_a_uuid_trace_id() -> None:
    settings = Settings()
    trace = obs_mod.trace_run(service="agent", model="claude-sonnet-5", settings=settings)
    assert uuid.UUID(trace.trace_id)  # a real uuid, not a placeholder string


def test_trace_run_noop_mode_produces_a_prompt_log_entry(tmp_path: object) -> None:
    log_path = tmp_path / "prompt_log.jsonl"  # type: ignore[operator]
    settings = Settings(prompt_log_path=str(log_path))
    trace = obs_mod.trace_run(service="agent", model="claude-sonnet-5", settings=settings)

    trace.record(
        surface="incident-agent",
        system_prompt="be helpful",
        input_text="alert: checkout down",
        output_text='{"what_changed": "..."}',
        input_tokens=12,
        output_tokens=8,
        cost_usd=0.001,
        cached=False,
    )

    rows = [json.loads(line) for line in log_path.read_text(encoding="utf-8").splitlines()]
    assert len(rows) == 1
    row = rows[0]
    assert row["trace_id"] == trace.trace_id
    assert row["service"] == "agent"
    assert row["model"] == "claude-sonnet-5"
    assert row["cached"] is False
    assert row["input_tokens"] == 12
    assert row["output_tokens"] == 8
    assert row["cost_usd"] == 0.001
    assert row["prompt_version"] == "incident-agent/system-v6.txt"
    assert "system_prompt_sha256" in row and "completion_sha256" in row


def test_no_langfuse_env_never_imports_langfuse_module(monkeypatch: pytest.MonkeyPatch) -> None:
    """The `obs` extra must stay optional: importing peterpan.observability
    and using no-op tracing must never require `langfuse` to be installed."""
    monkeypatch.delitem(sys.modules, "langfuse", raising=False)
    settings = Settings()
    trace = obs_mod.trace_run(service="agent", model="m", settings=settings)
    assert trace._langfuse_trace is None
    assert "langfuse" not in sys.modules


# --- cached path ------------------------------------------------------------


def test_record_cached_call_logs_zero_cost_and_cached_true(tmp_path: object) -> None:
    log_path = tmp_path / "prompt_log.jsonl"  # type: ignore[operator]
    settings = Settings(prompt_log_path=str(log_path))
    trace = obs_mod.trace_run(service="agent", model="claude-sonnet-5", settings=settings)

    trace.record(
        surface="incident-agent",
        system_prompt="be helpful",
        input_text="alert: checkout down",
        output_text='{"what_changed": "..."}',
        input_tokens=0,
        output_tokens=0,
        cost_usd=0.0,
        cached=True,
    )

    row = json.loads(log_path.read_text(encoding="utf-8").splitlines()[0])
    assert row["cached"] is True
    assert row["cost_usd"] == 0.0
    assert row["input_tokens"] == 0


# --- Langfuse-configured mode, behind a fake module -------------------------


def _install_fake_langfuse(monkeypatch: pytest.MonkeyPatch, *, generation_calls: list) -> None:
    class _FakeTrace:
        id = "trace-abc-123"

        def generation(self, **kwargs: object) -> None:
            generation_calls.append(kwargs)

    class _FakeLangfuse:
        def __init__(self, **kwargs: object) -> None:
            self.kwargs = kwargs

        def trace(self, **kwargs: object) -> _FakeTrace:
            return _FakeTrace()

    fake_module = types.SimpleNamespace(Langfuse=_FakeLangfuse)
    monkeypatch.setitem(sys.modules, "langfuse", fake_module)


def test_trace_run_uses_langfuse_trace_id_when_configured(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("LANGFUSE_PUBLIC_KEY", "pk-test")
    monkeypatch.setenv("LANGFUSE_SECRET_KEY", "sk-test")
    generation_calls: list = []
    _install_fake_langfuse(monkeypatch, generation_calls=generation_calls)

    settings = Settings()
    trace = obs_mod.trace_run(service="agent", model="claude-sonnet-5", settings=settings)

    assert trace.trace_id == "trace-abc-123"
    assert trace._langfuse_trace is not None


def test_record_calls_langfuse_generation_with_model_tokens_cost(
    monkeypatch: pytest.MonkeyPatch, tmp_path: object
) -> None:
    monkeypatch.setenv("LANGFUSE_PUBLIC_KEY", "pk-test")
    monkeypatch.setenv("LANGFUSE_SECRET_KEY", "sk-test")
    generation_calls: list = []
    _install_fake_langfuse(monkeypatch, generation_calls=generation_calls)

    log_path = tmp_path / "prompt_log.jsonl"  # type: ignore[operator]
    settings = Settings(prompt_log_path=str(log_path))
    trace = obs_mod.trace_run(service="agent", model="claude-sonnet-5", settings=settings)

    trace.record(
        surface="incident-agent",
        system_prompt="be helpful",
        input_text="alert text",
        output_text="completion text",
        input_tokens=100,
        output_tokens=50,
        cost_usd=0.01,
        cached=False,
    )

    assert len(generation_calls) == 1
    call = generation_calls[0]
    assert call["model"] == "claude-sonnet-5"
    assert call["usage"] == {"input": 100, "output": 50}
    assert call["metadata"] == {"cost_usd": 0.01, "cached": False}
    # the prompt-log row is still written alongside the Langfuse span
    assert len(log_path.read_text(encoding="utf-8").splitlines()) == 1


def test_langfuse_construction_failure_degrades_to_noop(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("LANGFUSE_PUBLIC_KEY", "pk-test")
    monkeypatch.setenv("LANGFUSE_SECRET_KEY", "sk-test")

    class _BoomLangfuse:
        def __init__(self, **kwargs: object) -> None:
            raise ConnectionError("simulated Langfuse outage")

    monkeypatch.setitem(sys.modules, "langfuse", types.SimpleNamespace(Langfuse=_BoomLangfuse))

    settings = Settings()
    trace = obs_mod.trace_run(service="agent", model="m", settings=settings)

    assert uuid.UUID(trace.trace_id)  # still got a usable trace_id
    assert trace._langfuse_trace is None


def test_langfuse_generation_failure_never_breaks_the_prompt_log(
    monkeypatch: pytest.MonkeyPatch, tmp_path: object
) -> None:
    monkeypatch.setenv("LANGFUSE_PUBLIC_KEY", "pk-test")
    monkeypatch.setenv("LANGFUSE_SECRET_KEY", "sk-test")

    class _FlakyTrace:
        id = "trace-flaky"

        def generation(self, **kwargs: object) -> None:
            raise ConnectionError("simulated mid-call Langfuse failure")

    class _FlakyLangfuse:
        def __init__(self, **kwargs: object) -> None:
            pass

        def trace(self, **kwargs: object) -> _FlakyTrace:
            return _FlakyTrace()

    monkeypatch.setitem(sys.modules, "langfuse", types.SimpleNamespace(Langfuse=_FlakyLangfuse))

    log_path = tmp_path / "prompt_log.jsonl"  # type: ignore[operator]
    settings = Settings(prompt_log_path=str(log_path))
    trace = obs_mod.trace_run(service="agent", model="m", settings=settings)

    trace.record(
        surface="incident-agent",
        system_prompt="s",
        input_text="i",
        output_text="o",
        input_tokens=1,
        output_tokens=1,
        cost_usd=0.0,
        cached=False,
    )  # must not raise despite the Langfuse client blowing up

    assert len(log_path.read_text(encoding="utf-8").splitlines()) == 1


# --- secret scrubbing (adversarial) -----------------------------------------


@pytest.mark.parametrize(
    "secret_text",
    [
        "please use password=hunter2 to log in",
        "API_KEY: sk-abcdef1234567890",
        "Authorization: Bearer eyJhbGciOiJIUzI1NiJ9.secretpayload",
        "token=ghp_1234567890abcdef",
    ],
)
def test_preview_scrubs_secret_looking_content(secret_text: str, tmp_path: object) -> None:
    log_path = tmp_path / "prompt_log.jsonl"  # type: ignore[operator]
    settings = Settings(prompt_log_path=str(log_path))
    trace = obs_mod.trace_run(service="agent", model="m", settings=settings)

    trace.record(
        surface="incident-agent",
        system_prompt="s",
        input_text=f"attacker-controlled alert description: {secret_text}",
        output_text="fine",
        input_tokens=1,
        output_tokens=1,
        cost_usd=0.0,
        cached=False,
    )

    row = json.loads(log_path.read_text(encoding="utf-8").splitlines()[0])
    assert "hunter2" not in row["preview"]
    assert "sk-abcdef1234567890" not in row["preview"]
    assert "secretpayload" not in row["preview"]
    assert "ghp_1234567890abcdef" not in row["preview"]
    assert "<redacted>" in row["preview"]


def test_preview_is_capped_at_200_chars() -> None:
    long_text = "x" * 500
    preview = obs_mod._preview(long_text)
    assert len(preview) <= 200


def test_read_prompt_log_missing_file_returns_empty_list(tmp_path: object) -> None:
    missing = tmp_path / "does-not-exist.jsonl"  # type: ignore[operator]
    assert obs_mod.read_prompt_log("any-trace", str(missing)) == []


def test_read_prompt_log_filters_by_trace_id(tmp_path: object) -> None:
    log_path = tmp_path / "prompt_log.jsonl"  # type: ignore[operator]
    settings = Settings(prompt_log_path=str(log_path))

    trace_a = obs_mod.trace_run(service="agent", model="m", settings=settings)
    trace_a.record(
        surface="incident-agent",
        system_prompt="s",
        input_text="i",
        output_text="o",
        input_tokens=1,
        output_tokens=1,
        cost_usd=0.0,
    )
    trace_b = obs_mod.trace_run(service="agent", model="m", settings=settings)
    trace_b.record(
        surface="incident-agent",
        system_prompt="s",
        input_text="i2",
        output_text="o2",
        input_tokens=1,
        output_tokens=1,
        cost_usd=0.0,
    )

    rows = obs_mod.read_prompt_log(trace_a.trace_id, str(log_path))
    assert len(rows) == 1
    assert rows[0]["trace_id"] == trace_a.trace_id


# --- prompt_version() lookup -------------------------------------------------


def test_prompt_version_reads_current_incident_agent_surface() -> None:
    assert obs_mod.prompt_version("incident-agent") == "incident-agent/system-v6.txt"


def test_prompt_version_unknown_surface_returns_none() -> None:
    assert obs_mod.prompt_version("no-such-surface") is None


def test_prompt_version_missing_file_returns_none(
    monkeypatch: pytest.MonkeyPatch, tmp_path: object
) -> None:
    monkeypatch.setattr(obs_mod, "_VERSIONS_PATH", tmp_path / "nope.yaml")  # type: ignore[operator]
    assert obs_mod.prompt_version("incident-agent") is None
