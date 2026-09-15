from __future__ import annotations

from datetime import UTC, datetime

import networkx as nx

from berlin_urban_intelligence.adapters.osm_network import OsmnxRoadNetworkClient

NOW = datetime(2026, 9, 15, 12, 0, tzinfo=UTC)


class _FakeSettings:
    overpass_url = "https://overpass-api.de/api"


class _FakeRouting:
    @staticmethod
    def add_edge_speeds(graph: nx.MultiDiGraph[str]) -> nx.MultiDiGraph[str]:
        for _, _, _, data in graph.edges(keys=True, data=True):
            data["speed_kph"] = 30.0
        return graph

    @staticmethod
    def add_edge_travel_times(graph: nx.MultiDiGraph[str]) -> nx.MultiDiGraph[str]:
        for _, _, _, data in graph.edges(keys=True, data=True):
            data["travel_time"] = 12.0
        return graph


class _FakeOsmnx:
    def __init__(self) -> None:
        self.settings = _FakeSettings()
        self.routing = _FakeRouting()
        self.endpoint_seen_during_fetch: str | None = None

    def graph_from_place(
        self, place: str, *, network_type: str, simplify: bool
    ) -> nx.MultiDiGraph[str]:
        assert place == "Mitte, Berlin, Germany"
        assert network_type == "drive"
        assert simplify is True
        self.endpoint_seen_during_fetch = self.settings.overpass_url
        graph: nx.MultiDiGraph[str] = nx.MultiDiGraph()
        graph.add_node("1", x=13.4, y=52.5)
        graph.add_node("2", x=13.41, y=52.51)
        graph.add_edge("1", "2", key=0, length=100.0, osmid=123)
        return graph


def test_explicit_overpass_endpoint_is_scoped_to_fetch_and_provenance_visible() -> None:
    fake = _FakeOsmnx()
    client = OsmnxRoadNetworkClient(
        osmnx_module=fake,
        overpass_url="https://overpass.private.coffee/api",
    )

    snapshot = client.fetch(
        "Mitte, Berlin, Germany",
        allow_speed_imputation=True,
        retrieved_at=NOW,
    )

    assert fake.endpoint_seen_during_fetch == "https://overpass.private.coffee/api"
    assert fake.settings.overpass_url == "https://overpass-api.de/api"
    provenance = snapshot.edges[0].provenance
    assert provenance is not None
    assert "Overpass delivery endpoint https://overpass.private.coffee/api" in (
        provenance.processing_method or ""
    )


def test_default_client_does_not_override_osmnx_endpoint() -> None:
    fake = _FakeOsmnx()
    client = OsmnxRoadNetworkClient(osmnx_module=fake)

    client.fetch(
        "Mitte, Berlin, Germany",
        allow_speed_imputation=True,
        retrieved_at=NOW,
    )

    assert fake.endpoint_seen_during_fetch == "https://overpass-api.de/api"
    assert fake.settings.overpass_url == "https://overpass-api.de/api"
