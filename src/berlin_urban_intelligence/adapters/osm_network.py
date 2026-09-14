"""Normalize an OSMnx-produced directed road graph into canonical network contracts.

The normalizer deliberately requires length and travel_time to already exist. It never invents a
speed or travel time when the source/OSMnx processing chain did not provide one.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

import networkx as nx
from pydantic import BaseModel, ConfigDict, HttpUrl

from berlin_urban_intelligence.shared.contracts import NetworkEdge, NetworkNode, Provenance
from berlin_urban_intelligence.shared.temporal import ensure_utc


class RoadNetworkSnapshot(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    retrieved_at: datetime
    source_query: str
    nodes: tuple[NetworkNode, ...]
    edges: tuple[NetworkEdge, ...]
    source_url: str = "https://www.openstreetmap.org/"
    licence: str = "ODbL 1.0"
    attribution: str = "© OpenStreetMap contributors"


def _osmid(value: Any) -> str:
    if isinstance(value, (list, tuple)):
        return "+".join(str(item) for item in value)
    return str(value)


def normalize_osmnx_graph(
    graph: nx.MultiDiGraph[Any],
    *,
    retrieved_at: datetime,
    source_query: str,
    processing_note: str | None = None,
) -> RoadNetworkSnapshot:
    retrieved = ensure_utc(retrieved_at)
    if not source_query.strip():
        raise ValueError("source_query must identify the OSM acquisition scope")
    provenance = Provenance(
        provider="OpenStreetMap contributors",
        dataset="OpenStreetMap road network",
        source_url=HttpUrl("https://www.openstreetmap.org/"),
        retrieved_at=retrieved,
        processed_at=retrieved,
        processing_method=(
            "OSMnx acquisition followed by canonical normalization; edge length and travel_time "
            "must already be present and are not guessed by this normalizer"
            + (f"; {processing_note}" if processing_note else "")
        ),
        agent="resilience",
        agent_version="1.0.0",
        source_licence="ODbL 1.0",
        quality_note="Community-maintained road data; completeness and tags vary by segment.",
    )
    nodes: list[NetworkNode] = []
    for node_id, data in graph.nodes(data=True):
        if "x" not in data or "y" not in data:
            raise ValueError(f"OSM node {node_id} is missing longitude/latitude coordinates")
        nodes.append(
            NetworkNode(
                id=f"osm-node:{node_id}",
                longitude=float(data["x"]),
                latitude=float(data["y"]),
                provenance=provenance,
            )
        )

    edges: list[NetworkEdge] = []
    for source, target, key, data in graph.edges(keys=True, data=True):
        if data.get("travel_time") is None:
            raise ValueError(f"OSM edge {source}->{target}:{key} is missing travel_time")
        if data.get("length") is None:
            raise ValueError(f"OSM edge {source}->{target}:{key} is missing length")
        osm_identifier = _osmid(data.get("osmid", "unknown"))
        edges.append(
            NetworkEdge(
                id=f"osm:{source}:{target}:{key}:{osm_identifier}",
                source=f"osm-node:{source}",
                target=f"osm-node:{target}",
                travel_time_s=float(data["travel_time"]),
                length_m=float(data["length"]),
                # OSMnx MultiDiGraph already represents directionality explicitly.
                bidirectional=False,
                provenance=provenance,
            )
        )
    return RoadNetworkSnapshot(
        retrieved_at=retrieved,
        source_query=source_query,
        nodes=tuple(sorted(nodes, key=lambda item: item.id)),
        edges=tuple(sorted(edges, key=lambda item: item.id)),
    )


class OsmnxRoadNetworkClient:
    """Acquire an OSM road graph and convert it to canonical network contracts.

    OSM edges commonly lack a complete speed field. Speed/travel-time imputation is therefore an
    explicit opt-in, never a silent fallback. When enabled, the provenance records that OSMnx
    derived/imputed speeds before travel-time calculation.
    """

    def __init__(self, *, osmnx_module: Any | None = None) -> None:
        self._osmnx = osmnx_module

    def _module(self) -> Any:
        if self._osmnx is not None:
            return self._osmnx
        try:
            import osmnx as ox
        except ImportError as exc:
            raise RuntimeError(
                "OSM acquisition requires the optional 'osm' dependency: pip install -e '.[osm]'"
            ) from exc
        return ox

    @staticmethod
    def _routing_function(ox: Any, name: str) -> Any:
        routing = getattr(ox, "routing", None)
        function = getattr(routing, name, None) if routing is not None else None
        if function is None:
            function = getattr(ox, name, None)
        if function is None:
            raise RuntimeError(f"installed OSMnx version does not expose {name}")
        return function

    def fetch(
        self,
        place: str,
        *,
        network_type: str = "drive",
        allow_speed_imputation: bool = False,
        retrieved_at: datetime | None = None,
    ) -> RoadNetworkSnapshot:
        if not place.strip():
            raise ValueError("place must not be blank")
        if network_type not in {"drive", "drive_service", "walk", "bike", "all", "all_public"}:
            raise ValueError("unsupported OSMnx network_type")
        ox = self._module()
        graph = ox.graph_from_place(place, network_type=network_type, simplify=True)
        note = None
        if allow_speed_imputation:
            add_speeds = self._routing_function(ox, "add_edge_speeds")
            add_times = self._routing_function(ox, "add_edge_travel_times")
            graph = add_speeds(graph)
            graph = add_times(graph)
            note = (
                "OSMnx add_edge_speeds/add_edge_travel_times explicitly enabled; missing speed "
                "values may be imputed by OSMnx and travel time is therefore derived"
            )
        retrieved = retrieved_at or datetime.now(UTC)
        return normalize_osmnx_graph(
            graph,
            retrieved_at=retrieved,
            source_query=place,
            processing_note=note,
        )
