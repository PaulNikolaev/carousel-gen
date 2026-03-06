"""Middleware: require X-API-Key header when API_KEY is set. Health path is excluded.

Note: when using the api_key query parameter, the key may appear in server/proxy access logs;
prefer the X-API-Key header when possible.
"""

import hmac

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse

from app.core.config import get_settings


def _is_health_path(path: str) -> bool:
    """True if path is the health check (e.g. /api/v1/health or /health)."""
    p = path.rstrip("/")
    return p.endswith("/health")


class APIKeyMiddleware(BaseHTTPMiddleware):
    """If settings.API_KEY is set, require X-API-Key header (or api_key query param for SSE/EventSource); skip for health path."""

    async def dispatch(self, request: Request, call_next):
        if request.method == "OPTIONS":
            return await call_next(request)

        settings = get_settings()
        expected = settings.API_KEY.get_secret_value()
        if not expected:
            return await call_next(request)

        if _is_health_path(request.url.path):
            return await call_next(request)

        provided_header = request.headers.get("X-API-Key")
        if provided_header:
            if hmac.compare_digest(provided_header, expected):
                return await call_next(request)
        else:
            provided_query = request.query_params.get("api_key")
            if provided_query and hmac.compare_digest(provided_query, expected):
                return await call_next(request)

        return JSONResponse(
            status_code=401,
            content={"detail": "Invalid or missing API key", "code": 401},
        )
