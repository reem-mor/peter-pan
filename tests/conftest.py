"""Pytest process bootstrap for the fixture-first path.

A developer ``.env`` may set ``PP_API_TOKEN`` for the EC2/demo mesh. Service
modules build ``Settings()`` at import time, so that token would 401 the
entire API suite. Empty-string overrides ``.env`` (see
``Settings._empty_api_token_is_none``) and keeps auth open for tests.
``test_api_auth.py`` still installs its own tokenized apps explicitly.
"""

from __future__ import annotations

import os

# Must run before test modules import peterpan.services.* (module-level Settings).
os.environ["PP_API_TOKEN"] = ""
