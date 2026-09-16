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


def status(
    source_id: str,
    *,
    availability: AvailabilityStatus = AvailabilityStatus.AVAILABLE,
    freshness: FreshnessStatus = FreshnessStatus.VALID,
) -> SourceRuntimeStatus:
    return SourceRuntimeStatus(
        source_id=source_id,
        availability=availability,
        freshness=freshness,
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


def test_mobility_air_quality_context_is_descriptive_and_traceable() -> None:
    derived = DerivedProductBuilder().build(runtime_state())
    records = {record.definition_id: record for record in derived.records}

    context = records["mobility-air-quality-context-v1"]
    mobility_input = f"vbb-gtfs-rt:{NOW.isoformat()}"

    assert context.value == {
        "delayed_trip_update_share": 0.25,
        "mobility_trip_updates": 100,
        "mobility_delayed_trip_updates": 25,
        "mobility_observed_at": NOW.isoformat(),
        "lqi_grade": 3,
        "lqi_entity_id": "air-quality-station:MC042",
        "lqi_observed_at": NOW.isoformat(),
    }
    assert {item.id for item in context.inputs} == {mobility_input, "obs:lqi"}
    assert set(context.provenance.upstream_ids) == {mobility_input, "obs:lqi"}
    assert context.quality is QualityFlag.SUSPECT
    assert context.freshness is FreshnessStatus.VALID
    assert "score" not in context.phenomenon


def test_cross_domain_context_propagates_stale_source_freshness() -> None:
    state = runtime_state()
    source_statuses = dict(state.source_statuses)
    source_statuses["vbb_gtfs_rt"] = status(
        "vbb_gtfs_rt",
        freshness=FreshnessStatus.STALE,
    )
    stale = state.model_copy(update={"source_statuses": source_statuses})

    derived = DerivedProductBuilder().build(stale)
    records = {record.definition_id: record for record in derived.records}

    assert records["mobility-air-quality-context-v1"].freshness is FreshnessStatus.STALE
    assert records["mobility-delay-share-v1"].freshness is FreshnessStatus.STALE
    assert records["heat-air-quality-context-v1"].freshness is FreshnessStatus.VALID


def test_cross_domain_context_exposes_last_known_data_during_source_failure() -> None:
    state = runtime_state()
    source_statuses = dict(state.source_statuses)
    source_statuses["berlin_air_quality"] = status(
        "berlin_air_quality",
        availability=AvailabilityStatus.UNAVAILABLE,
        freshness=FreshnessStatus.UNAVAILABLE,
    )
    degraded = state.model_copy(update={"source_statuses": source_statuses})

    derived = DerivedProductBuilder().build(degraded)
    records = {record.definition_id: record for record in derived.records}

    assert records["mobility-air-quality-context-v1"].freshness is FreshnessStatus.UNAVAILABLE
    assert records["heat-air-quality-context-v1"].freshness is FreshnessStatus.UNAVAILABLE


def test_missing_mobility_input_omits_only_the_mobility_cross_domain_context() -> None:
    state = runtime_state().model_copy(update={"mobility": None})

    derived = DerivedProductBuilder().build(state)
    definition_ids = {record.definition_id for record in derived.records}

    assert "heat-air-quality-context-v1" in definition_ids
    assert "mobility-air-quality-context-v1" not in definition_ids
    assert "mobility-delay-share-v1" not in definition_ids


def test_missing_lqi_omits_cross_domain_contexts_without_hiding_mobility() -> None:
    state = runtime_state()
    without_lqi = state.model_copy(
        update={
            "observations": tuple(
                item for item in state.observations if item.phenomenon != "berlin_lqi_grade"
            )
        }
    )

    derived = DerivedProductBuilder().build(without_lqi)
    definition_ids = {record.definition_id for record in derived.records}

    assert "mobility-delay-share-v1" in definition_ids
    assert "heat-air-quality-context-v1" not in definition_ids
    assert "mobility-air-quality-context-v1" not in definition_ids


def test_missing_domain_data_produces_no_fabricated_record() -> None:
    state = RuntimeState(generated_at=NOW)
    derived = DerivedProductBuilder().build(state)

    assert len(derived.definitions) == 3
    assert derived.records == ()
