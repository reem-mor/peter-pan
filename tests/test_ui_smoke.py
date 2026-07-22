"""Streamlit UI smoke — runs the real app headless via streamlit's AppTest.

Requires the `ui` extra; skipped wherever streamlit isn't installed (CI's
test job installs [dev,llm,agents] only — this guards local/full installs
and the release-verification environment, where the demo surface matters).
"""

from __future__ import annotations

from pathlib import Path

import pytest

pytest.importorskip("streamlit.testing.v1")

from streamlit.testing.v1 import AppTest  # noqa: E402

# CWD-independent: AppTest.from_file resolves relative paths against the
# current working directory first, which breaks under IDE test runners.
_APP_PATH = str(Path(__file__).resolve().parents[1] / "ui" / "app.py")


def _run_app() -> AppTest:
    at = AppTest.from_file(_APP_PATH)
    at.run(timeout=30)
    assert not at.exception, f"app raised on boot: {at.exception}"
    return at


def test_app_boots_without_exceptions() -> None:
    _run_app()


def test_draw_tab_exposes_grafana_preview_and_download() -> None:
    at = _run_app()
    draw = next(b for b in at.button if (b.label or "") == "Draw")
    draw.click()
    at.run(timeout=30)
    assert not at.exception, f"Draw raised: {at.exception}"

    rendered = "\n".join(str(m.value) for m in at.markdown)
    assert "Grafana export" in rendered
    assert "import is a human action" in rendered

    # The exporter ran and the validated preview is downloadable. AppTest
    # element coverage varies by streamlit version, so probe defensively —
    # but if download_button is queryable, it must be present and enabled
    # (the fixture alert has no hostile labels).
    try:
        downloads = at.get("download_button")
    except (KeyError, AttributeError):
        downloads = []
    if downloads:
        # Present AND enabled — the download gate binds to the deterministic
        # validator (disabled=not preview.validated); an inversion typo in
        # ui/app.py must fail here.
        assert any("Grafana" in (d.label or "") and not d.disabled for d in downloads)
