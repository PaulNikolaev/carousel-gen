"""Middleware: generate request_id (UUID), bind to structlog contextvars, set X-Request-ID on response."""

import uuid

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from structlog import contextvars as structlog_contextvars


class CorrelationIdMiddleware(BaseHTTPMiddleware):
    """Set request_id per request in contextvars and in response header X-Request-ID."""

    async def dispatch(self, request: Request, call_next) -> Response:
        request_id = str(uuid.uuid4())
        structlog_contextvars.clear_contextvars()
        structlog_contextvars.bind_contextvars(request_id=request_id)
        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id
        return response
