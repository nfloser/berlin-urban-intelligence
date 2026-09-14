from datetime import UTC, datetime
from io import BytesIO
from zipfile import ZIP_DEFLATED, ZipFile

import pytest

from berlin_urban_intelligence.adapters.vbb_static import VbbGtfsStaticAdapter
from berlin_urban_intelligence.agents.heat import HeatAgent
from berlin_urban_intelligence.runtime.reference_refresh import ReferenceRefreshCoordinator
from berlin_urban_intelligence.shared.contracts import QualityFlag

NOW = datetime(2026, 9, 14, 16, 0, tzinfo=UTC)


class FakeWfs:
    def __init__(self, feature_types: list[str]) -> None:
        self._feature_types = feature_types
        self.requested: list[str] = []

    def feature_types(self) -> list[str]:
        return list(self._feature_types)

    def fetch_geojson(self, feature_type: str, *, count: int | None = None) -> dict[str, object]:
        del count
        self.requested.append(feature_type)
        return {
            "type": "FeatureCollection",
            "features": [
                {
                    "type": "Feature",
                    "id": f"{feature_type}.1",
                    "geometry": {"type": "Point", "coordinates": [13.4, 52.5]},
                    "properties": {"name": feature_type},
                }
            ],
        }

    def fetch_all_geojson(self, feature_type: str) -> dict[str, object]:
        return self.fetch_geojson(feature_type)


def test_reference_refresh_selects_current_official_wfs_layers() -> None:
    hospitals = FakeWfs(
        [
            "krankenhaeuser:plankrankenhaeuser",
            "krankenhaeuser:weitere_krankenhaeuser",
        ]
    )
    fire = FakeWfs(
        [
            "feuerwehr:b_feuerwehr_einsatzbereiche",
            "feuerwehr:a_feuerwehr_standorte",
        ]
    )
    climate_names = [
        f"ua_klimaanalyse_2022:{name}"
        for name in ReferenceRefreshCoordinator.CLIMATE_LAYER_LOCAL_NAMES
    ]
    climate = FakeWfs(["ua_klimaanalyse_2022:aa_ua_lufttemp_alkisgeb_2022", *climate_names])

    state = ReferenceRefreshCoordinator(
        hospital_client=hospitals,
        fire_client=fire,
        climate_client=climate,
        now_factory=lambda: NOW,
    ).refresh()

    assert state.errors == {}
    assert len([item for item in state.critical_facilities if item.category == "hospital"]) == 2
    assert len([item for item in state.critical_facilities if item.category == "fire_station"]) == 1
    assert hospitals.requested == [
        "krankenhaeuser:plankrankenhaeuser",
        "krankenhaeuser:weitere_krankenhaeuser",
    ]
    assert fire.requested == ["feuerwehr:a_feuerwehr_standorte"]
    assert climate.requested == climate_names
    assert len(state.official_model_features) == len(climate_names)


def test_invalid_official_climate_geometry_is_repaired_and_marked_suspect() -> None:
    payload = {
        "type": "FeatureCollection",
        "features": [
            {
                "type": "Feature",
                "id": "climate.1",
                "geometry": {
                    "type": "Polygon",
                    "coordinates": [
                        [
                            [13.0, 52.0],
                            [13.1, 52.1],
                            [13.1, 52.0],
                            [13.0, 52.1],
                            [13.0, 52.0],
                        ]
                    ],
                },
                "properties": {"class": "fixture"},
            }
        ],
    }

    features = HeatAgent(now_factory=lambda: NOW).ingest_official_climate_features(
        payload,
        feature_type="ua_klimaanalyse_2022:ti_kak_kaltluftabfluss_2022",
        retrieved_at=NOW,
    )

    assert len(features) == 1
    assert features[0].quality == QualityFlag.SUSPECT
    assert "shapely.make_valid" in (features[0].provenance.processing_method or "")
    assert "repaired" in (features[0].provenance.quality_note or "")


def _gtfs_archive(*, unused_size: int = 0, extra_trip_rows: int = 0) -> bytes:
    payload = BytesIO()
    with ZipFile(payload, "w", compression=ZIP_DEFLATED) as archive:
        archive.writestr(
            "stops.txt",
            "stop_id,stop_name,stop_lat,stop_lon\nde:11000:1,Example Stop,52.5,13.4\n",
        )
        archive.writestr("routes.txt", "route_id,route_short_name\nr1,R1\n")
        trips = "route_id,service_id,trip_id\nr1,s1,t1\n"
        trips += "".join(f"r1,s1,t{index + 2}\n" for index in range(extra_trip_rows))
        archive.writestr("trips.txt", trips)
        if unused_size:
            archive.writestr("shapes.txt", "x" * unused_size)
    return payload.getvalue()


def test_vbb_adapter_does_not_reject_large_unused_gtfs_members() -> None:
    adapter = VbbGtfsStaticAdapter()
    adapter.MAX_REQUIRED_UNCOMPRESSED_BYTES = 512

    snapshot = adapter.parse(_gtfs_archive(unused_size=10_000), retrieved_at=NOW)

    assert snapshot.stop_count == 1
    assert snapshot.route_count == 1
    assert snapshot.trip_count == 1


def test_vbb_adapter_still_limits_files_it_actually_decompresses() -> None:
    adapter = VbbGtfsStaticAdapter()
    adapter.MAX_REQUIRED_UNCOMPRESSED_BYTES = 256

    with pytest.raises(ValueError, match="consumed by this adapter"):
        adapter.parse(_gtfs_archive(extra_trip_rows=100), retrieved_at=NOW)
