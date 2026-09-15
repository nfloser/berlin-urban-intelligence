from datetime import UTC, datetime

import pytest

from berlin_urban_intelligence.agents.base import BaseAgent
from berlin_urban_intelligence.agents.registry import AgentRegistry
from berlin_urban_intelligence.shared.contracts import (
    AgentDescriptor,
    AgentHealth,
    AvailabilityStatus,
)

NOW = datetime(2026, 9, 15, 12, 0, tzinfo=UTC)


class CapabilityAgent(BaseAgent):
    def __init__(self, agent_id: str, capability: str) -> None:
        self.descriptor = AgentDescriptor(
            id=agent_id,
            name=agent_id,
            version="1.0.0",
            domain="fixture",
            description="Capability resolution fixture.",
            capabilities=(capability,),
            input_contracts=("FixtureInput",),
            output_contracts=("FixtureOutput",),
        )
        super().__init__(now_factory=lambda: NOW)

    def health(self) -> AgentHealth:
        return AgentHealth(
            agent_id=self.descriptor.id,
            status=AvailabilityStatus.AVAILABLE,
            checked_at=self.now(),
        )


def test_registry_resolves_unique_capability() -> None:
    registry = AgentRegistry()
    heat = CapabilityAgent("heat", "heat_state")
    registry.register(heat)

    assert registry.resolve_capability("heat_state") is heat
    assert registry.resolve_capability("missing") is None


def test_registry_rejects_ambiguous_capability() -> None:
    registry = AgentRegistry()
    registry.register(CapabilityAgent("heat_a", "heat_state"))
    registry.register(CapabilityAgent("heat_b", "heat_state"))

    with pytest.raises(ValueError, match="multiple agents.*heat_a.*heat_b"):
        registry.resolve_capability("heat_state")
