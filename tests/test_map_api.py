from datetime import UTC, datetime

from fastapi.testclient import TestClient

from berlin_urban_intelligence.api.app import create_app
from berlin_urban_intelligence.runtime.reference import ReferenceState, ReferenceStateStore
from berlin_urban_intelligence.shared.contracts import (
    CriticalFacility,
    DataState,
    OfficialModelFeature,
    Provenance,
    QualityFlag,
    SpatialReference,
    UrbanEntity,
)

NOW = datetime(2026, 9, 15, 9, 0, tzinfo=UTC)


def provenance(identifier: str) -> Provenance:
    return Provenance(
        provider="fixture",
        dataset="map-api",
        source_url="https://example.invalid/map-api",
        original_identifier=identifier,
        retrieved_at=NOW,
        processed_at=NOW,
        processing_method="fixture",
        agent="fixture",
        agent_version="1.0.0",
    )


def write_reference(path) -> None:
    state = ReferenceState(
        generated_at=NOW,
        critical_facilities=(
            CriticalFacility(
                id="facility:inside",
                name="Inside hospital",
                category="hospital",
                quality=QualityFlag.VALID,
                provenance=provenance("facility-inside"),
                spatial=SpatialReference(
                    crs="EPSG:4326",
                    geometry={"type": "Point", "coordinates": [13.405, 52.52]},
                ),
            ),
            CriticalFacility(
                id="facility:outside",
                name="Outside hospital",
                category="hospital",
                quality=QualityFlag.VALID,
                provenance=provenance("facility-outside"),
                spatial=SpatialReference(
                    crs="EPSG:4326",
                    geometry={"type": "Point", "coordinates": [13.8, 52.7]},
                ),
            ),
        ),
        transport_stops=(
            UrbanEntity(
                id="stop:inside:1",
                entity_type="transport_stop",
                name="Inside stop 1",
                spatial=SpatialReference(
                    crs="EPSG:4326",
                    geometry={"type": "Point", "coordinates": [13.41, 52.521]},
                ),
            ),
            UrbanEntity(
                id="stop:inside:2",
                entity_type="transport_stop",
                name="Inside stop 2",
                spatial=SpatialReference(
                    crs="EPSG:4326",
                    geometry={"type": "Point", "coordinates": [13.42, 52.522]},
                ),
            ),
        ),
        official_model_features=(
            OfficialModelFeature(
                id="climate:intersects",
                entity_id="berlin:climate-fixture",
                model_name="Fixture climate model",
                feature_type="heat_zone",
                properties={"class": "warm"},
                state=DataState.OFFICIAL_MODELLED,
                quality=QualityFlag.VALID,
                provenance=provenance("climate-intersects"),
                spatial=SpatialReference(
                    crs="EPSG:4326",
                    geometry={
                        "type": "Polygon",
                        "coordinates": [
                            [
                                [13.39, 52.51],
                                [13.43, 52.51],
                                [13.43, 52.53],
                                [13.39, 52.53],
                                [13.39, 52.51],
                            ]
                        ],
                    },
                ),
            ),
        ),
    )
    ReferenceStateStore(path).save(state)


def client_with_reference(monkeypatch, tmp_path) -> TestClient:
    reference_path = tmp_path / "reference.json"
    write_reference(reference_path)
    monkeypatch.setenv("BUI_RUNTIME_STATE", str(tmp_path / "missing-runtime.json"))
    monkeypatch.setenv("BUI_REFERENCE_STATE", str(reference_path))
    monkeypatch.setenv("BUI_ENERGY_STATE", str(tmp_path / "missing-energy.json"))
    monkeypatch.setenv("BUI_DERIVED_STATE", str(tmp_path / "missing-derived.json"))
    return TestClient(create_app())


def test_reference_map_endpoint_filters_by_bbox_and_preserves_layer_identity(
    monkeypatch, tmp_path
) -> None:
    with client_with_reference(monkeypatch, tmp_path) as client:
        response = client.get(
            "/api/v1/map/reference",
            params={
                "west": 13.38,
                "south": 52.50,
                "east": 13.45,
                "north": 52.54,
                "layers": "facilities,stops,climate",
                "limit_per_layer": 100,
            },
        )

    assert response.status_code == 200
    body = response.json()
    assert body["type"] == "FeatureCollection"
    by_id = {feature["properties"]["id"]: feature for feature in body["features"]}
    assert set(by_id) == {
        "facility:inside",
        "stop:inside:1",
        "stop:inside:2",
        "climate:intersects",
    }
    assert by_id["facility:inside"]["properties"]["layer"] == "facilities"
    assert by_id["stop:inside:1"]["properties"]["layer"] == "stops"
    assert by_id["climate:intersects"]["properties"]["layer"] == "climate"
    assert body["metadata"]["totals"] == {"facilities": 2, "stops": 2, "climate": 1}
    assert body["metadata"]["matched"] == {"facilities": 1, "stops": 2, "climate": 1}
    assert body["metadata"]["truncated"] == {
        "facilities": False,
        "stops": False,
        "climate": False,
    }


def test_reference_map_endpoint_reports_per_layer_truncation(monkeypatch, tmp_path) -> None:
    with client_with_reference(monkeypatch, tmp_path) as client:
        response = client.get(
            "/api/v1/map/reference",
            params={
                "west": 13.38,
                "south": 52.50,
                "east": 13.45,
                "north": 52.54,
                "layers": "stops",
                "limit_per_layer": 1,
            },
        )

    assert response.status_code == 200
    body = response.json()
    assert len(body["features"]) == 1
    assert body["metadata"]["matched"]["stops"] == 2
    assert body["metadata"]["returned"]["stops"] == 1
    assert body["metadata"]["truncated"]["stops"] is True


def test_reference_map_endpoint_rejects_invalid_bounds_and_layers(monkeypatch, tmp_path) -> None:
    with client_with_reference(monkeypatch, tmp_path) as client:
        invalid_bounds = client.get(
            "/api/v1/map/reference",
            params={"west": 13.5, "south": 52.5, "east": 13.4, "north": 52.6},
        )
        invalid_layer = client.get(
            "/api/v1/map/reference",
            params={
                "west": 13.3,
                "south": 52.4,
                "east": 13.6,
                "north": 52.7,
                "layers": "facilities,unknown",
            },
        )

    assert invalid_bounds.status_code == 422
    assert "west must be smaller than east" in invalid_bounds.json()["detail"]
    assert invalid_layer.status_code == 422
    assert "unknown map layer" in invalid_layer.json()["detail"]


def test_reference_detail_endpoint_returns_full_canonical_object(monkeypatch, tmp_path) -> None:
    with client_with_reference(monkeypatch, tmp_path) as client:
        facility = client.get("/api/v1/map/reference/facilities/facility:inside")
        stop = client.get("/api/v1/map/reference/stops/stop:inside:1")
        climate = client.get("/api/v1/map/reference/climate/climate:intersects")

    assert facility.status_code == 200
    assert facility.json()["name"] == "Inside hospital"
    assert facility.json()["provenance"]["dataset"] == "map-api"
    assert stop.status_code == 200
    assert stop.json()["entity_type"] == "transport_stop"
    assert climate.status_code == 200
    assert climate.json()["properties"] == {"class": "warm"}
    assert climate.json()["provenance"]["original_identifier"] == "climate-intersects"


def test_reference_detail_endpoint_distinguishes_invalid_layer_and_missing_id(
    monkeypatch, tmp_path
) -> None:
    with client_with_reference(monkeypatch, tmp_path) as client:
        invalid_layer = client.get("/api/v1/map/reference/unknown/facility:inside")
        missing = client.get("/api/v1/map/reference/facilities/facility:missing")

    assert invalid_layer.status_code == 422
    assert "unknown map layer" in invalid_layer.json()["detail"]
    assert missing.status_code == 404
    assert "reference object not found" in missing.json()["detail"]
