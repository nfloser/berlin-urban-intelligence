from __future__ import annotations

from datetime import UTC, datetime, timedelta
from pathlib import Path

from fastapi.testclient import TestClient
from pydantic import HttpUrl

from berlin_urban_intelligence.api.app import create_app
from berlin_urban_intelligence.runtime.reference import ReferenceState, ReferenceStateStore
from berlin_urban_intelligence.runtime.traffic_disruptions import (
    TrafficDisruption,
    TrafficDisruptionState,
    TrafficDisruptionStateStore,
)
from berlin_urban_intelligence.shared.contracts import (
    CriticalFacility,
    FreshnessStatus,
    NetworkEdge,
    NetworkNode,
    Provenance,
    QualityFlag,
    SpatialReference,
)

NOW = datetime.now(UTC).replace(microsecond=0)
VIZ_URL = HttpUrl("https://api.viz.berlin.de/daten/baustellen_sperrungen_viz.json")


def provenance(identifier: str) -> Provenance:
    return Provenance(
        provider="API traffic acceptance provider",
        dataset="API traffic acceptance",
        source_url=VIZ_URL,
        original_identifier=identifier,
        retrieved_at=NOW,
        processed_at=NOW,
        agent="resilience",
        agent_version="1.0.0",
        source_licence="Datenlizenz Deutschland - Namensnennung - Version 2.0",
    )


def disruption(
    disruption_id: str,
    *,
    valid_from: datetime,
    valid_to: datetime,
    severity: str = "Vollsperrung",
) -> TrafficDisruption:
    return TrafficDisruption(
        id=disruption_id,
        subtype="Sperrung",
        severity=severity,
        street="Acceptance Straße",
        section="zwischen A und B",
        description="Acceptance disruption",
        valid_from=valid_from,
        valid_to=valid_to,
        source_updated_at=NOW - timedelta(minutes=10),
        is_full_closure=severity == "Vollsperrung",
        spatial=SpatialReference(
            crs="EPSG:4326",
            geometry={
                "type": "LineString",
                "coordinates": [[13.4000, 52.5200], [13.4100, 52.5200]],
            },
        ),
        provenance=provenance(disruption_id),
    )


def traffic_state(*items: TrafficDisruption) -> TrafficDisruptionState:
    return TrafficDisruptionState(
        generated_at=NOW,
        source_id="berlin_viz_road_disruptions",
        disruptions=items,
        last_success_at=NOW,
        latest_source_update_at=NOW - timedelta(minutes=10),
        freshness=FreshnessStatus.VALID,
    )


def reference_state() -> ReferenceState:
    facilities = (
        CriticalFacility(
            id="facility:hospital",
            name="Hospital",
            category="hospital",
            quality=QualityFlag.VALID,
            provenance=provenance("hospital"),
            spatial=SpatialReference(
                crs="EPSG:4326",
                geometry={"type": "Point", "coordinates": [13.4000, 52.5200]},
            ),
        ),
        CriticalFacility(
            id="facility:fire",
            name="Fire",
            category="fire_station",
            quality=QualityFlag.VALID,
            provenance=provenance("fire"),
            spatial=SpatialReference(
                crs="EPSG:4326",
                geometry={"type": "Point", "coordinates": [13.4200, 52.5200]},
            ),
        ),
    )
    nodes = (
        NetworkNode(id="a", longitude=13.4000, latitude=52.5200),
        NetworkNode(id="b", longitude=13.4100, latitude=52.5200),
        NetworkNode(id="c", longitude=13.4200, latitude=52.5200),
        NetworkNode(id="x", longitude=13.4100, latitude=52.5300),
    )
    edges = (
        NetworkEdge(id="ab", source="a", target="b", travel_time_s=50, length_m=700),
        NetworkEdge(id="bc", source="b", target="c", travel_time_s=50, length_m=700),
        NetworkEdge(id="ax", source="a", target="x", travel_time_s=80, length_m=1100),
        NetworkEdge(id="xc", source="x", target="c", travel_time_s=80, length_m=1100),
    )
    return ReferenceState(
        generated_at=NOW,
        critical_facilities=facilities,
        network_nodes=nodes,
        network_edges=edges,
    )


def configure_paths(monkeypatch, tmp_path: Path) -> tuple[Path, Path]:
    reference_path = tmp_path / "reference.json"
    traffic_path = tmp_path / "traffic-disruptions.json"
    monkeypatch.setenv("BUI_REFERENCE_STATE", str(reference_path))
    monkeypatch.setenv("BUI_TRAFFIC_DISRUPTION_STATE", str(traffic_path))
    monkeypatch.setenv("BUI_RUNTIME_STATE", str(tmp_path / "runtime-missing.json"))
    monkeypatch.setenv("BUI_ENERGY_STATE", str(tmp_path / "energy-missing.json"))
    monkeypatch.setenv("BUI_DERIVED_STATE", str(tmp_path / "derived-missing.json"))
    ReferenceStateStore(reference_path).save(reference_state())
    return reference_path, traffic_path


def test_traffic_disruption_api_is_bounded_and_defaults_to_active_items(
    monkeypatch,
    tmp_path: Path,
) -> None:
    _, traffic_path = configure_paths(monkeypatch, tmp_path)
    active = disruption(
        "viz:active",
        valid_from=NOW - timedelta(hours=1),
        valid_to=NOW + timedelta(hours=1),
    )
    future = disruption(
        "viz:future",
        valid_from=NOW + timedelta(hours=2),
        valid_to=NOW + timedelta(hours=3),
    )
    TrafficDisruptionStateStore(traffic_path).save(traffic_state(active, future))

    with TestClient(create_app()) as client:
        active_response = client.get("/api/v1/traffic/disruptions?limit=10")
        all_response = client.get("/api/v1/traffic/disruptions?active_only=false&offset=1&limit=1")

    assert active_response.status_code == 200
    active_body = active_response.json()
    assert active_body["freshness"] == "valid"
    assert active_body["routing_eligible"] is True
    assert active_body["disruption_count_total"] == 2
    assert active_body["active_count_total"] == 1
    assert active_body["returned"] == 1
    assert active_body["disruptions"][0]["id"] == "viz:active"

    assert all_response.status_code == 200
    all_body = all_response.json()
    assert all_body["returned"] == 1
    assert all_body["truncated"] is False
    assert all_body["disruptions"][0]["id"] == "viz:future"


def test_missing_traffic_state_is_explicitly_unavailable(monkeypatch, tmp_path: Path) -> None:
    configure_paths(monkeypatch, tmp_path)

    with TestClient(create_app()) as client:
        response = client.get("/api/v1/traffic/disruptions")

    assert response.status_code == 200
    assert response.json() == {
        "generated_at": None,
        "source_id": "berlin_viz_road_disruptions",
        "last_success_at": None,
        "latest_source_update_at": None,
        "source_error": "STATE_UNAVAILABLE",
        "freshness": "unavailable",
        "routing_eligible": False,
        "evaluated_at": None,
        "disruption_count_total": 0,
        "active_count_total": 0,
        "returned": 0,
        "truncated": False,
        "disruptions": [],
    }


def test_running_api_recomputes_critical_routes_when_traffic_snapshot_changes(
    monkeypatch,
    tmp_path: Path,
) -> None:
    _, traffic_path = configure_paths(monkeypatch, tmp_path)

    with TestClient(create_app()) as client:
        first = client.get("/api/v1/resilience/critical-routes?limit=10").json()
        first_route = next(
            item for item in first["routes"] if item["origin_facility_id"] == "facility:hospital"
        )
        assert first_route["route_state"] == "baseline"
        assert first_route["travel_time_s"] == 100.0

        closure = disruption(
            "viz:closure:ab",
            valid_from=NOW - timedelta(hours=1),
            valid_to=NOW + timedelta(hours=1),
        )
        TrafficDisruptionStateStore(traffic_path).save(traffic_state(closure))

        second = client.get("/api/v1/resilience/critical-routes?limit=10").json()
        system = client.get("/api/v1/system").json()

    second_route = next(
        item for item in second["routes"] if item["origin_facility_id"] == "facility:hospital"
    )
    assert second_route["route_state"] == "rerouted"
    assert second_route["disruption_aware_travel_time_s"] == 160.0
    assert second_route["active_disruption_ids"] == ["viz:closure:ab"]
    assert system["traffic_disruption_generated_at"] == NOW.isoformat().replace("+00:00", "Z")
    assert system["snapshot_reload"]["traffic_disruptions"]["status"] == "current"
