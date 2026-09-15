"""Verification helpers for real OSM road-network readiness evidence.

This module validates an already acquired canonical road snapshot. It never repairs, imputes or
fabricates network data. Acquisition and optional OSMnx speed imputation remain explicit adapter
concerns; this verifier only proves that the resulting state is internally consistent and routable.
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field

from berlin_urban_intelligence.adapters.osm_network import RoadNetworkSnapshot
from berlin_urban_intelligence.agents.resilience import ResilienceAgent
from berlin_urban_intelligence.shared.contracts import Provenance

_OSM_PROVIDER = "OpenStreetMap contributors"
_OSM_DATASET = "OpenStreetMap road network"
_OSM_LICENCE = "ODbL 1.0"
_IMPUTATION_MARKERS = ("add_edge_speeds", "add_edge_travel_times", "explicitly enabled")


class RoadRouteEvidence(BaseModel):
    """A deterministic baseline route used to prove that the snapshot is routable."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    origin: str = Field(min_length=1)
    destination: str = Field(min_length=1)
    node_path: list[str] = Field(min_length=2)
    edge_ids: list[str] = Field(min_length=1)
    travel_time_s: float = Field(gt=0)


class RoadNetworkReadinessReport(BaseModel):
    """Evidence extracted from one validated real road-network snapshot."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    source_query: str = Field(min_length=1)
    retrieved_at: object
    node_count: int = Field(gt=0)
    edge_count: int = Field(gt=0)
    provider: str = Field(min_length=1)
    source_licence: str = Field(min_length=1)
    speed_imputation_visible: bool
    route: RoadRouteEvidence


def _validate_osm_provenance(resource_id: str, provenance: Provenance | None) -> Provenance:
    if provenance is None:
        raise ValueError(f"road resource {resource_id!r} is missing provenance")
    if provenance.provider != _OSM_PROVIDER:
        raise ValueError(f"road resource {resource_id!r} has unexpected OSM provider")
    if provenance.dataset != _OSM_DATASET:
        raise ValueError(f"road resource {resource_id!r} has unexpected OSM dataset")
    if provenance.source_licence != _OSM_LICENCE:
        raise ValueError(f"road resource {resource_id!r} has unexpected OSM licence")
    if "openstreetmap.org" not in str(provenance.source_url):
        raise ValueError(f"road resource {resource_id!r} has unexpected OSM source URL")
    return provenance


def _imputation_is_visible(provenance: Provenance) -> bool:
    method = provenance.processing_method or ""
    return all(marker in method for marker in _IMPUTATION_MARKERS)


def verify_road_network_snapshot(
    snapshot: RoadNetworkSnapshot,
    *,
    require_speed_imputation_visible: bool = False,
) -> RoadNetworkReadinessReport:
    """Prove canonical OSM consistency and one deterministic baseline route.

    The route endpoints are taken from the lexicographically first non-self edge. This keeps the
    evidence deterministic while guaranteeing that the selected pair has at least the direct edge
    available. The existing :class:`ResilienceAgent` performs the actual shortest-path calculation.
    """

    if not snapshot.nodes or not snapshot.edges:
        raise ValueError("road readiness requires non-empty nodes and edges")

    node_ids = {node.id for node in snapshot.nodes}
    if len(node_ids) != len(snapshot.nodes):
        raise ValueError("road snapshot contains duplicate node identifiers")

    for node in snapshot.nodes:
        if node.longitude is None or node.latitude is None:
            raise ValueError(f"road node {node.id!r} is missing coordinates")
        _validate_osm_provenance(node.id, node.provenance)

    imputation_visible = True
    for edge in snapshot.edges:
        if edge.source not in node_ids:
            raise ValueError(f"road edge {edge.id!r} references unknown source node {edge.source!r}")
        if edge.target not in node_ids:
            raise ValueError(f"road edge {edge.id!r} references unknown target node {edge.target!r}")
        provenance = _validate_osm_provenance(edge.id, edge.provenance)
        imputation_visible = imputation_visible and _imputation_is_visible(provenance)

    if require_speed_imputation_visible and not imputation_visible:
        raise ValueError("speed/travel-time imputation is not provenance-visible on every edge")

    candidate_edges = sorted(
        (edge for edge in snapshot.edges if edge.source != edge.target),
        key=lambda item: item.id,
    )
    if not candidate_edges:
        raise ValueError("road readiness requires at least one non-self edge for baseline routing")

    route_edge = candidate_edges[0]
    route = ResilienceAgent(list(snapshot.edges)).shortest_path(
        route_edge.source,
        route_edge.target,
    )
    if route.travel_time_s <= 0 or not route.edge_ids or len(route.node_path) < 2:
        raise ValueError("baseline road route is not usable")

    first_provenance = _validate_osm_provenance(
        snapshot.nodes[0].id,
        snapshot.nodes[0].provenance,
    )
    return RoadNetworkReadinessReport(
        source_query=snapshot.source_query,
        retrieved_at=snapshot.retrieved_at,
        node_count=len(snapshot.nodes),
        edge_count=len(snapshot.edges),
        provider=first_provenance.provider,
        source_licence=first_provenance.source_licence or _OSM_LICENCE,
        speed_imputation_visible=imputation_visible,
        route=RoadRouteEvidence(
            origin=route_edge.source,
            destination=route_edge.target,
            node_path=route.node_path,
            edge_ids=route.edge_ids,
            travel_time_s=route.travel_time_s,
        ),
    )
