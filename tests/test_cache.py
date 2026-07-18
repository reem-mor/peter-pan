"""Cache/queue (ADR-0001) — in-process backend, key stability, fallback."""

from __future__ import annotations

import hashlib
import logging

import pytest

import peterpan.cache as cache_mod


@pytest.fixture(autouse=True)
def _reset_cache_state(monkeypatch: pytest.MonkeyPatch) -> None:
    """Every test starts from a clean slate: no PP_REDIS_URL, no leaked
    backend/counters from a previous test (module-global state)."""
    monkeypatch.delenv("PP_REDIS_URL", raising=False)
    cache_mod.reset_backend()
    yield
    cache_mod.reset_backend()


# --- in-process backend: TTL expiry -------------------------------------------


def test_in_process_get_returns_none_for_missing_key() -> None:
    backend = cache_mod.InProcessBackend()
    assert backend.get("missing") is None


def test_in_process_ttl_expiry(monkeypatch: pytest.MonkeyPatch) -> None:
    backend = cache_mod.InProcessBackend()
    now = [1_000.0]
    monkeypatch.setattr(cache_mod.time, "monotonic", lambda: now[0])

    backend.set("k", "v", ttl_s=10)
    assert backend.get("k") == "v"

    now[0] += 9.999  # not expired yet
    assert backend.get("k") == "v"

    now[0] += 1  # now past the 10s TTL
    assert backend.get("k") is None


def test_in_process_expired_entry_is_evicted_not_just_hidden(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    backend = cache_mod.InProcessBackend()
    now = [0.0]
    monkeypatch.setattr(cache_mod.time, "monotonic", lambda: now[0])
    backend.set("k", "v", ttl_s=1)
    now[0] = 5.0
    assert backend.get("k") is None
    assert "k" not in backend._store


# --- in-process backend: queue FIFO -------------------------------------------


def test_in_process_queue_is_fifo() -> None:
    backend = cache_mod.InProcessBackend()
    backend.enqueue("pp:alerts", "a")
    backend.enqueue("pp:alerts", "b")
    backend.enqueue("pp:alerts", "c")
    assert backend.dequeue("pp:alerts") == "a"
    assert backend.dequeue("pp:alerts") == "b"
    assert backend.dequeue("pp:alerts") == "c"


def test_dequeue_empty_queue_returns_none() -> None:
    backend = cache_mod.InProcessBackend()
    assert backend.dequeue("nonexistent") is None


def test_queues_are_independent_per_name() -> None:
    backend = cache_mod.InProcessBackend()
    backend.enqueue("q1", "x")
    assert backend.dequeue("q2") is None
    assert backend.dequeue("q1") == "x"


def test_module_level_enqueue_dequeue_roundtrip() -> None:
    cache_mod.enqueue("pp:alerts", {"id": "a1"})
    cache_mod.enqueue("pp:alerts", {"id": "a2"})
    assert cache_mod.dequeue("pp:alerts") == {"id": "a1"}
    assert cache_mod.dequeue("pp:alerts") == {"id": "a2"}
    assert cache_mod.dequeue("pp:alerts") is None


# --- cache_key: sha256(model + payload), stable and collision-resistant ------


def test_cache_key_is_sha256_of_length_prefixed_model_plus_payload() -> None:
    key = cache_mod.cache_key("claude-sonnet-5", "hello")
    assert key == hashlib.sha256(b"15:claude-sonnet-5hello").hexdigest()


def test_cache_key_is_collision_safe_across_model_payload_split() -> None:
    # Without length-prefixing these two would hash identically.
    assert cache_mod.cache_key("ab", "c") != cache_mod.cache_key("a", "bc")


def test_cache_key_is_stable_across_calls() -> None:
    assert cache_mod.cache_key("m", "p") == cache_mod.cache_key("m", "p")


def test_cache_key_differs_by_model() -> None:
    assert cache_mod.cache_key("model-a", "same payload") != cache_mod.cache_key(
        "model-b", "same payload"
    )


def test_cache_key_differs_by_payload() -> None:
    assert cache_mod.cache_key("model", "payload-a") != cache_mod.cache_key("model", "payload-b")


# --- cache_stats: hits/misses ---------------------------------------------------


def test_cache_stats_starts_at_zero() -> None:
    assert cache_mod.cache_stats() == {"hits": 0, "misses": 0}


def test_cache_stats_counts_hits_and_misses() -> None:
    key = cache_mod.cache_key("model", "payload")

    assert cache_mod.cache_get(key) is None  # miss
    assert cache_mod.cache_stats() == {"hits": 0, "misses": 1}

    cache_mod.cache_set(key, "value")
    assert cache_mod.cache_get(key) == "value"  # hit
    assert cache_mod.cache_stats() == {"hits": 1, "misses": 1}


def test_cache_set_default_ttl_is_24h() -> None:
    assert cache_mod.DEFAULT_TTL_S == 86400


# --- fallback on Redis connection failure ---------------------------------------


def test_no_redis_url_uses_in_process_backend() -> None:
    backend = cache_mod._get_backend()
    assert isinstance(backend, cache_mod.InProcessBackend)


def test_fallback_to_in_process_on_redis_connection_error(
    monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
) -> None:
    monkeypatch.setenv("PP_REDIS_URL", "redis://unreachable-host:6379/0")

    class _BoomBackend:
        def __init__(self, url: str) -> None:
            raise ConnectionError("simulated connection failure")

    monkeypatch.setattr(cache_mod, "RedisBackend", _BoomBackend)

    with caplog.at_level(logging.WARNING, logger=cache_mod.logger.name):
        backend = cache_mod._get_backend()

    assert isinstance(backend, cache_mod.InProcessBackend)
    assert any("falling back to in-process" in r.message for r in caplog.records)


def test_fallback_never_crashes_cache_get_or_set(monkeypatch: pytest.MonkeyPatch) -> None:
    """The fixture-first path: even with a bad PP_REDIS_URL, cache_get/cache_set
    must behave like a normal (empty) cache, never raise."""
    monkeypatch.setenv("PP_REDIS_URL", "redis://unreachable-host:6379/0")

    class _BoomBackend:
        def __init__(self, url: str) -> None:
            raise ConnectionError("simulated connection failure")

    monkeypatch.setattr(cache_mod, "RedisBackend", _BoomBackend)

    key = cache_mod.cache_key("model", "payload")
    assert cache_mod.cache_get(key) is None
    cache_mod.cache_set(key, "value")
    assert cache_mod.cache_get(key) == "value"


def test_warning_logged_only_once_per_selection(
    monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
) -> None:
    monkeypatch.setenv("PP_REDIS_URL", "redis://unreachable-host:6379/0")

    class _BoomBackend:
        def __init__(self, url: str) -> None:
            raise ConnectionError("simulated connection failure")

    monkeypatch.setattr(cache_mod, "RedisBackend", _BoomBackend)

    with caplog.at_level(logging.WARNING, logger=cache_mod.logger.name):
        cache_mod._get_backend()  # first selection: falls back + warns
        cache_mod._get_backend()  # backend already cached: no re-warn
        cache_mod._get_backend()

    warnings = [r for r in caplog.records if "falling back to in-process" in r.message]
    assert len(warnings) == 1


def test_get_backend_returns_working_redis_stub_when_construction_succeeds(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Selection success path: PP_REDIS_URL set, construction/ping succeeds ->
    the (redis-shaped) backend is used directly, no fallback."""
    monkeypatch.setenv("PP_REDIS_URL", "redis://stub:6379/0")

    class _StubBackend(cache_mod.RedisBackend):
        def __init__(self, url: str) -> None:
            self.url = url  # skip the real `import redis` + ping

    monkeypatch.setattr(cache_mod, "RedisBackend", _StubBackend)

    backend = cache_mod._get_backend()
    assert isinstance(backend, _StubBackend)
    assert cache_mod._get_backend() is backend  # cached, not re-selected


def test_mid_call_redis_failure_degrades_each_operation(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A backend that connects fine at startup but fails on a later call
    (server restart, network blip) must degrade the same way construction
    failure does: warn, fall back to in-process, and still return an
    in-process-consistent result — never propagate the Redis error."""
    monkeypatch.setenv("PP_REDIS_URL", "redis://stub:6379/0")

    class _FlakyBackend(cache_mod.RedisBackend):
        def __init__(self, url: str) -> None:
            self.url = url

        def get(self, key: str) -> object:
            raise ConnectionError("boom")

        def set(self, key: str, value: object, ttl_s: int) -> None:
            raise ConnectionError("boom")

        def enqueue(self, queue: str, item: object) -> None:
            raise ConnectionError("boom")

        def dequeue(self, queue: str) -> object:
            raise ConnectionError("boom")

    monkeypatch.setattr(cache_mod, "RedisBackend", _FlakyBackend)

    cache_mod.reset_backend()
    assert cache_mod.cache_get("k") is None  # degrades cache_get's own try/except
    assert isinstance(cache_mod._get_backend(), cache_mod.InProcessBackend)

    cache_mod.reset_backend()
    cache_mod.cache_set("k", "v")  # degrades cache_set's own try/except
    assert cache_mod._get_backend().get("k") == "v"

    cache_mod.reset_backend()
    cache_mod.enqueue("q", "item")  # degrades enqueue's own try/except
    assert cache_mod._get_backend().dequeue("q") == "item"

    cache_mod.reset_backend()  # re-arm the flaky backend for the dequeue path
    assert cache_mod.dequeue("q") is None  # degrades dequeue's own try/except


# --- Redis backend: real connection, skipped unless redis is installed AND reachable ---


def test_redis_backend_get_set_and_queue_roundtrip() -> None:
    pytest.importorskip("redis", reason="redis extra not installed (opt-in `cache` extra)")
    try:
        backend = cache_mod.RedisBackend("redis://localhost:6379/0")
    except Exception:
        pytest.skip("no reachable Redis server for this test run")

    backend.set("pp:test:cache-key", {"a": 1}, ttl_s=5)
    assert backend.get("pp:test:cache-key") == {"a": 1}

    backend.enqueue("pp:test:queue", "x")
    assert backend.dequeue("pp:test:queue") == "x"
    assert backend.dequeue("pp:test:queue") is None
