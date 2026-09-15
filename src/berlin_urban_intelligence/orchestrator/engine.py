"""Deterministic registry-driven workflow planning and execution.

Workflows declare capabilities rather than concrete agent identifiers. The registry resolves those
capabilities to modular agents and preserves declared inter-agent dependency order. Core execution
remains explicit and deterministic; no opaque planner or synthetic replacement data is involved.
"""

from __future__ import annotations

from collections.abc import Callable, Mapping
from datetime import UTC, datetime
from enum import StrEnum

from pydantic import BaseModel, ConfigDict

from berlin_urban_intelligence.agents.base import BaseAgent
from berlin_urban_intelligence.agents.registry import AgentRegistry
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
    required_capabilities: list[str]
    missing_capabilities: list[str]
    requires_llm: bool = False
    note: str


class ExecutionResult(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    workflow: WorkflowKind
    generated_at: datetime
    status: AvailabilityStatus
    agent_health: dict[str, AgentHealth]
    missing_agents: list[str]
    missing_capabilities: list[str]
    requires_llm: bool = False
    note: str


class Orchestrator:
    """Resolve cross-domain workflows from agent capabilities and dependency metadata."""

    _WORKFLOW_CAPABILITIES: dict[WorkflowKind, tuple[str, ...]] = {
        WorkflowKind.URBAN_SNAPSHOT: (
            "mobility_state",
            "exposure_state",
            "heat_state",
            "energy_forecast_contract",
        ),
        WorkflowKind.HEAT_ENERGY: ("heat_state", "energy_forecast_contract"),
        WorkflowKind.MOBILITY_EXPOSURE: ("mobility_state", "exposure_state"),
        WorkflowKind.MOBILITY_RESILIENCE: ("mobility_state", "accessibility"),
        WorkflowKind.HEAT_MOBILITY_RESILIENCE: (
            "heat_state",
            "mobility_state",
            "accessibility",
        ),
    }

    def __init__(
        self,
        agents: Mapping[str, BaseAgent] | AgentRegistry | None = None,
        *,
        now_factory: Callable[[], datetime] | None = None,
    ) -> None:
        if isinstance(agents, AgentRegistry):
            self._registry = agents
        else:
            self._registry = AgentRegistry()
            for agent in (agents or {}).values():
                self._registry.register(agent)
        self._now_factory = now_factory or (lambda: datetime.now(UTC))

    def _resolved_agents(self, workflow: WorkflowKind) -> tuple[list[BaseAgent], list[str]]:
        required = self._WORKFLOW_CAPABILITIES[workflow]
        selected_ids: set[str] = set()
        missing: list[str] = []
        for capability in required:
            agent = self._registry.resolve_capability(capability)
            if agent is None:
                missing.append(capability)
                continue
            selected_ids.add(agent.descriptor.id)

        ordered = [
            agent
            for agent in self._registry.dependency_order()
            if agent.descriptor.id in selected_ids
        ]
        return ordered, missing

    def plan(self, request: OrchestrationRequest) -> ExecutionPlan:
        agents, missing = self._resolved_agents(request.workflow)
        return ExecutionPlan(
            workflow=request.workflow,
            agents=[agent.descriptor.id for agent in agents],
            required_capabilities=list(self._WORKFLOW_CAPABILITIES[request.workflow]),
            missing_capabilities=missing,
            requires_llm=False,
            note=(
                "Deterministic capability resolution through the validated agent registry; "
                "numerical results remain the responsibility of domain agents."
            ),
        )

    def execute(self, request: OrchestrationRequest) -> ExecutionResult:
        now = self._now_factory()
        if now.tzinfo is None or now.utcoffset() is None:
            raise ValueError("now_factory must return a timezone-aware datetime")
        now = now.astimezone(UTC)

        agents, missing_capabilities = self._resolved_agents(request.workflow)
        health = {agent.descriptor.id: agent.health() for agent in agents}
        statuses = [item.status for item in health.values()]
        if missing_capabilities and not statuses:
            overall = AvailabilityStatus.UNAVAILABLE
        elif missing_capabilities:
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
            missing_agents=[],
            missing_capabilities=missing_capabilities,
            requires_llm=False,
            note=(
                "No synthetic replacement values are generated for missing or unavailable domains. "
                "Workflow-specific numerical analysis must be produced by the responsible agents."
            ),
        )
