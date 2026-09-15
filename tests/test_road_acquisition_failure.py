from datetime import UTC, datetime

from berlin_urban_intelligence.runtime.reference import ReferenceState
from berlin_urban_intelligence.runtime.reference_acquisition import ReferenceAcquisitionCoordinator
from berlin_urban_intelligence.shared.contracts import NetworkEdge, NetworkNode, Provenance

NOW = datetime(2026, 9, 15, 12, 0, tzinfo=UTC)


def _provenance() -> Provenance:
    return Provenance(
        provider="OpenStreetMap contributors",
        dataset="OpenStreetMap road network",
        source_url="https://www.openstreetmap.org/",
        retrieved_at=NOW,
        processed_at=NOW,
        processing_method=(
            "OSMnx acquisition followed by canonical normalization; "
            "OSMnx add_edge_speeds/add_edge_travel_times explicitly enabled"
        ),
        agent="resilience",
        agent_version="1.0.0",
        source_licence="ODbL 1.0",
    )


def _previous() -> ReferenceState:
    provenance = _provenance()
    return ReferenceState(
        generated_at=NOW,
        network_nodes=(
            NetworkNode(
                id="osm-node:1", longitude=13.4, latitude=52.5, provenance=provenance
            ),
            NetworkNode(
                id="osm-node:2", longitude=13.41, latitude=52.51, provenance=provenance
            ),
        ),
        network_edges=(
            NetworkEdge(
                id="osm:1:2:0:1",
                source="osm-node:1",
                target="osm-node:2",
                travel_time_s=10.0,
                length_m=100.0,
                bidirectional=False,
                provenance=provenance,
            ),
        ),
    )


class _PassThroughWfs:
    def refresh(self, *, previous: ReferenceState | None = None) -> ReferenceState:
        return previous or ReferenceState(generated_at=NOW)


class _UnavailableRoad:
    def fetch(self, *args: object, **kwargs: object) -> object:
        del args, kwargs
        raise RuntimeError("provider unavailable")


class _InvalidRoad:
    def fetch(self, *args: object, **kwargs: object) -> object:
        del args, kwargs
        raise ValueError("schema changed")


def test_osm_provider_failure_retains_last_known_good_network_without_fabrication() -> None:
    previous = _previous()
    state = ReferenceAcquisitionCoordinator(
        wfs=_PassThroughWfs(),
        road_client=_UnavailableRoad(),  # type: ignore[arg-type]
        now_factory=lambda: NOW,
    ).refresh(previous=previous, include_osm=True, allow_speed_imputation=True)

    assert state.errors["osm_berlin"] == "SOURCE_UNAVAILABLE"
    assert state.network_nodes == previous.network_nodes
    assert state.network_edges == previous.network_edges


def test_osm_schema_failure_is_explicit_and_does_not_create_network() -> None:
    state = ReferenceAcquisitionCoordinator(
        wfs=_PassThroughWfs(),
        road_client=_InvalidRoad(),  # type: ignore[arg-type]
        now_factory=lambda: NOW,
    ).refresh(include_osm=True, allow_speed_imputation=True)

    assert state.errors["osm_berlin"] == "SCHEMA_CHANGED"
    assert state.network_nodes == ()
    assert state.network_edges == ()
