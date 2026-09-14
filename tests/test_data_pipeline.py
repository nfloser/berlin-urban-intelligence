from datetime import UTC, datetime, timedelta
from io import BytesIO
from zipfile import ZIP_DEFLATED, ZipFile

from rdflib import Literal
from rdflib.namespace import PROV

from berlin_urban_intelligence.adapters.berlin_air_quality import (
    extract_lqi_records,
    parse_lqi_record,
)
from berlin_urban_intelligence.adapters.dwd import DwdTenMinuteAirTemperatureClient
from berlin_urban_intelligence.agents.exposure import ExposureAgent
from berlin_urban_intelligence.knowledge.graph import BUI, KnowledgeGraph
from berlin_urban_intelligence.shared.contracts import (
    AvailabilityStatus,
    DataState,
    FreshnessStatus,
    QualityFlag,
)
from berlin_urban_intelligence.shared.source_status import SourceStatusStore

NOW = datetime(2026, 9, 14, 15, 30, tzinfo=UTC)


def test_current_berlin_lqi_station_envelope_is_normalised() -> None:
    payload = [
        {
            "station": "mc010",
            "data": [
                {
                    "component": "lqi",
                    "datetime": "2026-09-14T17:00:00+02:00",
                    "grade": 3.0,
                    "period": "1h",
                    "station": "mc010",
                    "value": 3.0,
                },
                {
                    "component": "pm10",
                    "datetime": "2026-09-14T17:00:00+02:00",
                    "grade": 2.0,
                    "period": "24h",
                    "station": "mc010",
                    "value": 2.0,
                },
                {
                    "component": "pm25",
                    "datetime": "2026-09-14T17:00:00+02:00",
                    "grade": 2.0,
                    "period": "24h",
                    "station": "mc010",
                    "value": 2.0,
                },
                {
                    "component": "no2",
                    "datetime": "2026-09-14T17:00:00+02:00",
                    "grade": 1.0,
                    "period": "1h",
                    "station": "mc010",
                    "value": 1.0,
                },
                {
                    "component": "o3",
                    "datetime": "2026-09-14T17:00:00+02:00",
                    "grade": 3.0,
                    "period": "1h",
                    "station": "mc010",
                    "value": 3.0,
                },
                {
                    "component": "co",
                    "datetime": "2026-09-14T17:00:00+02:00",
                    "grade": None,
                    "period": "8h",
                    "station": "mc010",
                    "value": None,
                },
            ],
        }
    ]

    extracted = extract_lqi_records(payload)
    assert len(extracted) == 1

    record = parse_lqi_record(extracted[0])
    assert record.station_code == "MC010"
    assert record.observed_at == datetime(2026, 9, 14, 15, 0, tzinfo=UTC)
    assert record.grade == 3
    assert record.component_grades == {"PM10": 2, "PM2.5": 2, "NO2": 1, "O3": 3}


def test_official_air_payload_flows_through_agent_into_rdf_provenance() -> None:
    record = parse_lqi_record(
        {
            "station": {"code": "MC010"},
            "timestamp": "2026-09-14T15:00:00Z",
            "lqi": 3,
            "components": {"pm10": 2, "no2": 3},
        }
    )
    agent = ExposureAgent(now_factory=lambda: NOW)
    observations = agent.ingest_lqi_records([record], retrieved_at=NOW)

    overall = next(item for item in observations if item.phenomenon == "berlin_lqi_grade")
    assert overall.state == DataState.OBSERVED
    assert overall.quality == QualityFlag.SUSPECT
    assert overall.unit == "1"
    assert overall.provenance.provider == "Berliner Luftgütemessnetz"
    assert overall.provenance.original_identifier == "MC010"

    graph = KnowledgeGraph()
    subject = graph.add_observation(overall)
    assert (subject, BUI.dataState, Literal("observed")) in graph.graph
    assert (subject, BUI.qualityFlag, Literal("suspect")) in graph.graph
    assert any(graph.graph.objects(subject, PROV.wasDerivedFrom))
    assert any(graph.graph.objects(subject, PROV.wasGeneratedBy))


def test_dwd_missing_sentinel_stays_missing() -> None:
    csv_payload = (
        "STATIONS_ID;MESS_DATUM;QN;PP_10;TT_10;TM5_10;RF_10;TD_10\n"
        "00433;202609141500;1;-999;-999;-999;-999;-999\n"
    )
    archive = BytesIO()
    with ZipFile(archive, "w", compression=ZIP_DEFLATED) as output:
        output.writestr("produkt_zehn_min_tu_20260914.txt", csv_payload)

    record = DwdTenMinuteAirTemperatureClient.parse_latest(archive.getvalue(), station_id="00433")

    assert record.temperature_c is None
    assert record.pressure_hpa is None
    assert record.near_ground_temperature_c is None
    assert record.relative_humidity_pct is None
    assert record.dew_point_c is None


def test_source_availability_failure_does_not_erase_last_success_or_fake_freshness() -> None:
    store = SourceStatusStore()
    observed_at = NOW - timedelta(hours=3)
    store.record_success("fixture-source", retrieved_at=observed_at, observation_time=observed_at)
    store.record_failure("fixture-source", checked_at=NOW, error_code="SOURCE_UNAVAILABLE")

    status = store.get("fixture-source", now=NOW, freshness_threshold=timedelta(hours=2))

    assert status.availability == AvailabilityStatus.UNAVAILABLE
    assert status.freshness == FreshnessStatus.STALE
    assert status.last_successful_retrieval == observed_at
    assert status.latest_observation_time == observed_at
    assert status.error_code == "SOURCE_UNAVAILABLE"
