"""Transparent network resilience and critical-infrastructure calculations."""

from __future__ import annotations

from collections.abc import Callable
from datetime import UTC, datetime
from typing import Any

import networkx as nx
from pydantic import BaseModel, ConfigDict, Field, HttpUrl
from pyproj import Transformer
from shapely.geometry import Point, shape
from shapely.ops import transform as transform_geometry

from berlin_urban_intelligence.agents.base import BaseAgent
from berlin_urban_intelligence.scenario_engine.models import Scenario
from berlin_urban_intelligence.shared.contracts import (
    AgentDescriptor,
    AgentHealth,
    AvailabilityStatus,
    CriticalFacility,
    FreshnessStatus,
    NetworkEdge,
    NetworkNode,
    Provenance,
    QualityFlag,
    SpatialReference,
)


class NearestNetworkNode(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    node_id: str = Field(min_length=1)
    longitude: float = Field(ge=-180, le=180)
    latitude: float = Field(ge=-90, le=90)
    distance_m: float = Field(ge=0)
    metric_crs: str = "EPSG:25833"


def nearest_network_node(
    longitude: float,
    latitude: float,
    nodes: list[NetworkNode] | tuple[NetworkNode, ...],
    *,
    metric_crs: str = "EPSG:25833",
) -> NearestNetworkNode:
    if not -180 <= longitude <= 180 or not -90 <= latitude <= 90:
        raise ValueError("longitude/latitude are outside WGS84 bounds")
    if not nodes:
        raise ValueError("network contains no nodes")
    if any(node.longitude is None or node.latitude is None for node in nodes):
        raise ValueError("all network nodes require coordinates for nearest-node lookup")
    transformer = Transformer.from_crs("EPSG:4326", metric_crs, always_xy=True)
    x, y = transformer.transform(longitude, latitude)
    candidates = []
    for candidate_node in nodes:
        if candidate_node.longitude is None or candidate_node.latitude is None:
            raise ValueError("all network nodes require coordinates for nearest-node lookup")
        candidate_x, candidate_y = transformer.transform(
            candidate_node.longitude, candidate_node.latitude
        )
        candidates.append((candidate_node, candidate_x, candidate_y))
    node, node_x, node_y = min(
        candidates, key=lambda candidate: (x - candidate[1]) ** 2 + (y - candidate[2]) ** 2
    )
    distance = float(((x - node_x) ** 2 + (y - node_y) ** 2) ** 0.5)
    if node.longitude is None or node.latitude is None:
        raise ValueError("nearest network node unexpectedly lacks coordinates")
    return NearestNetworkNode(
        node_id=node.id,
        longitude=node.longitude,
        latitude=node.latitude,
        distance_m=distance,
        metric_crs=metric_crs,
    )


class FacilityNetworkLink(BaseModel):
    """Explicit spatial linkage between a critical facility and a road-network node."""

    model_config = ConfigDict(extra="forbid", frozen=True)
    facility_id: str = Field(min_length=1)
    node_id: str = Field(min_length=1)
    distance_m: float = Field(ge=0)
    metric_crs: str = "EPSG:25833"


def snap_facilities_to_network(
    facilities: list[CriticalFacility] | tuple[CriticalFacility, ...],
    nodes: list[NetworkNode] | tuple[NetworkNode, ...],
    *,
    max_distance_m: float = 1000.0,
    metric_crs: str = "EPSG:25833",
) -> list[FacilityNetworkLink]:
    """Snap facilities to their nearest network node using projected metric coordinates.

    Facilities farther than ``max_distance_m`` are deliberately omitted. This avoids silently
    linking a facility to a road node that is geographically implausible.
    """

    if max_distance_m <= 0 or max_distance_m > 50_000:
        raise ValueError("max_distance_m must be greater than zero and at most 50000")
    if not nodes:
        return []
    if any(node.longitude is None or node.latitude is None for node in nodes):
        raise ValueError("all network nodes require coordinates for facility snapping")

    node_transformer = Transformer.from_crs("EPSG:4326", metric_crs, always_xy=True)
    projected_nodes = []
    for network_node in nodes:
        if network_node.longitude is None or network_node.latitude is None:
            raise ValueError("all network nodes require coordinates for facility snapping")
        node_x, node_y = node_transformer.transform(network_node.longitude, network_node.latitude)
        projected_nodes.append((network_node, node_x, node_y))

    links: list[FacilityNetworkLink] = []
    for facility in facilities:
        spatial = facility.spatial
        if spatial is None or spatial.geometry is None:
            continue
        geometry = shape(spatial.geometry)
        transformer = Transformer.from_crs(spatial.crs, metric_crs, always_xy=True)
        projected = transform_geometry(transformer.transform, geometry)
        point = projected if isinstance(projected, Point) else projected.representative_point()
        if not isinstance(point, Point):
            raise ValueError("facility geometry could not be reduced to a point")
        node, x, y = min(
            projected_nodes,
            key=lambda candidate: (point.x - candidate[1]) ** 2 + (point.y - candidate[2]) ** 2,
        )
        distance = float(((point.x - x) ** 2 + (point.y - y) ** 2) ** 0.5)
        if distance <= max_distance_m:
            links.append(
                FacilityNetworkLink(
                    facility_id=facility.id,
                    node_id=node.id,
                    distance_m=distance,
                    metric_crs=metric_crs,
                )
            )
    return sorted(links, key=lambda item: item.facility_id)


class RouteResult(BaseModel):
    model_config = ConfigDict(frozen=True)
    node_path: list[str]
    edge_ids: list[str]
    travel_time_s: float
    scenario_name: str | None = None


class RouteComparison(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    origin: str
    destination: str
    scenario_name: str
    baseline_travel_time_s: float
    scenario_travel_time_s: float
    absolute_delta_s: float
    relative_delta_pct: float
    baseline_node_path: list[str]
    baseline_edge_ids: list[str]
    scenario_node_path: list[str]
    scenario_edge_ids: list[str]


class AccessibilityResult(BaseModel):
    model_config = ConfigDict(frozen=True)
    origin_node: str
    travel_time_budget_s: float = Field(gt=0)
    reachable_facility_ids: list[str]
    unreachable_facility_ids: list[str]


class SnappedAccessibilityResult(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    origin_node: str
    travel_time_budget_s: float = Field(gt=0)
    reachable_facility_ids: list[str]
    unreachable_facility_ids: list[str]
    unsnapped_facility_ids: list[str]
    links: list[FacilityNetworkLink]


class CriticalInfrastructureRegistry:
    """Normalize official Berlin critical-facility GeoJSON without guessing operational status."""

    _NAME_KEYS = ("name", "bezeichnung", "bez", "krankenhaus", "standort", "einrichtung")

    @classmethod
    def _name(cls, properties: dict[str, Any], fallback: str) -> str:
        lowered = {str(key).lower(): value for key, value in properties.items()}
        for key in cls._NAME_KEYS:
            value = lowered.get(key)
            if isinstance(value, str) and value.strip():
                return value.strip()
        return fallback

    def ingest_official_geojson(
        self,
        payload: dict[str, Any],
        *,
        category: str,
        provider: str,
        dataset: str,
        source_url: str,
        licence: str,
        retrieved_at: datetime | None = None,
    ) -> list[CriticalFacility]:
        if payload.get("type") != "FeatureCollection" or not isinstance(
            payload.get("features"), list
        ):
            raise ValueError("critical infrastructure source must be a GeoJSON FeatureCollection")
        retrieved = retrieved_at or datetime.now(UTC)
        if retrieved.tzinfo is None or retrieved.utcoffset() is None:
            raise ValueError("retrieved_at must be timezone-aware")
        facilities: list[CriticalFacility] = []
        for index, raw in enumerate(payload["features"]):
            if not isinstance(raw, dict):
                continue
            geometry = raw.get("geometry")
            if not isinstance(geometry, dict):
                continue
            feature_id = str(raw.get("id") or f"feature-{index}")
            raw_properties = raw.get("properties")
            properties = (
                {str(key): value for key, value in raw_properties.items()}
                if isinstance(raw_properties, dict)
                else {}
            )
            provenance = Provenance(
                provider=provider,
                dataset=dataset,
                source_url=HttpUrl(source_url),
                original_identifier=feature_id,
                retrieved_at=retrieved,
                processed_at=retrieved,
                processing_method="official Berlin WFS GeoJSON normalization",
                agent="resilience",
                agent_version="1.0.0",
                source_licence=licence,
                quality_note=(
                    "Dataset identity/location only; no claim of live operational availability."
                ),
            )
            facilities.append(
                CriticalFacility(
                    id=f"critical:official:{category}:{feature_id}",
                    name=self._name(properties, feature_id),
                    category=category,
                    confidence="official_dataset",
                    quality=QualityFlag.VALID,
                    provenance=provenance,
                    spatial=SpatialReference(crs="EPSG:4326", geometry=geometry),
                    source_identifier=feature_id,
                )
            )
        return facilities


class ResilienceAgent(BaseAgent):
    descriptor = AgentDescriptor(
        id="resilience",
        version="1.0.0",
        description=(
            "Network accessibility and disruption analysis over explicit network/facility inputs."
        ),
        capabilities=(
            "shortest_path",
            "accessibility",
            "scenario_comparison",
            "critical_infrastructure",
        ),
        input_contracts=("NetworkEdge", "CriticalFacility", "Scenario"),
        output_contracts=("RouteResult", "AccessibilityResult", "RouteComparison"),
        source_dependencies=("osm_berlin", "berlin_hospitals", "berlin_fire_stations"),
    )

    def __init__(
        self,
        edges: list[NetworkEdge] | None = None,
        *,
        now_factory: Callable[[], datetime] | None = None,
    ) -> None:
        super().__init__(now_factory=now_factory)
        self._edges = tuple(edges or [])
        self._base_graph = self._build_graph(self._edges)

    @staticmethod
    def _build_graph(
        edges: tuple[NetworkEdge, ...] | list[NetworkEdge],
    ) -> nx.MultiDiGraph[str]:
        graph: nx.MultiDiGraph[str] = nx.MultiDiGraph()
        for edge in edges:
            graph.add_edge(
                edge.source,
                edge.target,
                key=edge.id,
                id=edge.id,
                travel_time_s=edge.travel_time_s,
                length_m=edge.length_m,
            )
            if edge.bidirectional:
                graph.add_edge(
                    edge.target,
                    edge.source,
                    key=edge.id,
                    id=edge.id,
                    travel_time_s=edge.travel_time_s,
                    length_m=edge.length_m,
                )
        return graph

    def _scenario_graph(self, scenario: Scenario | None) -> nx.MultiDiGraph[str]:
        graph = self._base_graph.copy()
        if scenario is None:
            return graph
        closed = set(scenario.closed_network_edges)
        for u, v, key, data in list(graph.edges(keys=True, data=True)):
            edge_id = str(data.get("id"))
            if edge_id in closed:
                graph.remove_edge(u, v, key=key)
                continue
            penalty = scenario.edge_penalties.get(edge_id)
            if penalty is not None:
                data["travel_time_s"] = float(data["travel_time_s"]) * penalty
        return graph

    def shortest_path(
        self, origin: str, destination: str, scenario: Scenario | None = None
    ) -> RouteResult:
        graph = self._scenario_graph(scenario)
        path = nx.shortest_path(graph, origin, destination, weight="travel_time_s")
        edge_ids: list[str] = []
        travel_time = 0.0
        for u, v in zip(path, path[1:], strict=False):
            edge_options = graph.get_edge_data(u, v)
            if not edge_options:
                raise RuntimeError("route path references a missing graph edge")
            _, data = min(
                edge_options.items(),
                key=lambda item: (float(item[1]["travel_time_s"]), str(item[0])),
            )
            edge_ids.append(str(data["id"]))
            travel_time += float(data["travel_time_s"])
        return RouteResult(
            node_path=list(path),
            edge_ids=edge_ids,
            travel_time_s=travel_time,
            scenario_name=scenario.name if scenario else None,
        )

    def compare_route(self, origin: str, destination: str, scenario: Scenario) -> RouteComparison:
        baseline = self.shortest_path(origin, destination)
        disrupted = self.shortest_path(origin, destination, scenario=scenario)
        if baseline.travel_time_s <= 0:
            raise ValueError("route comparison requires distinct origin and destination")
        delta = disrupted.travel_time_s - baseline.travel_time_s
        relative = (delta / baseline.travel_time_s) * 100.0
        return RouteComparison(
            origin=origin,
            destination=destination,
            scenario_name=scenario.name,
            baseline_travel_time_s=baseline.travel_time_s,
            scenario_travel_time_s=disrupted.travel_time_s,
            absolute_delta_s=delta,
            relative_delta_pct=relative,
            baseline_node_path=baseline.node_path,
            baseline_edge_ids=baseline.edge_ids,
            scenario_node_path=disrupted.node_path,
            scenario_edge_ids=disrupted.edge_ids,
        )

    def accessibility(
        self,
        origin: str,
        facilities_by_node: dict[str, CriticalFacility],
        travel_time_budget_s: float,
        scenario: Scenario | None = None,
    ) -> AccessibilityResult:
        graph = self._scenario_graph(scenario)
        lengths = nx.single_source_dijkstra_path_length(
            graph, origin, cutoff=travel_time_budget_s, weight="travel_time_s"
        )
        unavailable = set(scenario.unavailable_facilities if scenario else [])
        reachable: list[str] = []
        unreachable: list[str] = []
        for node, facility in facilities_by_node.items():
            if facility.id in unavailable or node not in lengths:
                unreachable.append(facility.id)
            else:
                reachable.append(facility.id)
        return AccessibilityResult(
            origin_node=origin,
            travel_time_budget_s=travel_time_budget_s,
            reachable_facility_ids=sorted(reachable),
            unreachable_facility_ids=sorted(unreachable),
        )

    def accessibility_links(
        self,
        origin: str,
        facilities: list[CriticalFacility] | tuple[CriticalFacility, ...],
        nodes: list[NetworkNode] | tuple[NetworkNode, ...],
        travel_time_budget_s: float,
        *,
        scenario: Scenario | None = None,
        max_snap_distance_m: float = 1000.0,
    ) -> SnappedAccessibilityResult:
        links = snap_facilities_to_network(facilities, nodes, max_distance_m=max_snap_distance_m)
        by_id = {facility.id: facility for facility in facilities}
        graph = self._scenario_graph(scenario)
        lengths = nx.single_source_dijkstra_path_length(
            graph, origin, cutoff=travel_time_budget_s, weight="travel_time_s"
        )
        unavailable = set(scenario.unavailable_facilities if scenario else [])
        reachable: list[str] = []
        unreachable: list[str] = []
        for link in links:
            facility = by_id[link.facility_id]
            if facility.id in unavailable or link.node_id not in lengths:
                unreachable.append(facility.id)
            else:
                reachable.append(facility.id)
        snapped_ids = {link.facility_id for link in links}
        unsnapped = sorted(facility.id for facility in facilities if facility.id not in snapped_ids)
        return SnappedAccessibilityResult(
            origin_node=origin,
            travel_time_budget_s=travel_time_budget_s,
            reachable_facility_ids=sorted(reachable),
            unreachable_facility_ids=sorted(unreachable),
            unsnapped_facility_ids=unsnapped,
            links=links,
        )

    def health(self) -> AgentHealth:
        if not self._edges:
            return self.unavailable_health("No network snapshot is loaded.")
        return AgentHealth(
            agent_id=self.descriptor.id,
            status=AvailabilityStatus.AVAILABLE,
            checked_at=self.now(),
            freshness=FreshnessStatus.UNKNOWN,
            quality=QualityFlag.VALID,
            detail=(
                f"Network contains {self._base_graph.number_of_nodes()} nodes and "
                f"{self._base_graph.number_of_edges()} directed arcs."
            ),
        )
