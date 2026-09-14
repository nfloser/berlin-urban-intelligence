from berlin_urban_intelligence.agents.resilience import ResilienceAgent
from berlin_urban_intelligence.scenario_engine.models import Scenario, ScenarioKind
from berlin_urban_intelligence.shared.contracts import NetworkEdge


def edge(edge_id: str, source: str, target: str, travel_time_s: float) -> NetworkEdge:
    return NetworkEdge(
        id=edge_id,
        source=source,
        target=target,
        length_m=100.0,
        travel_time_s=travel_time_s,
        bidirectional=False,
    )


def test_parallel_edges_are_not_overwritten() -> None:
    agent = ResilienceAgent(
        [
            edge("fixture:slow", "a", "b", 20.0),
            edge("fixture:fast", "a", "b", 5.0),
            edge("fixture:bc", "b", "c", 5.0),
            edge("fixture:ac", "a", "c", 30.0),
        ]
    )
    route = agent.shortest_path("a", "c")
    assert route.edge_ids == ["fixture:fast", "fixture:bc"]
    assert route.travel_time_s == 10.0


def test_closure_changes_scenario_graph_without_mutating_baseline() -> None:
    agent = ResilienceAgent(
        [
            edge("fixture:ab", "a", "b", 5.0),
            edge("fixture:bc", "b", "c", 5.0),
            edge("fixture:ac", "a", "c", 30.0),
        ]
    )
    scenario = Scenario(
        name="fixture-closure",
        kinds={ScenarioKind.NETWORK_DISRUPTION},
        closed_network_edges=["fixture:bc"],
    )
    comparison = agent.compare_route("a", "c", scenario)
    assert comparison.baseline_travel_time_s == 10.0
    assert comparison.scenario_travel_time_s == 30.0
    assert agent.shortest_path("a", "c").travel_time_s == 10.0
