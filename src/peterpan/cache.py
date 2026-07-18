"""Cache / queue — Redis-backed with an in-process fallback (ADR-0001).

Two narrow uses, one interface:

1. **Response/embedding cache.** `cache_get`/`cache_set`, keyed by
   `cache_key(model, payload) = sha256((model + payload).encode()).hexdigest()`.
   TTL defaults to 24h. Callers own building `payload` from whatever fully
   determines the cached value (e.g. the exact prompt text sent to the
   model, or the embedding input string) — the key convention lives here,
   the "what goes into the payload" decision lives at the call site.
2. **Async incident intake queue.** `enqueue`/`dequeue`, FIFO per queue name
   (`enqueue` appends, `dequeue` pops from the front — same ordering as
   Redis `LPUSH` + `RPOP`).

Redis is opt-in: set `PP_REDIS_URL` to use it. Unset, or ANY connection
failure (bad URL, unreachable host, auth failure, ...), falls back to an
in-process dict (cache) + deque (queue) behind the same interface, logging
exactly one warning. The fixture-first demo path never depends on a live
Redis instance — this module must never raise for that reason.
"""

from __future__ import annotations

import hashlib
import json
import logging
import time
from abc import ABC, abstractmethod
from collections import deque
from dataclasses import dataclass
from typing import Any

from peterpan.config import Settings

logger = logging.getLogger(__name__)

DEFAULT_TTL_S = 86400  # 24h, per ADR-0001


def cache_key(model: str, payload: str) -> str:
    """The ADR-0001 key convention: sha256(model + payload)."""
    return hashlib.sha256((model + payload).encode("utf-8")).hexdigest()


class CacheBackend(ABC):
    """One interface for both the cache (get/set) and the queue (enqueue/dequeue)."""

    @abstractmethod
    def get(self, key: str) -> Any | None: ...

    @abstractmethod
    def set(self, key: str, value: Any, ttl_s: int) -> None: ...

    @abstractmethod
    def enqueue(self, queue: str, item: Any) -> None: ...

    @abstractmethod
    def dequeue(self, queue: str) -> Any | None: ...


@dataclass
class _Entry:
    value: Any
    expires_at: float


class InProcessBackend(CacheBackend):
    """dict-with-TTL cache + per-queue deque. Default backend — zero external
    services, so the fixture-first demo path always has somewhere to go."""

    def __init__(self) -> None:
        self._store: dict[str, _Entry] = {}
        self._queues: dict[str, deque[Any]] = {}

    def get(self, key: str) -> Any | None:
        entry = self._store.get(key)
        if entry is None:
            return None
        if entry.expires_at <= time.monotonic():
            del self._store[key]
            return None
        return entry.value

    def set(self, key: str, value: Any, ttl_s: int) -> None:
        self._store[key] = _Entry(value=value, expires_at=time.monotonic() + ttl_s)

    def enqueue(self, queue: str, item: Any) -> None:
        self._queues.setdefault(queue, deque()).append(item)

    def dequeue(self, queue: str) -> Any | None:
        q = self._queues.get(queue)
        if not q:
            return None
        return q.popleft()


class RedisBackend(CacheBackend):
    """Redis-backed cache/queue. `redis` is a lazy import behind the optional
    `cache` extra (`pip install -e '.[cache]'`) — importing this module must
    not require it. Construction pings the server so a bad/unreachable
    PP_REDIS_URL fails fast and the caller can fall back."""

    def __init__(self, url: str) -> None:
        import redis  # lazy: optional `cache` extra

        self.url = url
        self._client = redis.Redis.from_url(url, socket_connect_timeout=2, socket_timeout=2)
        self._client.ping()

    def get(self, key: str) -> Any | None:
        raw = self._client.get(key)
        if raw is None:
            return None
        return json.loads(raw)

    def set(self, key: str, value: Any, ttl_s: int) -> None:
        self._client.set(key, json.dumps(value), ex=ttl_s)

    def enqueue(self, queue: str, item: Any) -> None:
        self._client.lpush(queue, json.dumps(item))

    def dequeue(self, queue: str) -> Any | None:
        raw = self._client.rpop(queue)
        if raw is None:
            return None
        return json.loads(raw)


_backend: CacheBackend | None = None
_warned_fallback = False
_hits = 0
_misses = 0


def _warn_fallback(url: str, exc: Exception) -> None:
    """Log the fallback exactly once per process — the connection is almost
    always down for the whole process lifetime once it fails, so repeating
    the warning on every call would just be noise."""
    global _warned_fallback
    if not _warned_fallback:
        logger.warning(
            "PP_REDIS_URL=%s set but Redis is unreachable (%s: %s); "
            "falling back to in-process cache/queue.",
            url,
            type(exc).__name__,
            exc,
        )
        _warned_fallback = True


def _get_backend() -> CacheBackend:
    global _backend
    if _backend is not None:
        return _backend
    url = Settings().redis_url
    if url:
        try:
            _backend = RedisBackend(url)
            return _backend
        except Exception as exc:  # noqa: BLE001 — any connection failure falls back
            _warn_fallback(url, exc)
    _backend = InProcessBackend()
    return _backend


def _degrade(backend: CacheBackend, exc: Exception) -> CacheBackend:
    """A RedisBackend that connected fine at startup can still fail mid-call
    (server restart, network blip). Same contract as construction failure:
    warn once, fall back to in-process, never propagate."""
    global _backend
    url = backend.url if isinstance(backend, RedisBackend) else "<redis>"
    _warn_fallback(url, exc)
    _backend = InProcessBackend()
    return _backend


def cache_get(key: str) -> Any | None:
    """Cache lookup. Every call is counted toward `cache_stats()`."""
    global _hits, _misses
    backend = _get_backend()
    try:
        value = backend.get(key)
    except Exception as exc:  # noqa: BLE001 — degrade, never crash the caller
        value = _degrade(backend, exc).get(key)
    if value is None:
        _misses += 1
    else:
        _hits += 1
    return value


def cache_set(key: str, value: Any, ttl_s: int = DEFAULT_TTL_S) -> None:
    backend = _get_backend()
    try:
        backend.set(key, value, ttl_s)
    except Exception as exc:  # noqa: BLE001
        _degrade(backend, exc).set(key, value, ttl_s)


def enqueue(queue: str, item: Any) -> None:
    backend = _get_backend()
    try:
        backend.enqueue(queue, item)
    except Exception as exc:  # noqa: BLE001
        _degrade(backend, exc).enqueue(queue, item)


def dequeue(queue: str) -> Any | None:
    backend = _get_backend()
    try:
        return backend.dequeue(queue)
    except Exception as exc:  # noqa: BLE001
        return _degrade(backend, exc).dequeue(queue)


def cache_stats() -> dict[str, int]:
    """Countable cache hits/misses — hits never produce a usage-log cost
    entry (the caller skips the priced call entirely on a hit), but they
    still need to be visible somewhere; this is that somewhere."""
    return {"hits": _hits, "misses": _misses}


def reset_backend() -> None:
    """Force re-selection of the backend and zero the counters. Used at
    process start after a config change, and by tests that need isolation
    from this module's process-global state."""
    global _backend, _warned_fallback, _hits, _misses
    _backend = None
    _warned_fallback = False
    _hits = 0
    _misses = 0
