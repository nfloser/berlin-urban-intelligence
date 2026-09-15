"""Live state aggregation over typed health inputs."""

from __future__ import annotations

from collections.abc import Callable, Mapping
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
        name="Live State Agent",
        version="0.1.0",
        domain="cross_domain",
        description="Aggregates typed agent-health state without invoking domain agents directly.",
        capabilities=("agent_health_snapshot",),
        input_contracts=("AgentHealth",),
        output_contracts=("LiveStateSnapshot",),
        agent_dependencies=("mobility", "exposure", "heat", "energy", "resilience"),
    )

    def __init__(
        self,
        *,
        now_factory: Callable[[], datetime] | None = None,
    ) -> None:
        super().__init__(now_factory=now_factory)
        self._last: LiveStateSnapshot | None = None

    def snapshot(self, agent_health: Mapping[str, AgentHealth]) -> LiveStateSnapshot:
        health = dict(agent_health)
        for agent_id, item in health.items():
            if item.agent_id != agent_id:
                raise ValueError(
                    f"agent health key {agent_id!r} does not match payload agent_id {item.agent_id!r}"
                )

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
            note=(
                "Overall status summarises supplied domain-agent availability only; unavailable "
                "domains are never replaced with synthetic values."
            ),
        )
        self._last = snapshot
        return snapshot

    def health(self) -> AgentHealth:
        snapshot = self._last
        if snapshot is None:
            return AgentHealth(
                agent_id=self.descriptor.id,
                status=AvailabilityStatus.UNKNOWN,
                checked_at=self.now(),
                freshness=FreshnessStatus.UNKNOWN,
                quality=QualityFlag.UNKNOWN,
                detail="No composed domain-agent health snapshot has been supplied.",
            )
        return AgentHealth(
            agent_id=self.descriptor.id,
            status=snapshot.overall_status,
            checked_at=self.now(),
            freshness=FreshnessStatus.UNKNOWN,
            quality=QualityFlag.VALID,
            detail=snapshot.note,
        )
