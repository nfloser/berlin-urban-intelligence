from datetime import UTC, datetime

import networkx as nx
import pytest

from berlin_urban_intelligence.adapters.osm_network import (
    OsmnxRoadNetworkClient,
    RoadNetworkSnapshot,
)
from berlin_urban_intelligence.runtime.road_readiness import verify_road_network_snapshot
from berlin_urban_intelligence.shared.contracts import NetworkEdge, NetworkNode, Provenance

NOW = datetime(2026, 9, 15, 12, 0, tzinfo=UTC)


def _provenance(*, imputed: bool = True) -> Provenance:
    method = "OSMnx acquisition followed by canonical normalization"
    if imputed:
        method += (
            "; OSMnx add_edge_speeds/add_edge_travel_times explicitly enabled; "
            "missing speed values may be imputed by OSMnx and travel time is therefore derived"
        )
    return Provenance(
        provider="OpenStreetMap contributors",
        dataset="OpenStreetMap road network",
        source_url="https://www.openstreetmap.org/",
        retrieved_at=NOW,
        processed_at=NOW,
        processing_method=method,
        agent="resilience",
        agent_version="1.0.0",
        source_licence="ODbL 1.0",
        quality_note="Community-maintained road data; completeness and tags vary by segment.",
    )


def _snapshot(*, imputed: bool = True) -> RoadNetworkSnapshot:
    provenance = _provenance(imputed=imputed)
    return RoadNetworkSnapshot(
        retrieved_at=NOW,
        source_query="Mitte, Berlin, Germany",
        nodes=(
            NetworkNode(id="osm-node:1", longitude=13.4, latitude=52.5, provenance=provenance),
            NetworkNode(id="osm-node:2", longitude=13.41, latitude=52.51, provenance=provenance),
        ),
        edges=(
            NetworkEdge(
                id="osm:1:2:0:10",
                source="osm-node:1",
                target="osm-node:2",
                travel_time_s=42.0,
                length_m=350.0,
                bidirectional=False,
                provenance=provenance,
            ),
        ),
    )


def test_readiness_report_proves_real_osm_contract_and_baseline_route() -> None:
    report = verify_road_network_snapshot(_snapshot(), require_speed_imputation_visible=True)

    assert report.source_query == "Mitte, Berlin, Germany"
    assert report.node_count == 2
    assert report.edge_count == 1
    assert report.provider == "OpenStreetMap contributors"
    assert report.source_licence == "ODbL 1.0"
    assert report.speed_imputation_visible is True
    assert report.route.origin == "osm-node:1"
    assert report.route.destination == "osm-node:2"
    assert report.route.travel_time_s == 42.0
    assert report.route.edge_ids == ["osm:1:2:0:10"]


def test_readiness_rejects_empty_network() -> None:
    snapshot = RoadNetworkSnapshot(
        retrieved_at=NOW,
        source_query="Mitte, Berlin, Germany",
        nodes=(),
        edges=(),
    )

    with pytest.raises(ValueError, match="non-empty nodes and edges"):
        verify_road_network_snapshot(snapshot)


def test_readiness_rejects_dangling_edge_endpoint() -> None:
    provenance = _provenance()
    snapshot = RoadNetworkSnapshot(
        retrieved_at=NOW,
        source_query="Mitte, Berlin, Germany",
        nodes=(NetworkNode(id="osm-node:1", longitude=13.4, latitude=52.5, provenance=provenance),),
        edges=(
            NetworkEdge(
                id="osm:1:2:0:10",
                source="osm-node:1",
                target="osm-node:2",
                travel_time_s=42.0,
                length_m=350.0,
                bidirectional=False,
                provenance=provenance,
            ),
        ),
    )

    with pytest.raises(ValueError, match="unknown target node"):
        verify_road_network_snapshot(snapshot)


def test_readiness_requires_osm_provenance_and_visible_imputation() -> None:
    snapshot = _snapshot(imputed=False)

    with pytest.raises(ValueError, match="speed/travel-time imputation is not provenance-visible"):
        verify_road_network_snapshot(snapshot, require_speed_imputation_visible=True)

    missing = snapshot.model_copy(
        update={
            "nodes": (
                snapshot.nodes[0].model_copy(update={"provenance": None}),
                snapshot.nodes[1],
            )
        }
    )
    with pytest.raises(ValueError, match="missing provenance"):
        verify_road_network_snapshot(missing)


class _FakeRouting:
    def __init__(self) -> None:
        self.speed_calls = 0
        self.time_calls = 0

    def add_edge_speeds(self, graph: nx.MultiDiGraph[str]) -> nx.MultiDiGraph[str]:
        self.speed_calls += 1
        for _, _, _, data in graph.edges(keys=True, data=True):
            data["speed_kph"] = 30.0
        return graph

    def add_edge_travel_times(self, graph: nx.MultiDiGraph[str]) -> nx.MultiDiGraph[str]:
        self.time_calls += 1
        for _, _, _, data in graph.edges(keys=True, data=True):
            data["travel_time"] = 12.0
        return graph


class _FakeOsmnx:
    def __init__(self) -> None:
        self.routing = _FakeRouting()

    @staticmethod
    def graph_from_place(place: str, *, network_type: str, simplify: bool) -> nx.MultiDiGraph[str]:
        assert place == "Mitte, Berlin, Germany"
        assert network_type == "drive"
        assert simplify is True
        graph: nx.MultiDiGraph[str] = nx.MultiDiGraph()
        graph.add_node("1", x=13.4, y=52.5)
        graph.add_node("2", x=13.41, y=52.51)
        graph.add_edge("1", "2", key=0, length=100.0, osmid=123)
        return graph


def test_osmnx_speed_imputation_remains_explicit_opt_in_and_visible() -> None:
    fake = _FakeOsmnx()
    client = OsmnxRoadNetworkClient(osmnx_module=fake)

    with pytest.raises(ValueError, match="missing travel_time"):
        client.fetch(
            "Mitte, Berlin, Germany",
            allow_speed_imputation=False,
            retrieved_at=NOW,
        )
    assert fake.routing.speed_calls == 0
    assert fake.routing.time_calls == 0

    snapshot = client.fetch(
        "Mitte, Berlin, Germany",
        allow_speed_imputation=True,
        retrieved_at=NOW,
    )

    assert fake.routing.speed_calls == 1
    assert fake.routing.time_calls == 1
    assert snapshot.edges[0].travel_time_s == 12.0
    method = snapshot.edges[0].provenance.processing_method if snapshot.edges[0].provenance else ""
    assert "add_edge_speeds/add_edge_travel_times explicitly enabled" in (method or "")
