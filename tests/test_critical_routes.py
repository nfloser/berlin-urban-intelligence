from __future__ import annotations

from datetime import UTC, datetime, timedelta
from pathlib import Path

from fastapi.testclient import TestClient
from pydantic import HttpUrl

from berlin_urban_intelligence.api.app import create_app
from berlin_urban_intelligence.runtime.critical_routes import CriticalRouteMonitor
from berlin_urban_intelligence.runtime.reference import ReferenceState, ReferenceStateStore
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
    Provenance,
    QualityFlag,
    SpatialReference,
)

NOW = datetime(2026, 9, 19, 12, 0, tzinfo=UTC)
SOURCE = HttpUrl("https://example.invalid/critical-route-test")


def provenance(dataset: str, identifier: str) -> Provenance:
    return Provenance(
        provider="Critical route test provider",
        dataset=dataset,
        source_url=SOURCE,
        original_identifier=identifier,
        retrieved_at=NOW,
        processed_at=NOW,
        processing_method="deterministic test fixture",
        agent="resilience",
        agent_version="1.0.0",
        source_licence="ODbL-1.0",
    )


def node(node_id: str, longitude: float, latitude: float) -> NetworkNode:
    return NetworkNode(
        id=node_id,
        longitude=longitude,
        latitude=latitude,
        provenance=provenance("test-road-network", node_id),
    )


def edge(
    edge_id: str,
    source: str,
    target: str,
    travel_time_s: float,
    *,
    length_m: float = 1000.0,
) -> NetworkEdge:
    return NetworkEdge(
        id=edge_id,
        source=source,
        target=target,
        travel_time_s=travel_time_s,
        length_m=length_m,
        bidirectional=True,
        provenance=provenance("test-road-network", edge_id),
    )


def facility(
    facility_id: str,
    name: str,
    category: str,
    longitude: float,
    latitude: float,
) -> CriticalFacility:
    return CriticalFacility(
        id=facility_id,
        name=name,
        category=category,
        confidence="official_dataset",
        quality=QualityFlag.VALID,
        provenance=provenance("test-critical-facilities", facility_id),
        spatial=SpatialReference(
            crs="EPSG:4326",
            geometry={"type": "Point", "coordinates": [longitude, latitude]},
        ),
    )


def reference_fixture(*, direct_travel_time_s: float = 120.0) -> ReferenceState:
    return ReferenceState(
        generated_at=NOW,
        critical_facilities=(
            facility("facility:hospital", "Hospital", "hospital", 13.4000, 52.5200),
            facility("facility:fire", "Fire station", "fire_station", 13.4200, 52.5200),
            facility("facility:police", "Police", "police", 13.4200, 52.5300),
        ),
        network_nodes=(
            node("a", 13.4000, 52.5200),
            node("b", 13.4100, 52.5200),
            node("c", 13.4200, 52.5200),
            node("d", 13.4200, 52.5300),
        ),
        network_edges=(
            edge("ab", "a", "b", direct_travel_time_s / 2, length_m=700.0),
            edge("bc", "b", "c", direct_travel_time_s / 2, length_m=700.0),
            edge("cd", "c", "d", 60.0, length_m=900.0),
        ),
    )


def disruption(
    disruption_id: str,
    severity: str | None,
    geometry: dict[str, object],
) -> TrafficDisruption:
    return TrafficDisruption(
        id=disruption_id,
        subtype="Sperrung" if severity == "Vollsperrung" else "Baustelle",
        severity=severity,
        street="Teststraße",
        section="Testabschnitt",
        description="Source-backed traffic disruption",
        valid_from=NOW - timedelta(hours=1),
        valid_to=NOW + timedelta(hours=1),
        source_updated_at=NOW - timedelta(minutes=5),
        is_full_closure=severity == "Vollsperrung",
        spatial=SpatialReference(crs="EPSG:4326", geometry=geometry),
        provenance=Provenance(
            provider="Verkehrsinformationszentrale Berlin (VIZ)",
            dataset="VIZ road disruptions",
            source_url=HttpUrl("https://api.viz.berlin.de/daten/baustellen_sperrungen.json"),
            original_identifier=disruption_id,
            observation_time=NOW - timedelta(minutes=5),
            retrieved_at=NOW,
            processed_at=NOW,
            agent="resilience",
            agent_version="1.0.0",
            source_licence="Datenlizenz Deutschland - Namensnennung - Version 2.0",
        ),
    )


def traffic_state(*items: TrafficDisruption) -> TrafficDisruptionState:
    return TrafficDisruptionState(
        generated_at=NOW,
        source_id="berlin_viz_road_disruptions",
        disruptions=items,
        last_success_at=NOW,
        freshness="valid",
    )


def reference_with_alternative() -> ReferenceState:
    base = reference_fixture()
    return base.model_copy(
        update={
            "network_nodes": (
                *base.network_nodes,
                node("x", 13.4100, 52.5300),
            ),
            "network_edges": (
                *base.network_edges,
                edge("ax", "a", "x", 100.0, length_m=1200.0),
                edge("xc", "x", "c", 100.0, length_m=1200.0),
            ),
        }
    )


def test_monitor_derives_nearest_cross_category_routes_with_geometry_and_provenance() -> None:
    snapshot = CriticalRouteMonitor(reference_fixture(), now_factory=lambda: NOW).build()

    assert snapshot.status is AvailabilityStatus.AVAILABLE
    assert snapshot.traffic_data_available is False
    assert snapshot.reference_generated_at == NOW
    assert len(snapshot.routes) == 3
    assert snapshot.unsnapped_facility_ids == ()
    assert snapshot.unreachable_facility_ids == ()

    routes = {route.origin_facility_id: route for route in snapshot.routes}
    hospital_route = routes["facility:hospital"]
    assert hospital_route.destination_facility_id == "facility:fire"
    assert hospital_route.travel_time_s == 120.0
    assert hospital_route.length_m == 1400.0
    assert hospital_route.node_path == ("a", "b", "c")
    assert hospital_route.edge_ids == ("ab", "bc")
    assert hospital_route.geometry == {
        "type": "LineString",
        "coordinates": [[13.4, 52.52], [13.41, 52.52], [13.42, 52.52]],
    }
    assert hospital_route.provenance.traffic_data_available is False
    assert hospital_route.provenance.source_providers == ("Critical route test provider",)
    assert hospital_route.provenance.source_licences == ("ODbL-1.0",)


def test_active_full_closure_reroutes_affected_critical_route_without_speed_inference() -> None:
    closure = disruption(
        "viz:closure:ab",
        "Vollsperrung",
        {
            "type": "LineString",
            "coordinates": [[13.4000, 52.5200], [13.4100, 52.5200]],
        },
    )

    snapshot = CriticalRouteMonitor(
        reference_with_alternative(),
        traffic_state=traffic_state(closure),
        now_factory=lambda: NOW,
    ).build()

    route = next(item for item in snapshot.routes if item.origin_facility_id == "facility:hospital")
    assert snapshot.disruption_data_available is True
    assert snapshot.traffic_data_available is False
    assert route.travel_time_s == 120.0
    assert route.edge_ids == ("ab", "bc")
    assert route.route_state == "rerouted"
    assert route.active_disruption_ids == ("viz:closure:ab",)
    assert route.closed_edge_ids == ("ab",)
    assert route.disruption_aware_travel_time_s == 200.0
    assert route.disruption_aware_edge_ids == ("ax", "xc")
    assert route.disruption_aware_geometry == {
        "type": "LineString",
        "coordinates": [[13.4, 52.52], [13.41, 52.53], [13.42, 52.52]],
    }
    assert route.travel_time_delta_s == 80.0


def test_full_closure_without_alternative_marks_route_blocked() -> None:
    closure = disruption(
        "viz:closure:ab",
        "Vollsperrung",
        {
            "type": "LineString",
            "coordinates": [[13.4000, 52.5200], [13.4100, 52.5200]],
        },
    )

    snapshot = CriticalRouteMonitor(
        reference_fixture(),
        traffic_state=traffic_state(closure),
        now_factory=lambda: NOW,
    ).build()

    route = next(item for item in snapshot.routes if item.origin_facility_id == "facility:hospital")
    assert route.route_state == "blocked"
    assert route.disruption_aware_travel_time_s is None
    assert route.disruption_aware_geometry is None
    assert route.closed_edge_ids == ("ab",)


def test_non_closure_disruption_is_visible_without_invented_time_penalty() -> None:
    works = disruption(
        "viz:works:bc",
        "keine Sperrung",
        {
            "type": "LineString",
            "coordinates": [[13.4100, 52.5200], [13.4200, 52.5200]],
        },
    )

    snapshot = CriticalRouteMonitor(
        reference_fixture(),
        traffic_state=traffic_state(works),
        now_factory=lambda: NOW,
    ).build()

    route = next(item for item in snapshot.routes if item.origin_facility_id == "facility:hospital")
    assert route.route_state == "disrupted"
    assert route.active_disruption_ids == ("viz:works:bc",)
    assert route.closed_edge_ids == ()
    assert route.disruption_aware_travel_time_s == 120.0
    assert route.travel_time_delta_s == 0.0


def test_expired_or_future_disruptions_do_not_change_route_state() -> None:
    expired = disruption(
        "viz:expired",
        "Vollsperrung",
        {"type": "Point", "coordinates": [13.405, 52.52]},
    ).model_copy(
        update={
            "valid_from": NOW - timedelta(hours=3),
            "valid_to": NOW - timedelta(hours=2),
        }
    )
    future = disruption(
        "viz:future",
        "Vollsperrung",
        {"type": "Point", "coordinates": [13.405, 52.52]},
    ).model_copy(
        update={
            "valid_from": NOW + timedelta(hours=2),
            "valid_to": NOW + timedelta(hours=3),
        }
    )

    snapshot = CriticalRouteMonitor(
        reference_fixture(),
        traffic_state=traffic_state(expired, future),
        now_factory=lambda: NOW,
    ).build()

    route = next(item for item in snapshot.routes if item.origin_facility_id == "facility:hospital")
    assert route.route_state == "baseline"
    assert route.active_disruption_ids == ()
    assert route.closed_edge_ids == ()
    assert route.disruption_aware_travel_time_s == 120.0


def test_stale_disruption_state_is_visible_but_does_not_change_routes() -> None:
    closure = disruption(
        "viz:stale-closure:ab",
        "Vollsperrung",
        {
            "type": "LineString",
            "coordinates": [[13.4000, 52.5200], [13.4100, 52.5200]],
        },
    )
    stale_state = traffic_state(closure).model_copy(update={"freshness": FreshnessStatus.STALE})

    snapshot = CriticalRouteMonitor(
        reference_with_alternative(),
        traffic_state=stale_state,
        now_factory=lambda: NOW,
    ).build()

    route = next(item for item in snapshot.routes if item.origin_facility_id == "facility:hospital")
    assert snapshot.disruption_data_available is True
    assert snapshot.disruption_freshness is FreshnessStatus.STALE
    assert route.route_state == "baseline"
    assert route.active_disruption_ids == ()
    assert route.disruption_aware_travel_time_s == route.travel_time_s


def test_monitor_keeps_routes_but_marks_snapshot_degraded_when_reference_has_source_error() -> None:
    base = reference_fixture()
    degraded = base.model_copy(update={"errors": {"osm_berlin": "SOURCE_UNAVAILABLE"}})

    snapshot = CriticalRouteMonitor(degraded, now_factory=lambda: NOW).build()

    assert snapshot.status is AvailabilityStatus.DEGRADED
    assert len(snapshot.routes) == 3
    assert snapshot.source_errors == {"osm_berlin": "SOURCE_UNAVAILABLE"}
    assert "live traffic" in snapshot.note.lower()


def test_monitor_degrades_when_a_snapped_facility_is_on_an_isolated_node() -> None:
    base = reference_fixture()
    isolated_facility = facility(
        "facility:isolated",
        "Isolated facility",
        "emergency_service",
        13.4300,
        52.5400,
    )
    isolated_node = node("isolated", 13.4300, 52.5400)
    reference = base.model_copy(
        update={
            "critical_facilities": (*base.critical_facilities, isolated_facility),
            "network_nodes": (*base.network_nodes, isolated_node),
        }
    )

    snapshot = CriticalRouteMonitor(reference, now_factory=lambda: NOW).build()

    assert snapshot.status is AvailabilityStatus.DEGRADED
    assert "facility:isolated" in snapshot.unreachable_facility_ids
    assert "facility:isolated" not in {route.origin_facility_id for route in snapshot.routes}
    assert len(snapshot.routes) == 3


def test_monitor_is_explicitly_unavailable_without_required_reference_inputs() -> None:
    empty = ReferenceState(generated_at=NOW)

    snapshot = CriticalRouteMonitor(empty, now_factory=lambda: NOW).build()

    assert snapshot.status is AvailabilityStatus.UNAVAILABLE
    assert snapshot.routes == ()
    assert snapshot.traffic_data_available is False
    assert "network" in snapshot.note.lower()


def _write_reference(path: Path, *, generated_at: datetime, travel_time_s: float) -> None:
    state = reference_fixture(direct_travel_time_s=travel_time_s).model_copy(
        update={"generated_at": generated_at}
    )
    ReferenceStateStore(path).save(state)


def test_critical_route_api_recomputes_after_reference_snapshot_replacement(
    monkeypatch,
    tmp_path: Path,
) -> None:
    reference_path = tmp_path / "reference.json"
    monkeypatch.setenv("BUI_REFERENCE_STATE", str(reference_path))
    monkeypatch.setenv("BUI_RUNTIME_STATE", str(tmp_path / "missing-runtime.json"))
    monkeypatch.setenv("BUI_ENERGY_STATE", str(tmp_path / "missing-energy.json"))
    monkeypatch.setenv("BUI_DERIVED_STATE", str(tmp_path / "missing-derived.json"))

    _write_reference(reference_path, generated_at=NOW, travel_time_s=120.0)

    with TestClient(create_app()) as client:
        first = client.get("/api/v1/resilience/critical-routes?limit=10")
        assert first.status_code == 200
        first_body = first.json()
        assert first_body["route_count_total"] == 3
        assert first_body["returned"] == 3
        assert first_body["truncated"] is False
        assert first_body["traffic_data_available"] is False
        first_hospital = next(
            route
            for route in first_body["routes"]
            if route["origin_facility_id"] == "facility:hospital"
        )
        assert first_hospital["travel_time_s"] == 120.0

        second_time = NOW + timedelta(minutes=5)
        _write_reference(reference_path, generated_at=second_time, travel_time_s=200.0)

        second = client.get("/api/v1/resilience/critical-routes?limit=10")
        assert second.status_code == 200
        second_body = second.json()

    assert second_body["reference_generated_at"] == second_time.isoformat().replace("+00:00", "Z")
    second_hospital = next(
        route
        for route in second_body["routes"]
        if route["origin_facility_id"] == "facility:hospital"
    )
    assert second_hospital["travel_time_s"] == 200.0


def test_critical_route_api_is_bounded_and_reports_truncation(monkeypatch, tmp_path: Path) -> None:
    reference_path = tmp_path / "reference.json"
    monkeypatch.setenv("BUI_REFERENCE_STATE", str(reference_path))
    monkeypatch.setenv("BUI_RUNTIME_STATE", str(tmp_path / "missing-runtime.json"))
    monkeypatch.setenv("BUI_ENERGY_STATE", str(tmp_path / "missing-energy.json"))
    monkeypatch.setenv("BUI_DERIVED_STATE", str(tmp_path / "missing-derived.json"))
    _write_reference(reference_path, generated_at=NOW, travel_time_s=120.0)

    with TestClient(create_app()) as client:
        response = client.get("/api/v1/resilience/critical-routes?limit=2")

    assert response.status_code == 200
    body = response.json()
    assert body["route_count_total"] == 3
    assert body["returned"] == 2
    assert body["truncated"] is True
