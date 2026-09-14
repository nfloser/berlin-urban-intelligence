"""Deterministic workflow planning and execution for cross-domain requests."""

from __future__ import annotations

from collections.abc import Callable, Mapping
from datetime import UTC, datetime
from enum import StrEnum

from pydantic import BaseModel, ConfigDict

from berlin_urban_intelligence.agents.base import BaseAgent
from berlin_urban_intelligence.shared.contracts import AgentHealth, AvailabilityStatus


class WorkflowKind(StrEnum):
    URBAN_SNAPSHOT = "urban_snapshot"
    HEAT_ENERGY = "heat_energy"
    MOBILITY_EXPOSURE = "mobility_exposure"
    MOBILITY_RESILIENCE = "mobility_resilience"
    HEAT_MOBILITY_RESILIENCE = "heat_mobility_resilience"


class OrchestrationRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    workflow: WorkflowKind


class ExecutionPlan(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    workflow: WorkflowKind
    agents: list[str]
    requires_llm: bool = False
    note: str


class ExecutionResult(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    workflow: WorkflowKind
    generated_at: datetime
    status: AvailabilityStatus
    agent_health: dict[str, AgentHealth]
    missing_agents: list[str]
    requires_llm: bool = False
    note: str


class Orchestrator:
    _PLANS: dict[WorkflowKind, list[str]] = {
        WorkflowKind.URBAN_SNAPSHOT: ["live_state", "mobility", "exposure", "heat", "energy"],
        WorkflowKind.HEAT_ENERGY: ["live_state", "heat", "energy"],
        WorkflowKind.MOBILITY_EXPOSURE: ["live_state", "mobility", "exposure"],
        WorkflowKind.MOBILITY_RESILIENCE: ["live_state", "mobility", "resilience"],
        WorkflowKind.HEAT_MOBILITY_RESILIENCE: ["live_state", "heat", "mobility", "resilience"],
    }

    def __init__(
        self,
        agents: Mapping[str, BaseAgent] | None = None,
        *,
        now_factory: Callable[[], datetime] | None = None,
    ) -> None:
        self._agents = dict(agents or {})
        self._now_factory = now_factory or (lambda: datetime.now(UTC))

    def plan(self, request: OrchestrationRequest) -> ExecutionPlan:
        agents = self._PLANS[request.workflow]
        return ExecutionPlan(
            workflow=request.workflow,
            agents=list(agents),
            requires_llm=False,
            note="Deterministic agent routing; numerical results must come from domain agents.",
        )

    def execute(self, request: OrchestrationRequest) -> ExecutionResult:
        now = self._now_factory()
        if now.tzinfo is None or now.utcoffset() is None:
            raise ValueError("now_factory must return a timezone-aware datetime")
        now = now.astimezone(UTC)

        requested = [agent for agent in self._PLANS[request.workflow] if agent != "live_state"]
        health: dict[str, AgentHealth] = {}
        missing: list[str] = []
        for agent_id in requested:
            agent = self._agents.get(agent_id)
            if agent is None:
                missing.append(agent_id)
                continue
            health[agent_id] = agent.health()

        statuses = [item.status for item in health.values()]
        if missing and not statuses:
            overall = AvailabilityStatus.UNAVAILABLE
        elif missing:
            overall = AvailabilityStatus.DEGRADED
        elif statuses and all(item == AvailabilityStatus.AVAILABLE for item in statuses):
            overall = AvailabilityStatus.AVAILABLE
        elif any(
            item in {AvailabilityStatus.AVAILABLE, AvailabilityStatus.DEGRADED} for item in statuses
        ):
            overall = AvailabilityStatus.DEGRADED
        else:
            overall = AvailabilityStatus.UNAVAILABLE

        return ExecutionResult(
            workflow=request.workflow,
            generated_at=now,
            status=overall,
            agent_health=health,
            missing_agents=missing,
            requires_llm=False,
            note=(
                "No synthetic replacement values are generated for missing or unavailable domains. "
                "Workflow-specific numerical analysis must be produced by the responsible agents."
            ),
        )
