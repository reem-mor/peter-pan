"""NeMo Guardrails action bindings for this config directory.

Auto-discovered by `nemoguardrails.LLMRails` (it loads `actions.py` from the
config path) — do not rename these functions without updating rails/*.co.
Every action is a thin wrapper around the pure, independently-tested
detection functions in `peterpan.nemo_rails`; this file holds no detection
logic of its own so there is exactly one place (peterpan/nemo_rails.py) that
defines what each rail actually matches.
"""

from __future__ import annotations

from nemoguardrails.actions import action

from peterpan.config import Settings
from peterpan.nemo_rails import (
    detect_fabricated_citation,
    detect_injection,
    detect_secret_leak,
    detect_topical_drift,
    topical_llm_check,
)


@action(name="check_injection_action")
async def check_injection_action(context: dict | None = None) -> bool:
    return detect_injection((context or {}).get("user_message", ""))


@action(name="check_topical_action")
async def check_topical_action(context: dict | None = None) -> bool:
    return detect_topical_drift((context or {}).get("user_message", ""))


@action(name="check_citation_action")
async def check_citation_action(context: dict | None = None) -> bool:
    return detect_fabricated_citation((context or {}).get("bot_message", ""))


@action(name="check_secret_action")
async def check_secret_action(context: dict | None = None) -> bool:
    return detect_secret_leak((context or {}).get("bot_message", ""))


@action(name="check_topical_llm_action")
async def check_topical_llm_action(context: dict | None = None) -> bool:
    # Only ever invoked when guardrails_config/rails/topical.co's flow has
    # been spliced into the active input rails by
    # peterpan.nemo_rails._build_rails — which only happens when
    # Settings.nemo_topical_llm is True. topical_llm_check() itself is also
    # a no-op unless that flag is set, so this stays inert by default even
    # if ever wired in some other way.
    return topical_llm_check((context or {}).get("user_message", ""), Settings())
