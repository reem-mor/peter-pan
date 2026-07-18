# ADR-0001: Cache / queue — Redis, minimal scope

Status: accepted · Date: 2026-07-18

## Context

The brief (§6.10) requires deciding cache/queue infrastructure before
workstreams depend on it, and forbids unjustified infrastructure. Candidates
considered: Redis (cache and/or queue), n8n-native queueing, Postgres-backed
queue, no new infra.

## Decision

**Redis, two narrow uses; nothing else.**

1. **Response/embedding cache.** Key `sha256(model + input)` →
   embedding vector or LLM completion, TTL 24h. Saves repeat spend during
   demos and eval runs; PETER PAN OS meters the savings (cache hit = no
   `log_usage` cost entry, hits counted separately).
2. **Async incident intake queue.** `LPUSH pp:alerts` on webhook ingest, one
   worker consumes. Keeps the n8n webhook fast and gives the demo a visible
   queue depth metric. n8n-native queueing rejected: intake must also work
   in the fixture path with no n8n running.

Rejected:
- **Celery/RQ full task framework** — one worker loop does not justify a
  framework dependency.
- **Postgres queue** — no Postgres in the fixture stack; adding one for a
  queue is more infra than the queue is worth.

## Fixture-first constraint

Redis is **opt-in** (`PP_REDIS_URL` unset → in-process dict cache + in-process
deque, same interface). The demo path runs with zero external services;
`docker compose` includes a `redis:7-alpine` service for the full stack.

## Consequences

- New module `peterpan/cache.py` exposing `get/set` + `enqueue/dequeue`
  behind one interface with the in-memory fallback (WS11).
- Compose gains a redis service; CI docker-smoke covers it.
- No other component may add infra without a new ADR.
