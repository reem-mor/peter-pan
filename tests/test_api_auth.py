"""Application-level X-PP-Token auth — open when unset, 401 when set."""

from __future__ import annotations

from fastapi import FastAPI
from fastapi.testclient import TestClient
from pydantic import SecretStr

from peterpan.auth import HEADER, install_api_auth
from peterpan.config import Settings


def _app(token: str | None) -> FastAPI:
    app = FastAPI()
    settings = Settings(api_token=SecretStr(token) if token else None)
    install_api_auth(app, settings)

    @app.get("/healthz")
    def healthz() -> dict[str, str]:
        return {"status": "ok"}

    @app.get("/secret-data")
    def secret_data() -> dict[str, str]:
        return {"ok": "yes"}

    return app


def test_auth_disabled_when_token_unset() -> None:
    client = TestClient(_app(None))
    assert client.get("/secret-data").status_code == 200
    assert client.get("/healthz").status_code == 200


def test_auth_rejects_missing_and_wrong_token() -> None:
    client = TestClient(_app("correct-token"))
    assert client.get("/healthz").status_code == 200  # probes stay open
    assert client.get("/secret-data").status_code == 401
    assert client.get("/secret-data", headers={HEADER: "wrong"}).status_code == 401


def test_auth_accepts_matching_token() -> None:
    client = TestClient(_app("correct-token"))
    resp = client.get("/secret-data", headers={HEADER: "correct-token"})
    assert resp.status_code == 200
    assert resp.json()["ok"] == "yes"
