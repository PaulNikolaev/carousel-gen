"""Structlog configuration: JSON to stdout with timestamp, level, service, contextvars."""

import sys

import structlog
from structlog.contextvars import merge_contextvars
from structlog.processors import (
    JSONRenderer,
    add_log_level,
)
from structlog.typing import Processor

SERVICE_NAME = "backend"


def _add_service(_: object, __: str, event_dict: dict) -> dict:
    event_dict["service"] = SERVICE_NAME
    return event_dict


def configure_structlog() -> None:
    """Configure structlog for JSON output to stdout with timestamp, level, service, request_id."""
    shared_processors: list[Processor] = [
        merge_contextvars,
        add_log_level,
        structlog.processors.TimeStamper(fmt="iso", utc=True),
        _add_service,
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        JSONRenderer(),
    ]
    structlog.configure(
        processors=shared_processors,
        wrapper_class=structlog.BoundLogger,
        context_class=dict,
        logger_factory=structlog.PrintLoggerFactory(file=sys.stdout),
        cache_logger_on_first_use=True,
    )
