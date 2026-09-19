"""Cached, source-backed monitoring routes between Berlin critical facilities."""

from __future__ import annotations

from collections.abc import Callable
from datetime import UTC, datetime
from typing import Literal, cast

import networkx as nx
from pydantic import BaseModel, ConfigDict, Field
from pyproj import Transformer
from shapely.geometry import LineString, shape
from shapely.ops import transform as shapely_transform

from berlin_urban_intelligence.agents.resilience import snap_facilities_to_network
from berlin_urban_intelligence.runtime.reference import ReferenceState
from berlin_urban_intelligence.runtime.traffic_disruptions import (
    TrafficDisruption,
    TrafficDisruptionState,
)
from berlin_urban_intelligence.shared.contracts import (
    AvailabilityStatus,
    CriticalFacility,
    FreshnessStatus,
    NetworkEdge,
    NetworkNode,
    QualityFlag,
)


_TO_METRIC = Transformer.from_crs("EPSG:4326", "EPSG:25833", always_xy=True).transform


class CriticalRouteProvenance(BaseModel):
    """Compact provenance for a derived monitored route."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    reference_generated_at: datetime
    computed_at: datetime
    source_providers: tuple[str, ...] = ()
    source_datasets: tuple[str, ...] = ()
    source_licences: tuple[str, ...] = ()
    processing_method: str = (
        "nearest cross-category critical-facility route over persisted weighted road network"
    )
    traffic_data_available: Literal[False] = False
    disruption_source_providers: tuple[str, ...] = ()
    disruption_source_licences: tuple[str, ...] = ()


class CriticalRoute(BaseModel):
    """One automatically monitored critical-facility connection."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    id: str = Field(min_length=1)
    origin_facility_id: str = Field(min_length=1)
    origin_name: str = Field(min_length=1)
    origin_category: str = Field(min_length=1)
    destination_facility_id: str = Field(min_length=1)
    destination_name: str = Field(min_length=1)
    destination_category: str = Field(min_length=1)
    travel_time_s: float = Field(gt=0)
    length_m: float = Field(gt=0)
    node_path: tuple[str, ...]
    edge_ids: tuple[str, ...]
    geometry: dict[str, object]
    quality: QualityFlag
    freshness: FreshnessStatus = FreshnessStatus.UNKNOWN
    route_state: Literal["baseline", "disrupted", "rerouted", "blocked"] = "baseline"
    active_disruption_ids: tuple[str, ...] = ()
    closed_edge_ids: tuple[str, ...] = ()
    disruption_aware_travel_time_s: float | None = None
    disruption_aware_length_m: float | None = None
    disruption_aware_node_path: tuple[str, ...] = ()
    disruption_aware_edge_ids: tuple[str, ...] = ()
    disruption_aware_geometry: dict[str, object] | None = None
    travel_time_delta_s: float | None = None
    provenance: CriticalRouteProvenance


class CriticalRouteSnapshot(BaseModel):
    """Reference-snapshot-bound route monitor result."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    computed_at: datetime
    reference_generated_at: datetime | None
    status: AvailabilityStatus
    freshness: FreshnessStatus = FreshnessStatus.UNKNOWN
    quality: QualityFlag
    routes: tuple[CriticalRoute, ...] = ()
    unsnapped_facility_ids: tuple[str, ...] = ()
    unreachable_facility_ids: tuple[str, ...] = ()
    source_errors: dict[str, str] = Field(default_factory=dict)
    traffic_data_available: Literal[False] = False
    disruption_data_available: bool = False
    disruption_generated_at: datetime | None = None
    disruption_freshness: FreshnessStatus = FreshnessStatus.UNAVAILABLE
    disruption_source_error: str | None = None
    note: str


class CriticalRouteMonitor:
    """Derive a bounded-query-friendly route snapshot once per reference snapshot.

    Every snapped facility is routed to its nearest facility in another category. A multi-source
    Dijkstra search per origin category keeps the work bounded by the number of categories rather
    than running a complete shortest-path search for every possible facility pair.
    """

    def __init__(
        self,
        reference: ReferenceState | None,
        *,
        traffic_state: TrafficDisruptionState | None = None,
        max_snap_distance_m: float = 1000.0,
        disruption_match_distance_m: float = 25.0,
        now_factory: Callable[[], datetime] | None = None,
    ) -> None:
        if max_snap_distance_m <= 0 or max_snap_distance_m > 50_000:
            raise ValueError("max_snap_distance_m must be greater than zero and at most 50000")
        if disruption_match_distance_m <= 0 or disruption_match_distance_m > 250:
            raise ValueError(
                "disruption_match_distance_m must be greater than zero and at most 250"
            )
        self._reference = reference
        self._traffic_state = traffic_state
        self._max_snap_distance_m = max_snap_distance_m
        self._disruption_match_distance_m = disruption_match_distance_m
        self._now_factory = now_factory or (lambda: datetime.now(UTC))

    @staticmethod
    def _build_graph(edges: tuple[NetworkEdge, ...]) -> nx.MultiDiGraph[str]:
        graph: nx.MultiDiGraph[str] = nx.MultiDiGraph()
        for item in edges:
            graph.add_edge(
                item.source,
                item.target,
                key=item.id,
                id=item.id,
                travel_time_s=item.travel_time_s,
                length_m=item.length_m,
                edge=item,
            )
            if item.bidirectional:
                graph.add_edge(
                    item.target,
                    item.source,
                    key=item.id,
                    id=item.id,
                    travel_time_s=item.travel_time_s,
                    length_m=item.length_m,
                    edge=item,
                )
        return graph

    @staticmethod
    def _facility_name(facility: CriticalFacility) -> str:
        return facility.name or facility.id

    @staticmethod
    def _route_geometry(
        node_path: tuple[str, ...],
        nodes: dict[str, NetworkNode],
    ) -> dict[str, object] | None:
        coordinates: list[list[float]] = []
        for node_id in node_path:
            item = nodes.get(node_id)
            if item is None or item.longitude is None or item.latitude is None:
                return None
            coordinates.append([item.longitude, item.latitude])
        if len(coordinates) < 2:
            return None
        return {"type": "LineString", "coordinates": coordinates}

    @staticmethod
    def _path_edges(
        graph: nx.MultiDiGraph[str],
        node_path: tuple[str, ...],
    ) -> tuple[tuple[str, ...], float, float, tuple[NetworkEdge, ...]]:
        edge_ids: list[str] = []
        travel_time_s = 0.0
        length_m = 0.0
        source_edges: list[NetworkEdge] = []
        for source, target in zip(node_path, node_path[1:], strict=False):
            candidates = graph.get_edge_data(source, target)
            if not candidates:
                raise RuntimeError("critical route references a missing graph edge")
            _, data = min(
                candidates.items(),
                key=lambda item: (float(item[1]["travel_time_s"]), str(item[0])),
            )
            edge_ids.append(str(data["id"]))
            travel_time_s += float(data["travel_time_s"])
            length_m += float(data["length_m"])
            source_edge = data.get("edge")
            if isinstance(source_edge, NetworkEdge):
                source_edges.append(source_edge)
        return tuple(edge_ids), travel_time_s, length_m, tuple(source_edges)

    @staticmethod
    def _route_provenance(
        *,
        reference_generated_at: datetime,
        computed_at: datetime,
        origin: CriticalFacility,
        destination: CriticalFacility,
        edges: tuple[NetworkEdge, ...],
    ) -> CriticalRouteProvenance:
        providers: set[str] = set()
        datasets: set[str] = set()
        licences: set[str] = set()
        for provenance in [
            origin.provenance,
            destination.provenance,
            *(item.provenance for item in edges),
        ]:
            if provenance is None:
                continue
            providers.add(provenance.provider)
            datasets.add(provenance.dataset)
            if provenance.source_licence:
                licences.add(provenance.source_licence)
        return CriticalRouteProvenance(
            reference_generated_at=reference_generated_at,
            computed_at=computed_at,
            source_providers=tuple(sorted(providers)),
            source_datasets=tuple(sorted(datasets)),
            source_licences=tuple(sorted(licences)),
        )

    @staticmethod
    def _metric_shape(geometry: dict[str, object]):
        return shapely_transform(_TO_METRIC, shape(geometry))

    @staticmethod
    def _edge_geometry(
        edge: NetworkEdge,
        nodes: dict[str, NetworkNode],
    ) -> dict[str, object] | None:
        source = nodes.get(edge.source)
        target = nodes.get(edge.target)
        if (
            source is None
            or target is None
            or source.longitude is None
            or source.latitude is None
            or target.longitude is None
            or target.latitude is None
        ):
            return None
        return {
            "type": "LineString",
            "coordinates": [
                [source.longitude, source.latitude],
                [target.longitude, target.latitude],
            ],
        }

    def _active_disruptions(self, computed_at: datetime) -> tuple[TrafficDisruption, ...]:
        state = self._traffic_state
        if state is None or state.last_success_at is None:
            return ()
        return tuple(
            sorted(
                (item for item in state.disruptions if item.active_at(computed_at)),
                key=lambda item: item.id,
            )
        )

    def _matches_geometry(
        self,
        route_geometry: dict[str, object],
        disruption: TrafficDisruption,
    ) -> bool:
        route_shape = self._metric_shape(route_geometry)
        disruption_shape = self._metric_shape(disruption.spatial.geometry or {})
        return route_shape.distance(disruption_shape) <= self._disruption_match_distance_m

    def _closed_edge_ids(
        self,
        *,
        reference: ReferenceState,
        nodes: dict[str, NetworkNode],
        disruptions: tuple[TrafficDisruption, ...],
    ) -> tuple[str, ...]:
        full_closures = tuple(item for item in disruptions if item.is_full_closure)
        if not full_closures:
            return ()
        closure_shapes = [
            (item.id, self._metric_shape(item.spatial.geometry or {})) for item in full_closures
        ]
        closed: set[str] = set()
        for edge in reference.network_edges:
            geometry = self._edge_geometry(edge, nodes)
            if geometry is None:
                continue
            edge_shape = self._metric_shape(geometry)
            if any(
                edge_shape.distance(closure_shape) <= self._disruption_match_distance_m
                for _, closure_shape in closure_shapes
            ):
                closed.add(edge.id)
        return tuple(sorted(closed))

    @staticmethod
    def _remove_closed_edges(
        graph: nx.MultiDiGraph[str],
        closed_edge_ids: tuple[str, ...],
    ) -> nx.MultiDiGraph[str]:
        if not closed_edge_ids:
            return graph.copy()
        closed = set(closed_edge_ids)
        candidate = graph.copy()
        removals = [
            (source, target, key)
            for source, target, key, data in candidate.edges(keys=True, data=True)
            if str(data.get("id")) in closed
        ]
        for source, target, key in removals:
            candidate.remove_edge(source, target, key)
        return candidate

    def _apply_disruptions(
        self,
        *,
        route: CriticalRoute,
        graph: nx.MultiDiGraph[str],
        nodes: dict[str, NetworkNode],
        active_disruptions: tuple[TrafficDisruption, ...],
        closed_edge_ids: tuple[str, ...],
    ) -> CriticalRoute:
        state = self._traffic_state
        if state is None or state.last_success_at is None:
            return route

        matched = tuple(
            item for item in active_disruptions if self._matches_geometry(route.geometry, item)
        )
        matched_ids = tuple(item.id for item in matched)
        route_closed_edges = tuple(
            edge_id for edge_id in route.edge_ids if edge_id in set(closed_edge_ids)
        )
        disruption_providers = tuple(sorted({item.provenance.provider for item in matched}))
        disruption_licences = tuple(
            sorted(
                {
                    item.provenance.source_licence
                    for item in matched
                    if item.provenance.source_licence
                }
            )
        )
        provenance = route.provenance.model_copy(
            update={
                "disruption_source_providers": disruption_providers,
                "disruption_source_licences": disruption_licences,
            }
        )

        if not matched:
            return route.model_copy(
                update={
                    "disruption_aware_travel_time_s": route.travel_time_s,
                    "disruption_aware_length_m": route.length_m,
                    "disruption_aware_node_path": route.node_path,
                    "disruption_aware_edge_ids": route.edge_ids,
                    "disruption_aware_geometry": route.geometry,
                    "travel_time_delta_s": 0.0,
                    "provenance": provenance,
                }
            )

        if not route_closed_edges:
            return route.model_copy(
                update={
                    "route_state": "disrupted",
                    "active_disruption_ids": matched_ids,
                    "disruption_aware_travel_time_s": route.travel_time_s,
                    "disruption_aware_length_m": route.length_m,
                    "disruption_aware_node_path": route.node_path,
                    "disruption_aware_edge_ids": route.edge_ids,
                    "disruption_aware_geometry": route.geometry,
                    "travel_time_delta_s": 0.0,
                    "provenance": provenance,
                }
            )

        reroute_graph = self._remove_closed_edges(graph, closed_edge_ids)
        try:
            node_path = tuple(
                str(item)
                for item in nx.shortest_path(
                    reroute_graph,
                    source=route.node_path[0],
                    target=route.node_path[-1],
                    weight="travel_time_s",
                )
            )
        except (nx.NetworkXNoPath, nx.NodeNotFound):
            return route.model_copy(
                update={
                    "route_state": "blocked",
                    "active_disruption_ids": matched_ids,
                    "closed_edge_ids": route_closed_edges,
                    "provenance": provenance,
                }
            )

        geometry = self._route_geometry(node_path, nodes)
        if geometry is None:
            return route.model_copy(
                update={
                    "route_state": "blocked",
                    "active_disruption_ids": matched_ids,
                    "closed_edge_ids": route_closed_edges,
                    "provenance": provenance,
                }
            )
        edge_ids, travel_time_s, length_m, _ = self._path_edges(reroute_graph, node_path)
        return route.model_copy(
            update={
                "route_state": "rerouted",
                "active_disruption_ids": matched_ids,
                "closed_edge_ids": route_closed_edges,
                "disruption_aware_travel_time_s": travel_time_s,
                "disruption_aware_length_m": length_m,
                "disruption_aware_node_path": node_path,
                "disruption_aware_edge_ids": edge_ids,
                "disruption_aware_geometry": geometry,
                "travel_time_delta_s": travel_time_s - route.travel_time_s,
                "provenance": provenance,
            }
        )

    def _unavailable(self, *, computed_at: datetime, note: str) -> CriticalRouteSnapshot:
        reference = self._reference
        return CriticalRouteSnapshot(
            computed_at=computed_at,
            reference_generated_at=reference.generated_at if reference else None,
            status=AvailabilityStatus.UNAVAILABLE,
            quality=QualityFlag.UNKNOWN,
            source_errors=dict(reference.errors) if reference else {},
            disruption_data_available=(
                self._traffic_state is not None and self._traffic_state.last_success_at is not None
            ),
            disruption_generated_at=(
                self._traffic_state.generated_at if self._traffic_state else None
            ),
            disruption_freshness=(
                self._traffic_state.freshness
                if self._traffic_state
                else FreshnessStatus.UNAVAILABLE
            ),
            disruption_source_error=(
                self._traffic_state.source_error if self._traffic_state else None
            ),
            note=note,
        )

    def build(self) -> CriticalRouteSnapshot:
        computed_at = self._now_factory().astimezone(UTC)
        reference = self._reference
        if reference is None:
            return self._unavailable(
                computed_at=computed_at,
                note=(
                    "Critical routes are unavailable because no persisted reference snapshot is "
                    "loaded. No live traffic or synthetic route data is substituted."
                ),
            )
        if not reference.network_nodes or not reference.network_edges:
            return self._unavailable(
                computed_at=computed_at,
                note=(
                    "Critical routes are unavailable because the persisted road network "
                    "is missing. No live traffic or synthetic route data is substituted."
                ),
            )
        if len(reference.critical_facilities) < 2:
            return self._unavailable(
                computed_at=computed_at,
                note=(
                    "Critical routes require at least two persisted critical facilities. "
                    "No live traffic or synthetic facility data is substituted."
                ),
            )

        links = snap_facilities_to_network(
            reference.critical_facilities,
            reference.network_nodes,
            max_distance_m=self._max_snap_distance_m,
        )
        links_by_facility = {item.facility_id: item for item in links}
        facilities = {item.id: item for item in reference.critical_facilities}
        nodes = {item.id: item for item in reference.network_nodes}
        unsnapped = tuple(
            sorted(
                item.id
                for item in reference.critical_facilities
                if item.id not in links_by_facility
            )
        )
        graph = self._build_graph(reference.network_edges)
        reverse_graph = graph.reverse(copy=False)

        links_by_category: dict[str, list[tuple[CriticalFacility, str]]] = {}
        facilities_by_node: dict[str, list[CriticalFacility]] = {}
        for facility_id, link in links_by_facility.items():
            facility = facilities[facility_id]
            links_by_category.setdefault(facility.category, []).append((facility, link.node_id))
            facilities_by_node.setdefault(link.node_id, []).append(facility)
        for items in facilities_by_node.values():
            items.sort(key=lambda item: item.id)

        routes: list[CriticalRoute] = []
        unreachable: set[str] = set()
        categories = sorted(links_by_category)
        for origin_category in categories:
            target_links = [
                (facility, node_id)
                for category, items in links_by_category.items()
                if category != origin_category
                for facility, node_id in items
            ]
            if not target_links:
                unreachable.update(
                    facility.id for facility, _ in links_by_category[origin_category]
                )
                continue
            target_node_ids = sorted(
                {node_id for _, node_id in target_links if node_id in reverse_graph}
            )
            if not target_node_ids:
                unreachable.update(
                    facility.id for facility, _ in links_by_category[origin_category]
                )
                continue
            dijkstra_result = cast(
                tuple[dict[str, float], dict[str, list[str]]],
                nx.multi_source_dijkstra(
                    reverse_graph,
                    sources=target_node_ids,
                    weight="travel_time_s",
                ),
            )
            _, reverse_paths = dijkstra_result
            allowed_target_ids = {facility.id for facility, _ in target_links}
            for origin, origin_node_id in sorted(
                links_by_category[origin_category],
                key=lambda item: item[0].id,
            ):
                reverse_path = reverse_paths.get(origin_node_id)
                if not reverse_path or len(reverse_path) < 2:
                    unreachable.add(origin.id)
                    continue
                target_node_id = str(reverse_path[0])
                target_candidates = [
                    facility
                    for facility in facilities_by_node.get(target_node_id, [])
                    if facility.id in allowed_target_ids and facility.category != origin.category
                ]
                if not target_candidates:
                    unreachable.add(origin.id)
                    continue
                destination = min(target_candidates, key=lambda item: item.id)
                node_path = tuple(str(item) for item in reversed(reverse_path))
                geometry = self._route_geometry(node_path, nodes)
                if geometry is None:
                    unreachable.add(origin.id)
                    continue
                edge_ids, travel_time_s, length_m, source_edges = self._path_edges(graph, node_path)
                if travel_time_s <= 0 or length_m <= 0:
                    unreachable.add(origin.id)
                    continue
                quality = (
                    QualityFlag.PARTIAL
                    if reference.errors
                    or origin.quality is not QualityFlag.VALID
                    or destination.quality is not QualityFlag.VALID
                    else QualityFlag.VALID
                )
                routes.append(
                    CriticalRoute(
                        id=f"critical-route:{origin.id}:{destination.id}",
                        origin_facility_id=origin.id,
                        origin_name=self._facility_name(origin),
                        origin_category=origin.category,
                        destination_facility_id=destination.id,
                        destination_name=self._facility_name(destination),
                        destination_category=destination.category,
                        travel_time_s=travel_time_s,
                        length_m=length_m,
                        node_path=node_path,
                        edge_ids=edge_ids,
                        geometry=geometry,
                        quality=quality,
                        provenance=self._route_provenance(
                            reference_generated_at=reference.generated_at,
                            computed_at=computed_at,
                            origin=origin,
                            destination=destination,
                            edges=source_edges,
                        ),
                    )
                )

        routes.sort(
            key=lambda item: (
                item.origin_category,
                item.origin_name.casefold(),
                item.origin_facility_id,
                item.destination_facility_id,
            )
        )
        active_disruptions = self._active_disruptions(computed_at)
        closed_edge_ids = self._closed_edge_ids(
            reference=reference,
            nodes=nodes,
            disruptions=active_disruptions,
        )
        routes = [
            self._apply_disruptions(
                route=item,
                graph=graph,
                nodes=nodes,
                active_disruptions=active_disruptions,
                closed_edge_ids=closed_edge_ids,
            )
            for item in routes
        ]
        if not routes:
            return CriticalRouteSnapshot(
                computed_at=computed_at,
                reference_generated_at=reference.generated_at,
                status=AvailabilityStatus.UNAVAILABLE,
                quality=QualityFlag.UNKNOWN,
                unsnapped_facility_ids=unsnapped,
                unreachable_facility_ids=tuple(sorted(unreachable)),
                source_errors=dict(reference.errors),
                disruption_data_available=(
                    self._traffic_state is not None
                    and self._traffic_state.last_success_at is not None
                ),
                disruption_generated_at=(
                    self._traffic_state.generated_at if self._traffic_state else None
                ),
                disruption_freshness=(
                    self._traffic_state.freshness
                    if self._traffic_state
                    else FreshnessStatus.UNAVAILABLE
                ),
                disruption_source_error=(
                    self._traffic_state.source_error if self._traffic_state else None
                ),
                note=(
                    "No cross-category critical-facility route can be resolved from the persisted "
                    "road network. No live traffic or synthetic topology is substituted."
                ),
            )

        disruption_degraded = bool(
            self._traffic_state is not None
            and (
                self._traffic_state.source_error is not None
                or self._traffic_state.freshness is FreshnessStatus.STALE
            )
        )
        degraded = bool(reference.errors or unsnapped or unreachable or disruption_degraded)
        return CriticalRouteSnapshot(
            computed_at=computed_at,
            reference_generated_at=reference.generated_at,
            status=AvailabilityStatus.DEGRADED if degraded else AvailabilityStatus.AVAILABLE,
            quality=QualityFlag.PARTIAL if degraded else QualityFlag.VALID,
            routes=tuple(routes),
            unsnapped_facility_ids=unsnapped,
            unreachable_facility_ids=tuple(sorted(unreachable)),
            source_errors=dict(reference.errors),
            disruption_data_available=(
                self._traffic_state is not None
                and self._traffic_state.last_success_at is not None
            ),
            disruption_generated_at=(
                self._traffic_state.generated_at if self._traffic_state else None
            ),
            disruption_freshness=(
                self._traffic_state.freshness
                if self._traffic_state
                else FreshnessStatus.UNAVAILABLE
            ),
            disruption_source_error=(
                self._traffic_state.source_error if self._traffic_state else None
            ),
            note=(
                "Routes are recomputed from the current persisted weighted road/reference "
                "snapshot. Active official VIZ disruptions can mark routes disrupted, rerouted "
                "or blocked; only severity=Vollsperrung removes matched road edges. "
                "No live congestion-speed telemetry is integrated and no speed penalty is "
                "invented for other restrictions."
            ),
        )
