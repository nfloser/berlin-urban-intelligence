from datetime import UTC, datetime

from berlin_urban_intelligence.agents.base import BaseAgent
from berlin_urban_intelligence.agents.registry import AgentRegistry
from berlin_urban_intelligence.orchestrator.engine import (
    OrchestrationRequest,
    Orchestrator,
    WorkflowKind,
)
from berlin_urban_intelligence.shared.contracts import (
    AgentDescriptor,
    AgentHealth,
    AvailabilityStatus,
)


class StubAgent(BaseAgent):
    def __init__(
        self,
        agent_id: str,
        capability: str,
        dependencies: tuple[str, ...] = (),
    ) -> None:
        self.descriptor = AgentDescriptor(
            id=agent_id,
            name=agent_id,
            version="1.0.0",
            domain=agent_id,
            description=agent_id,
            capabilities=(capability,),
            agent_dependencies=dependencies,
        )
        super().__init__(now_factory=lambda: datetime(2026, 9, 15, 8, 0, tzinfo=UTC))

    def health(self) -> AgentHealth:
        return AgentHealth(
            agent_id=self.descriptor.id,
            status=AvailabilityStatus.AVAILABLE,
            checked_at=self.now(),
        )


def registry() -> AgentRegistry:
    result = AgentRegistry()
    result.register(StubAgent("heat", "heat_state"))
    result.register(StubAgent("energy", "energy_forecast_contract"))
    result.register(StubAgent("mobility", "mobility_state"))
    result.register(StubAgent("exposure", "exposure_state"))
    result.register(StubAgent("resilience", "accessibility", ("mobility",)))
    return result


def test_workflow_plan_is_resolved_from_registered_capabilities() -> None:
    orchestrator = Orchestrator(registry())
    plan = orchestrator.plan(OrchestrationRequest(workflow=WorkflowKind.HEAT_ENERGY))
    assert plan.agents == ["heat", "energy"]


def test_dependency_order_is_preserved_for_cross_domain_workflow() -> None:
    orchestrator = Orchestrator(registry())
    plan = orchestrator.plan(OrchestrationRequest(workflow=WorkflowKind.MOBILITY_RESILIENCE))
    assert plan.agents == ["mobility", "resilience"]


def test_missing_capability_is_reported_without_synthetic_agent() -> None:
    incomplete = AgentRegistry()
    incomplete.register(StubAgent("heat", "heat_state"))
    orchestrator = Orchestrator(incomplete)

    result = orchestrator.execute(OrchestrationRequest(workflow=WorkflowKind.HEAT_ENERGY))

    assert result.status is AvailabilityStatus.DEGRADED
    assert result.missing_capabilities == ["energy_forecast_contract"]
    assert result.agent_health["heat"].status is AvailabilityStatus.AVAILABLE
