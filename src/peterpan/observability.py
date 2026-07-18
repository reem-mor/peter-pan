"""Langfuse tracing + structured prompt/completion logging (§6.6).

Opt-in, fixture-first: the demo path never depends on Langfuse being
configured or reachable.

- `LANGFUSE_PUBLIC_KEY` + `LANGFUSE_SECRET_KEY` set: `trace_run` lazy-imports
  `langfuse` (optional `obs` extra, `pip install -e '.[obs]'`) and opens a
  real trace + generation span (input, output, model, tokens, cost).
- Unset (default), or any Langfuse failure: a no-op tracer that still mints
  a uuid4 `trace_id` — `Feedback.trace_id` (schemas.py) must always have
  something to key on, so tracing being off can never remove the id.

Alongside tracing, every LLM call appends one structured JSONL row via
`log_prompt` to `Settings.prompt_log_path` — the "what did we actually
send/receive" trail. `usage.py` stays the "what did it cost" trail; both are
keyed by `trace_id`. Rows never carry raw prompt/completion text: only
sha256 hashes plus a secret-scrubbed `preview` capped at 200 chars. Alert
text (and therefore prompt content) is attacker-controllable input — treat
it as data, never trust it to be leak-free.
"""

from __future__ import annotations

import hashlib
import json
import logging
import re
import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from peterpan.config import Settings

logger = logging.getLogger(__name__)

_PROMPTS_ROOT = Path(__file__).parent.parent.parent / "prompts"
_VERSIONS_PATH = _PROMPTS_ROOT / "versions.yaml"

_PREVIEW_MAX_CHARS = 200

# Simple, deliberately broad secret scrubber. Two shapes get caught:
#  1. "Bearer <token>" — the token has no key=/key: separator of its own, so
#     it needs its own pattern before the general one runs.
#  2. "key=value" / "key: value" — password=, api_key:, token=, etc.
# Not a full secret-scanning dependency; good enough for a 200-char preview.
_BEARER_PATTERN = re.compile(r"(?i)\bbearer\s+\S+")
# Matches bare, quoted (JSON), and compound keys: password=x, "api_key": "y",
# aws_secret_access_key=z. \w* on both sides catches underscore-embedded
# keywords that \b would miss; the optional quotes catch the JSON shape the
# alert payload is serialized in (attacker-controllable text).
_SECRET_PATTERN = re.compile(
    r"(?i)[\"']?\w*(api[_-]?key|secret|token|password|passwd|pwd|authorization)\w*[\"']?"
    r"\s*[:=]\s*[\"']?\S+"
)


def _scrub(text: str) -> str:
    text = _BEARER_PATTERN.sub("bearer=<redacted>", text)
    return _SECRET_PATTERN.sub(lambda m: f"{m.group(1)}=<redacted>", text)


def _preview(*parts: str) -> str:
    """Secret-scrubbed, length-capped preview built from prompt/completion text."""
    combined = " => ".join(p for p in parts if p)
    return _scrub(combined)[:_PREVIEW_MAX_CHARS]


def _sha256(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


# prompts/versions.yaml has a small, fixed two-level shape (see prompts/
# README.md): `surfaces:` then one `  <surface>:` block per surface, each
# with a `    current: <path>` line. A tiny line parser avoids pulling in a
# YAML dependency for a single lookup — this is our own generated file, not
# untrusted input.
_SURFACE_RE = re.compile(r"^ {2}(\S+):\s*$")
_CURRENT_RE = re.compile(r"^ {4}current:\s*(\S+)\s*$")


def prompt_version(surface: str) -> str | None:
    """Current prompt version for a surface, per prompts/versions.yaml.

    Best-effort: a missing file or unknown surface never breaks the
    caller — the prompt log just carries `prompt_version: null`.
    """
    try:
        lines = _VERSIONS_PATH.read_text(encoding="utf-8").splitlines()
    except OSError:
        return None
    in_surface = False
    for line in lines:
        m = _SURFACE_RE.match(line)
        if m:
            in_surface = m.group(1) == surface
            continue
        if in_surface:
            cm = _CURRENT_RE.match(line)
            if cm:
                return cm.group(1)
    return None


@dataclass
class TraceHandle:
    """One LLM call's tracing context. Always has a `trace_id`, tracing
    backend or not — that id is what `Feedback.trace_id` keys against."""

    trace_id: str
    service: str
    model: str
    settings: Settings
    _langfuse_trace: Any | None = field(default=None, repr=False)

    def record(
        self,
        *,
        surface: str,
        system_prompt: str,
        input_text: str,
        output_text: str,
        input_tokens: int,
        output_tokens: int,
        cost_usd: float,
        cached: bool = False,
    ) -> None:
        """Log this call: a Langfuse generation span (if configured) and
        always a structured prompt-log JSONL row. Never raises — a logging
        failure must not take down the LLM call it's describing."""
        if self._langfuse_trace is not None:
            try:
                self._langfuse_trace.generation(
                    name=surface,
                    model=self.model,
                    input=_preview(input_text),
                    output=_preview(output_text),
                    usage={"input": input_tokens, "output": output_tokens},
                    metadata={"cost_usd": cost_usd, "cached": cached},
                )
            except Exception:  # noqa: BLE001 — tracing must never break the caller
                logger.warning("langfuse generation logging failed", exc_info=True)

        try:
            _append_prompt_log(
                self.trace_id,
                service=self.service,
                model=self.model,
                surface=surface,
                system_prompt=system_prompt,
                input_text=input_text,
                output_text=output_text,
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                cost_usd=cost_usd,
                cached=cached,
                path=self.settings.prompt_log_path,
            )
        except Exception:  # noqa: BLE001 — observability is never load-bearing
            logger.warning("prompt-log append failed", exc_info=True)


def _append_prompt_log(
    trace_id: str,
    *,
    service: str,
    model: str,
    surface: str,
    system_prompt: str,
    input_text: str,
    output_text: str,
    input_tokens: int,
    output_tokens: int,
    cost_usd: float,
    cached: bool,
    path: str | Path,
) -> None:
    row = {
        "trace_id": trace_id,
        "ts": datetime.now(UTC).isoformat(),
        "service": service,
        "model": model,
        "prompt_version": prompt_version(surface),
        "system_prompt_sha256": _sha256(system_prompt),
        "completion_sha256": _sha256(output_text),
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
        "cost_usd": cost_usd,
        "cached": cached,
        "preview": _preview(input_text, output_text),
    }
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    with p.open("a", encoding="utf-8") as f:
        f.write(json.dumps(row) + "\n")


def _start_langfuse_trace(service: str, model: str, settings: Settings) -> tuple[str, Any | None]:
    """Best-effort Langfuse trace creation. Any failure (missing package,
    bad credentials, network) degrades to the no-op trace_id path — tracing
    is an observability nicety, never a hard dependency."""
    if not (settings.langfuse_public_key and settings.langfuse_secret_key):
        return str(uuid.uuid4()), None
    try:
        from langfuse import Langfuse  # lazy: optional `obs` extra

        client = Langfuse(
            public_key=settings.langfuse_public_key,
            secret_key=settings.langfuse_secret_key,
            host=settings.langfuse_host or None,
        )
        trace = client.trace(name=service)
        trace_id = str(trace.id) if getattr(trace, "id", None) else str(uuid.uuid4())
        return trace_id, trace
    except Exception:  # noqa: BLE001 — never let observability break the LLM path
        logger.warning("langfuse trace start failed; falling back to no-op tracing", exc_info=True)
        return str(uuid.uuid4()), None


def trace_run(service: str, model: str, settings: Settings) -> TraceHandle:
    """Start a trace for one LLM call. Always returns a usable `TraceHandle`
    — Langfuse-backed when `LANGFUSE_PUBLIC_KEY`/`LANGFUSE_SECRET_KEY` are
    set and reachable, a no-op (but still-uuid'd) handle otherwise."""
    trace_id, langfuse_trace = _start_langfuse_trace(service, model, settings)
    return TraceHandle(
        trace_id=trace_id,
        service=service,
        model=model,
        settings=settings,
        _langfuse_trace=langfuse_trace,
    )


def read_prompt_log(trace_id: str, path: str | Path) -> list[dict[str, Any]]:
    """All prompt-log rows for a trace_id — the query side of the JSONL log."""
    p = Path(path)
    if not p.exists():
        return []
    rows = []
    for line in p.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        try:
            row = json.loads(line)
        except ValueError:
            continue
        if row.get("trace_id") == trace_id:
            rows.append(row)
    return rows
