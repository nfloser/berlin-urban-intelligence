"""Live state aggregation agent."""

from __future__ import annotations

from collections.abc import Callable
from datetime import datetime

from pydantic import BaseModel, ConfigDict

from berlin_urban_intelligence.agents.base import BaseAgent
from berlin_urban_intelligence.shared.contracts import (
    AgentDescriptor,
    AgentHealth,
    AvailabilityStatus,
    FreshnessStatus,
    QualityFlag,
)


class LiveStateSnapshot(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    generated_at: datetime
    agents: dict[str, AgentHealth]
    overall_status: AvailabilityStatus
    note: str


class LiveStateAgent(BaseAgent):
    descriptor = AgentDescriptor(
        id="live_state",
        version="0.1.0",
        description="Aggregates agent/source availability without inventing missing domain values.",
        capabilities=("agent_health_snapshot",),
        output_contracts=("LiveStateSnapshot",),
    )

    def __init__(
        self,
        agents: list[BaseAgent] | None = None,
        *,
        now_factory: Callable[[], datetime] | None = None,
    ) -> None:
        super().__init__(now_factory=now_factory)
        self._agents = tuple(agents or [])
        self._last: LiveStateSnapshot | None = None

    def snapshot(self) -> LiveStateSnapshot:
        health = {agent.descriptor.id: agent.health() for agent in self._agents}
        statuses = [item.status for item in health.values()]
        if not statuses:
            overall = AvailabilityStatus.UNKNOWN
        elif all(item == AvailabilityStatus.AVAILABLE for item in statuses):
            overall = AvailabilityStatus.AVAILABLE
        elif any(
            item in {AvailabilityStatus.AVAILABLE, AvailabilityStatus.DEGRADED} for item in statuses
        ):
            overall = AvailabilityStatus.DEGRADED
        else:
            overall = AvailabilityStatus.UNAVAILABLE
        snapshot = LiveStateSnapshot(
            generated_at=self.now(),
            agents=health,
            overall_status=overall,
            note="Overall status summarises availability only; unavailable domains are never replaced with synthetic values.",
        )
        self._last = snapshot
        return snapshot

    def health(self) -> AgentHealth:
        snapshot = self._last or self.snapshot()
        return AgentHealth(
            agent_id=self.descriptor.id,
            status=snapshot.overall_status,
            checked_at=self.now(),
            freshness=FreshnessStatus.UNKNOWN,
            quality=QualityFlag.VALID,
            detail=snapshot.note,
        )
