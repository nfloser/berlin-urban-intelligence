"""Common agent interface with an injectable, timezone-aware clock."""

from abc import ABC, abstractmethod
from collections.abc import Callable
from datetime import UTC, datetime

from berlin_urban_intelligence.shared.contracts import (
    AgentDescriptor,
    AgentHealth,
    AvailabilityStatus,
    FreshnessStatus,
    QualityFlag,
)


class BaseAgent(ABC):
    descriptor: AgentDescriptor

    def __init__(self, *, now_factory: Callable[[], datetime] | None = None) -> None:
        self._now_factory = now_factory or (lambda: datetime.now(UTC))

    def now(self) -> datetime:
        value = self._now_factory()
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("agent clock must return a timezone-aware datetime")
        return value.astimezone(UTC)

    @abstractmethod
    def health(self) -> AgentHealth:
        raise NotImplementedError

    def unavailable_health(self, detail: str) -> AgentHealth:
        return AgentHealth(
            agent_id=self.descriptor.id,
            status=AvailabilityStatus.UNAVAILABLE,
            checked_at=self.now(),
            freshness=FreshnessStatus.UNAVAILABLE,
            quality=QualityFlag.UNKNOWN,
            detail=detail,
        )
