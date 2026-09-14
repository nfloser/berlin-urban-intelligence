"""Structured logging primitives for auditable platform operations."""

from __future__ import annotations

import json
import logging
from datetime import UTC, datetime
from typing import Any

_CONTEXT_FIELDS = (
    "operation_id",
    "agent",
    "source",
    "error_state",
    "duration_ms",
    "http_method",
    "http_path",
    "http_status",
)


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, Any] = {
            "timestamp": datetime.now(UTC).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        for field in _CONTEXT_FIELDS:
            value = getattr(record, field, None)
            if value is not None:
                payload[field] = value
        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)
        return json.dumps(payload, ensure_ascii=False, separators=(",", ":"), default=str)


def configure_structured_logging(level: int = logging.INFO) -> None:
    logger = logging.getLogger("berlin_urban_intelligence")
    if any(getattr(handler, "_bui_structured", False) for handler in logger.handlers):
        logger.setLevel(level)
        return
    handler = logging.StreamHandler()
    handler.setFormatter(JsonFormatter())
    handler._bui_structured = True
    logger.addHandler(handler)
    logger.setLevel(level)
    logger.propagate = False


def structured_log(
    logger: logging.Logger,
    message: str,
    **context: Any,
) -> None:
    """Emit one structured INFO record using the platform context field allow-list.

    Unknown context keys are ignored by :class:`JsonFormatter`, which prevents request bodies,
    query strings or arbitrary external payloads from accidentally entering structured logs.
    """

    configure_structured_logging()
    safe_context = {key: value for key, value in context.items() if key in _CONTEXT_FIELDS}
    logger.info(message, extra=safe_context)
