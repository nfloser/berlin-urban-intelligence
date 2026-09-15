from datetime import UTC, datetime

import pytest

from berlin_urban_intelligence.agents.base import BaseAgent
from berlin_urban_intelligence.agents.registry import AgentRegistry
from berlin_urban_intelligence.shared.contracts import (
    AgentDescriptor,
    AgentHealth,
    AvailabilityStatus,
)


class StubAgent(BaseAgent):
    def __init__(self, agent_id: str, dependencies: tuple[str, ...] = ()) -> None:
        self.descriptor = AgentDescriptor(
            id=agent_id,
            name=agent_id.replace("_", " ").title(),
            version="1.0.0",
            domain=agent_id,
            description=f"Fixture {agent_id}",
            capabilities=(agent_id,),
            agent_dependencies=dependencies,
        )
        super().__init__(now_factory=lambda: datetime(2026, 9, 15, 8, 0, tzinfo=UTC))

    def health(self) -> AgentHealth:
        return AgentHealth(
            agent_id=self.descriptor.id,
            status=AvailabilityStatus.AVAILABLE,
            checked_at=self.now(),
        )


def test_registry_resolves_agents_in_dependency_order() -> None:
    registry = AgentRegistry()
    registry.register(StubAgent("heat"))
    registry.register(StubAgent("exposure", ("heat",)))
    registry.register(StubAgent("resilience", ("exposure",)))

    assert tuple(agent.descriptor.id for agent in registry.dependency_order()) == (
        "heat",
        "exposure",
        "resilience",
    )


def test_registry_rejects_duplicate_identifiers() -> None:
    registry = AgentRegistry()
    registry.register(StubAgent("heat"))
    with pytest.raises(ValueError, match="already registered"):
        registry.register(StubAgent("heat"))


def test_registry_reports_missing_agent_dependencies() -> None:
    registry = AgentRegistry()
    registry.register(StubAgent("exposure", ("heat",)))
    with pytest.raises(ValueError, match="missing dependency.*heat"):
        registry.validate()


def test_registry_rejects_dependency_cycles() -> None:
    registry = AgentRegistry()
    registry.register(StubAgent("heat", ("exposure",)))
    registry.register(StubAgent("exposure", ("heat",)))
    with pytest.raises(ValueError, match="cycle"):
        registry.validate()
