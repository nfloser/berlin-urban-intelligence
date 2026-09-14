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
    if any(isinstance(handler.formatter, JsonFormatter) for handler in logger.handlers):
        logger.setLevel(level)
        return
    handler = logging.StreamHandler()
    handler.setFormatter(JsonFormatter())
    logger.addHandler(handler)
    logger.setLevel(level)
    logger.propagate = False
