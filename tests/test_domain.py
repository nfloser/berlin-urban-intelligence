from datetime import UTC, datetime, timedelta

import networkx as nx
import pytest
from pydantic import ValidationError
from rdflib import Graph

from berlin_urban_intelligence.agents.resilience import ResilienceAgent
from berlin_urban_intelligence.knowledge.graph import KnowledgeGraph
from berlin_urban_intelligence.scenario_engine.models import Scenario
from berlin_urban_intelligence.shared.contracts import NetworkEdge, Observation, Provenance

NOW = datetime(2026, 1, 1, tzinfo=UTC)


def observation(**changes):
    data = dict(
        id="station:one",
        entity_id="station:a",
        phenomenon="air_temperature_2m",
        value=20.0,
        unit="Cel",
        observed_at=NOW,
        state="observed",
        quality="valid",
        provenance=Provenance(
            provider="DWD Berlin",
            dataset="Weather / now",
            source_url="https://example.org/weather",
            retrieved_at=NOW,
            processed_at=NOW,
            agent="heat",
            agent_version="1",
        ),
    )
    return Observation(**(data | changes))


def test_rdf_roundtrip_with_human_readable_provider_names():
    graph = KnowledgeGraph()
    graph.add_observation(observation())
    serialized = graph.serialize()
    restored = Graph().parse(data=serialized, format="turtle")
    assert len(restored) == len(graph.graph)


@pytest.mark.parametrize("value", [float("nan"), float("inf"), -float("inf")])
def test_nonfinite_measurements_rejected(value):
    with pytest.raises(ValidationError):
        observation(value=value)


def test_numeric_units_and_utc_are_required():
    with pytest.raises(ValidationError):
        observation(unit=None)
    with pytest.raises(ValidationError):
        observation(observed_at=datetime(2026, 1, 1))


def test_immutable_network_overlay_and_disconnection():
    agent = ResilienceAgent(
        [
            NetworkEdge(id="ab", source="a", target="b", travel_time_s=10, length_m=50),
            NetworkEdge(id="bc", source="b", target="c", travel_time_s=10, length_m=50),
            NetworkEdge(id="ac", source="a", target="c", travel_time_s=30, length_m=100),
        ]
    )
    scenario = Scenario(name="closure", kinds={"network_disruption"}, closed_network_edges=["bc"])
    assert agent.shortest_path("a", "c").travel_time_s == 20
    assert agent.shortest_path("a", "c", scenario).travel_time_s == 30
    assert agent.shortest_path("a", "c").travel_time_s == 20
    disconnected = Scenario(
        name="cut", kinds={"network_disruption"}, closed_network_edges=["ab", "ac"]
    )
    with pytest.raises(nx.NetworkXNoPath):
        agent.shortest_path("a", "c", disconnected)


def test_stale_baseline_is_not_used_as_current_scenario():
    from berlin_urban_intelligence.agents.energy import EnergyAgent
    from berlin_urban_intelligence.agents.heat import HeatAgent
    from berlin_urban_intelligence.orchestrator.assessment import (
        AssessmentRequest,
        IntegratedAssessmentService,
    )

    def now():
        return NOW + timedelta(days=2)

    service = IntegratedAssessmentService(
        heat=HeatAgent([observation()], now_factory=now),
        energy=EnergyAgent(now_factory=now),
        resilience=ResilienceAgent(now_factory=now),
        now_factory=now,
    )
    result = service.assess(
        AssessmentRequest(
            scenario=Scenario(name="hot", kinds={"extreme_heat"}, temperature_delta_c=3)
        )
    )
    assert result.heat is None
    assert "heat" in result.unavailable_dimensions
