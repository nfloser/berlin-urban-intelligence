from datetime import UTC, datetime

import pytest

from berlin_urban_intelligence.agents.energy import EnergyAgent
from berlin_urban_intelligence.agents.exposure import ExposureAgent
from berlin_urban_intelligence.agents.heat import HeatAgent
from berlin_urban_intelligence.agents.live_state import LiveStateAgent
from berlin_urban_intelligence.agents.mobility import MobilityAgent
from berlin_urban_intelligence.agents.registry import AgentRegistry
from berlin_urban_intelligence.agents.resilience import ResilienceAgent
from berlin_urban_intelligence.orchestrator.engine import (
    OrchestrationRequest,
    Orchestrator,
    WorkflowKind,
)
from berlin_urban_intelligence.shared.contracts import (
    AgentDescriptor,
    AgentHealth,
    AvailabilityStatus,
    FreshnessStatus,
    QualityFlag,
)

NOW = datetime(2026, 9, 15, 12, 0, tzinfo=UTC)


def real_agents():
    return (
        MobilityAgent(now_factory=lambda: NOW),
        ExposureAgent(now_factory=lambda: NOW),
        HeatAgent(now_factory=lambda: NOW),
        EnergyAgent(now_factory=lambda: NOW),
        ResilienceAgent(now_factory=lambda: NOW),
        LiveStateAgent(now_factory=lambda: NOW),
    )


def test_all_real_agents_are_machine_describing() -> None:
    agents = real_agents()
    assert {agent.descriptor.id for agent in agents} == {
        "mobility",
        "exposure",
        "heat",
        "energy",
        "resilience",
        "live_state",
    }

    for agent in agents:
        descriptor = agent.descriptor
        assert descriptor.name
        assert descriptor.domain
        assert descriptor.capabilities
        assert descriptor.input_contracts
        assert descriptor.output_contracts
        if descriptor.id != "live_state":
            assert descriptor.source_dependencies


def test_real_agent_dependency_metadata_is_explicit_and_acyclic() -> None:
    registry = AgentRegistry()
    for agent in real_agents():
        registry.register(agent)

    registry.validate()
    live_state = registry.get("live_state").descriptor
    assert set(live_state.agent_dependencies) == {
        "mobility",
        "exposure",
        "heat",
        "energy",
        "resilience",
    }

    order = [agent.descriptor.id for agent in registry.dependency_order()]
    assert order[-1] == "live_state"
    for dependency in live_state.agent_dependencies:
        assert order.index(dependency) < order.index("live_state")


def test_real_registry_reports_missing_declared_dependency() -> None:
    registry = AgentRegistry()
    for agent in real_agents():
        if agent.descriptor.id != "mobility":
            registry.register(agent)

    with pytest.raises(ValueError, match="missing dependency.*mobility"):
        registry.validate()


def test_live_state_aggregates_typed_health_without_owning_agents() -> None:
    live_state = LiveStateAgent(now_factory=lambda: NOW)
    health = {
        "mobility": AgentHealth(
            agent_id="mobility",
            status=AvailabilityStatus.AVAILABLE,
            checked_at=NOW,
            freshness=FreshnessStatus.VALID,
            quality=QualityFlag.VALID,
        ),
        "heat": AgentHealth(
            agent_id="heat",
            status=AvailabilityStatus.UNAVAILABLE,
            checked_at=NOW,
            freshness=FreshnessStatus.UNAVAILABLE,
            quality=QualityFlag.UNKNOWN,
        ),
    }

    snapshot = live_state.snapshot(health)

    assert snapshot.agents == health
    assert snapshot.overall_status is AvailabilityStatus.DEGRADED
    assert "_agents" not in vars(live_state)


def test_duplicate_real_workflow_capability_is_rejected_as_ambiguous() -> None:
    class DuplicateHeatAgent(HeatAgent):
        descriptor = AgentDescriptor(
            id="duplicate_heat",
            name="Duplicate Heat Agent",
            version="1.0.0",
            domain="heat",
            description="Fixture duplicate capability provider.",
            capabilities=("heat_state",),
            input_contracts=("Observation",),
            output_contracts=("Observation",),
            source_dependencies=("dwd_open_data",),
        )

    registry = AgentRegistry()
    registry.register(HeatAgent(now_factory=lambda: NOW))
    registry.register(DuplicateHeatAgent(now_factory=lambda: NOW))
    registry.register(EnergyAgent(now_factory=lambda: NOW))

    orchestrator = Orchestrator(registry, now_factory=lambda: NOW)
    with pytest.raises(ValueError, match="multiple agents"):
        orchestrator.plan(OrchestrationRequest(workflow=WorkflowKind.HEAT_ENERGY))
