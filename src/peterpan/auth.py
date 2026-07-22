"""Application-level API authentication for the EC2 mesh.

Opt-in via ``PP_API_TOKEN``. When unset (fixture-first default), routes stay
open so local tests and demos need zero secrets. When set, every request
except ``GET /healthz`` must present matching ``X-PP-Token``.

Never log the token value. Never put it in browser-exposed config — Next.js
BFF / n8n server-side nodes hold it; public clients do not.
"""

from __future__ import annotations

from collections.abc import Awaitable, Callable

from fastapi import Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from peterpan.config import Settings

HEADER = "X-PP-Token"
# Liveness/readiness must stay probeable without credentials (ALB/compose/CW).
_OPEN_PATHS = frozenset({"/healthz", "/docs", "/openapi.json", "/redoc"})


class ApiTokenMiddleware(BaseHTTPMiddleware):
    """Reject unauthenticated mutating/read API calls when a token is configured."""

    def __init__(self, app: object, settings: Settings | None = None) -> None:
        super().__init__(app)  # type: ignore[arg-type]
        self._settings = settings or Settings()

    async def dispatch(
        self,
        request: Request,
        call_next: Callable[[Request], Awaitable[Response]],
    ) -> Response:
        token = self._settings.api_token
        if token is None:
            return await call_next(request)
        path = request.url.path.rstrip("/") or "/"
        if path in _OPEN_PATHS or path.endswith("/healthz"):
            return await call_next(request)
        presented = request.headers.get(HEADER, "")
        expected = token.get_secret_value()
        if not presented or presented != expected:
            return JSONResponse(
                status_code=401,
                content={"error": "unauthorized", "detail": f"missing or invalid {HEADER}"},
            )
        return await call_next(request)


def install_api_auth(app: object, settings: Settings | None = None) -> None:
    """Attach token middleware to a FastAPI app. Idempotent for tests."""
    from fastapi import FastAPI

    if not isinstance(app, FastAPI):
        raise TypeError("install_api_auth expects a FastAPI app")
    app.add_middleware(ApiTokenMiddleware, settings=settings or Settings())
