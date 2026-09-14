"""Orchestrate acquisition of non-live Berlin reference layers."""

from __future__ import annotations

from collections.abc import Callable
from datetime import UTC, datetime
from typing import Protocol

from berlin_urban_intelligence.adapters.osm_network import OsmnxRoadNetworkClient, RoadNetworkSnapshot
from berlin_urban_intelligence.adapters.vbb_static import GtfsStaticSnapshot, VbbGtfsStaticAdapter, VbbGtfsStaticClient
from berlin_urban_intelligence.runtime.reference import ReferenceState
from berlin_urban_intelligence.runtime.reference_refresh import ReferenceRefreshCoordinator


class GtfsReader(Protocol):
    def fetch(self) -> bytes: ...


class RoadReader(Protocol):
    def fetch(self, place: str, *, network_type: str = "drive", allow_speed_imputation: bool = False, retrieved_at: datetime | None = None) -> RoadNetworkSnapshot: ...


class WfsCoordinator(Protocol):
    def refresh(self, *, previous: ReferenceState | None = None) -> ReferenceState: ...


class ReferenceAcquisitionCoordinator:
    def __init__(self, *, wfs: WfsCoordinator | None = None, gtfs_client: GtfsReader | None = None, gtfs_adapter: VbbGtfsStaticAdapter | None = None, road_client: RoadReader | None = None, now_factory: Callable[[], datetime] | None = None) -> None:
        self.wfs = wfs or ReferenceRefreshCoordinator(now_factory=now_factory)
        self.gtfs_client = gtfs_client or VbbGtfsStaticClient()
        self.gtfs_adapter = gtfs_adapter or VbbGtfsStaticAdapter()
        self.road_client = road_client
        self.now_factory = now_factory or (lambda: datetime.now(UTC))

    @staticmethod
    def _failure(exc: Exception) -> str:
        return "SCHEMA_CHANGED" if isinstance(exc, (ValueError, KeyError, TypeError)) else "SOURCE_UNAVAILABLE"

    def refresh(self, *, previous: ReferenceState | None = None, include_gtfs: bool = False, include_osm: bool = False, place: str = "Berlin, Germany", network_type: str = "drive", allow_speed_imputation: bool = False) -> ReferenceState:
        now = self.now_factory()
        if now.tzinfo is None or now.utcoffset() is None:
            raise ValueError("now_factory must produce timezone-aware datetimes")
        now = now.astimezone(UTC)
        state = self.wfs.refresh(previous=previous)
        errors = dict(state.errors)
        stops = state.transport_stops
        nodes = state.network_nodes
        edges = state.network_edges

        if include_gtfs:
            try:
                snapshot: GtfsStaticSnapshot = self.gtfs_adapter.parse(self.gtfs_client.fetch(), retrieved_at=now)
                stops = snapshot.stops
                errors.pop("vbb_gtfs_static", None)
            except Exception as exc:
                errors["vbb_gtfs_static"] = self._failure(exc)
                stops = previous.transport_stops if previous is not None else ()

        if include_osm:
            try:
                road_client = self.road_client or OsmnxRoadNetworkClient()
                road = road_client.fetch(place, network_type=network_type, allow_speed_imputation=allow_speed_imputation, retrieved_at=now)
                nodes, edges = road.nodes, road.edges
                errors.pop("osm_berlin", None)
            except Exception as exc:
                errors["osm_berlin"] = self._failure(exc)
                nodes = previous.network_nodes if previous is not None else ()
                edges = previous.network_edges if previous is not None else ()

        return ReferenceState(
            generated_at=now,
            critical_facilities=state.critical_facilities,
            official_model_features=state.official_model_features,
            transport_stops=stops,
            network_nodes=nodes,
            network_edges=edges,
            errors=dict(sorted(errors.items())),
        )
