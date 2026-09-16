"""Structured logging primitives for auditable platform operations."""

from __future__ import annotations

import json
import logging
from collections.abc import Iterator
from contextlib import contextmanager
from datetime import UTC, datetime
from time import perf_counter
from typing import Any
from uuid import uuid4

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
        if record.exc_info and record.exc_info[0] is not None:
            payload["exception_type"] = record.exc_info[0].__name__
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


def structured_log(
    logger: logging.Logger,
    message: str,
    **context: Any,
) -> None:
    """Emit one structured INFO record using the platform context field allow-list.

    Unknown context keys are ignored by :class:`JsonFormatter`, which prevents request bodies,
    query strings or arbitrary external payloads from accidentally entering structured logs.
    Raw exception messages and tracebacks are likewise excluded because provider exceptions may
    contain URLs or other sensitive external context.
    """

    configure_structured_logging()
    safe_context = {key: value for key, value in context.items() if key in _CONTEXT_FIELDS}
    logger.info(message, extra=safe_context)


@contextmanager
def observe_operation(
    logger: logging.Logger,
    event: str,
    *,
    operation_id: str | None = None,
    agent: str | None = None,
    source: str | None = None,
) -> Iterator[str]:
    """Emit exactly one duration/error event for an operation boundary.

    ``event`` is a stable low-cardinality event name. Callers may pass an API operation ID to
    correlate nested work with the request; background work receives an independent UUID. Raw
    exception messages are never copied into structured context. The exception itself is re-raised
    unchanged after the event is emitted so normal failure semantics remain intact.
    """

    correlation_id = operation_id or str(uuid4())
    started = perf_counter()
    error_state: str | None = None
    try:
        yield correlation_id
    except Exception as exc:
        error_state = type(exc).__name__
        raise
    finally:
        structured_log(
            logger,
            event,
            operation_id=correlation_id,
            agent=agent,
            source=source,
            error_state=error_state,
            duration_ms=round((perf_counter() - started) * 1000.0, 3),
        )
