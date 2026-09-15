from datetime import UTC, datetime

from berlin_urban_intelligence.agents.mobility import MobilitySnapshot
from berlin_urban_intelligence.runtime.derived_products import DerivedProductBuilder
from berlin_urban_intelligence.runtime.state import RuntimeState
from berlin_urban_intelligence.shared.contracts import (
    AvailabilityStatus,
    DataState,
    FreshnessStatus,
    Observation,
    Provenance,
    QualityFlag,
)
from berlin_urban_intelligence.shared.source_status import SourceRuntimeStatus

NOW = datetime(2026, 9, 15, 8, 0, tzinfo=UTC)


def provenance(agent: str, source_id: str) -> Provenance:
    return Provenance(
        provider="fixture",
        dataset=source_id,
        source_url="https://example.invalid/source",
        retrieved_at=NOW,
        processed_at=NOW,
        processing_method="fixture normalisation",
        agent=agent,
        agent_version="1.0.0",
    )


def observation(
    *,
    observation_id: str,
    entity_id: str,
    phenomenon: str,
    value: float | int,
    unit: str,
    agent: str,
    quality: QualityFlag = QualityFlag.VALID,
) -> Observation:
    return Observation(
        id=observation_id,
        entity_id=entity_id,
        phenomenon=phenomenon,
        value=value,
        unit=unit,
        observed_at=NOW,
        state=DataState.OBSERVED,
        quality=quality,
        provenance=provenance(agent, phenomenon),
    )


def status(source_id: str) -> SourceRuntimeStatus:
    return SourceRuntimeStatus(
        source_id=source_id,
        availability=AvailabilityStatus.AVAILABLE,
        freshness=FreshnessStatus.VALID,
        last_retrieval_attempt=NOW,
        last_successful_retrieval=NOW,
        latest_observation_time=NOW,
    )


def runtime_state() -> RuntimeState:
    return RuntimeState(
        generated_at=NOW,
        observations=(
            observation(
                observation_id="obs:temperature",
                entity_id="weather-station:dwd:00433",
                phenomenon="air_temperature_2m",
                value=29.5,
                unit="Cel",
                agent="heat",
            ),
            observation(
                observation_id="obs:lqi",
                entity_id="air-quality-station:MC042",
                phenomenon="berlin_lqi_grade",
                value=3,
                unit="1",
                agent="exposure",
                quality=QualityFlag.SUSPECT,
            ),
        ),
        mobility=MobilitySnapshot(
            observed_at=NOW,
            retrieved_at=NOW,
            trip_updates=100,
            delayed_trip_updates=25,
            max_abs_delay_s=420,
            quality=QualityFlag.VALID,
            note="fixture",
        ),
        source_statuses={
            "dwd_open_data": status("dwd_open_data"),
            "berlin_air_quality": status("berlin_air_quality"),
            "vbb_gtfs_rt": status("vbb_gtfs_rt"),
        },
    )


def test_runtime_products_preserve_real_inputs_and_avoid_composite_score() -> None:
    derived = DerivedProductBuilder().build(runtime_state())

    records = {record.definition_id: record for record in derived.records}
    mobility = records["mobility-delay-share-v1"]
    context = records["heat-air-quality-context-v1"]

    assert mobility.value == 0.25
    assert mobility.unit == "1"
    assert mobility.provenance.upstream_ids == (mobility.inputs[0].id,)

    assert context.value == {
        "temperature_c": 29.5,
        "temperature_entity_id": "weather-station:dwd:00433",
        "temperature_observed_at": NOW.isoformat(),
        "lqi_grade": 3,
        "lqi_entity_id": "air-quality-station:MC042",
        "lqi_observed_at": NOW.isoformat(),
    }
    assert {item.id for item in context.inputs} == {"obs:temperature", "obs:lqi"}
    assert context.quality is QualityFlag.SUSPECT
    assert "score" not in context.phenomenon


def test_missing_domain_data_produces_no_fabricated_record() -> None:
    state = RuntimeState(generated_at=NOW)
    derived = DerivedProductBuilder().build(state)

    assert len(derived.definitions) == 2
    assert derived.records == ()
