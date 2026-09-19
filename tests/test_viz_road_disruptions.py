from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

import pytest
from pydantic import ValidationError

from berlin_urban_intelligence.adapters.viz_road_disruptions import VizRoadDisruptionAdapter
from berlin_urban_intelligence.runtime.traffic_disruptions import (
    TrafficDisruptionState,
    TrafficDisruptionStateStore,
)

RETRIEVED_AT = datetime(2026, 9, 19, 16, 15, tzinfo=UTC)
SOURCE_URL = "https://api.viz.berlin.de/daten/baustellen_sperrungen_viz.json"


def sample_feature_collection() -> dict[str, object]:
    return {
        "type": "FeatureCollection",
        "features": [
            {
                "type": "Feature",
                "geometry": {
                    "type": "GeometryCollection",
                    "geometries": [
                        {"type": "Point", "coordinates": [13.3890, 52.5162]},
                        {
                            "type": "LineString",
                            "coordinates": [[13.3880, 52.5160], [13.3900, 52.5165]],
                        },
                    ],
                },
                "properties": {
                    "id": "viz:closure:1",
                    "subtype": "Sperrung",
                    "severity": "Vollsperrung",
                    "validity": {
                        "from": "2026-09-19T16:00",
                        "to": "2026-09-20T20:00",
                    },
                    "tstore": "2026-09-19T14:05:00Z",
                    "street": "Behrenstraße",
                    "section": "zwischen Glinkastraße und Wilhelmstraße",
                    "content": "Vollsperrung für den Kfz-Verkehr",
                },
            },
            {
                "type": "Feature",
                "id": "viz:works:2",
                "geometry": {
                    "type": "Point",
                    "coordinates": [13.4050, 52.5200],
                },
                "properties": {
                    "id": "viz:works:2",
                    "subtype": "Baustelle",
                    "severity": "keine Sperrung",
                    "validity": {
                        "from": "2026-09-19T17:00",
                        "to": "2026-09-21T18:00",
                    },
                    "tstore": "2026-09-19T15:01:00Z",
                    "street": "Alexanderstraße",
                    "section": "Höhe Musterstraße",
                    "content": "Leitungsarbeiten",
                },
            },
        ],
    }


def test_adapter_parses_official_documented_fields_without_inventing_speed_penalty() -> None:
    disruptions = VizRoadDisruptionAdapter().parse(
        sample_feature_collection(),
        retrieved_at=RETRIEVED_AT,
        source_url=SOURCE_URL,
    )

    assert len(disruptions) == 2
    closure = disruptions[0]
    assert closure.id == "viz:closure:1"
    assert closure.subtype == "Sperrung"
    assert closure.severity == "Vollsperrung"
    assert closure.street == "Behrenstraße"
    assert closure.section == "zwischen Glinkastraße und Wilhelmstraße"
    assert closure.description == "Vollsperrung für den Kfz-Verkehr"
    assert closure.valid_from == datetime(2026, 9, 19, 14, 0, tzinfo=UTC)
    assert closure.valid_to == datetime(2026, 9, 20, 18, 0, tzinfo=UTC)
    assert closure.source_updated_at == datetime(2026, 9, 19, 14, 5, tzinfo=UTC)
    assert closure.is_full_closure is True
    assert closure.speed_penalty_factor is None
    assert closure.spatial.geometry["type"] == "GeometryCollection"
    assert closure.provenance.provider == "Verkehrsinformationszentrale Berlin (VIZ)"
    assert closure.provenance.source_licence == (
        "Datenlizenz Deutschland - Namensnennung - Version 2.0"
    )

    works = disruptions[1]
    assert works.is_full_closure is False
    assert works.speed_penalty_factor is None


def test_adapter_rejects_semantic_schema_drift() -> None:
    payload = sample_feature_collection()
    feature = payload["features"][0]
    feature["properties"]["impact"] = feature["properties"].pop("severity")

    with pytest.raises(ValueError, match="severity"):
        VizRoadDisruptionAdapter().parse(
            payload,
            retrieved_at=RETRIEVED_AT,
            source_url=SOURCE_URL,
        )


def test_adapter_rejects_invalid_or_missing_validity() -> None:
    payload = sample_feature_collection()
    payload["features"][0]["properties"]["validity"] = {
        "from": "2026-09-20T22:00",
        "to": "2026-09-19T22:00",
    }

    with pytest.raises((ValueError, ValidationError)):
        VizRoadDisruptionAdapter().parse(
            payload,
            retrieved_at=RETRIEVED_AT,
            source_url=SOURCE_URL,
        )


def test_traffic_disruption_state_roundtrips_atomically(tmp_path: Path) -> None:
    disruptions = VizRoadDisruptionAdapter().parse(
        sample_feature_collection(),
        retrieved_at=RETRIEVED_AT,
        source_url=SOURCE_URL,
    )
    state = TrafficDisruptionState(
        generated_at=RETRIEVED_AT,
        source_id="berlin_viz_road_disruptions",
        disruptions=disruptions,
    )
    path = tmp_path / "traffic-disruptions.json"
    store = TrafficDisruptionStateStore(path)

    store.save(state)
    loaded = store.load()

    assert loaded == state
    assert path.exists()
    assert not path.with_suffix(".json.tmp").exists()


def test_adapter_accepts_landesmeldestelle_german_local_time_variant() -> None:
    payload = sample_feature_collection()
    payload["features"][0]["properties"]["validity"] = {
        "from": "19.09.2026 16:00",
        "to": "20.09.2026 20:00",
    }

    disruptions = VizRoadDisruptionAdapter().parse(
        payload,
        retrieved_at=RETRIEVED_AT,
        source_url="https://api.viz.berlin.de/tic3/baustellen_sperrungen_tic.json",
    )

    assert disruptions[0].valid_from == datetime(2026, 9, 19, 14, 0, tzinfo=UTC)
