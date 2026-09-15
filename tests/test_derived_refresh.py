from datetime import UTC, datetime, timedelta

from berlin_urban_intelligence.agents.mobility import MobilitySnapshot
from berlin_urban_intelligence.runtime.derived_products import DerivedProductBuilder
from berlin_urban_intelligence.runtime.derived_refresh import DerivedRefreshCoordinator
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
LATER = NOW + timedelta(minutes=5)


def _provenance(agent: str) -> Provenance:
    return Provenance(
        provider="fixture",
        dataset="fixture",
        source_url="https://example.invalid/source",
        retrieved_at=NOW,
        processed_at=NOW,
        processing_method="fixture",
        agent=agent,
        agent_version="1.0.0",
    )


def _status(source_id: str) -> SourceRuntimeStatus:
    return SourceRuntimeStatus(
        source_id=source_id,
        availability=AvailabilityStatus.AVAILABLE,
        freshness=FreshnessStatus.VALID,
        latest_observation_time=NOW,
    )


def _runtime(*, generated_at: datetime, delayed: int) -> RuntimeState:
    return RuntimeState(
        generated_at=generated_at,
        observations=(
            Observation(
                id="obs:temperature",
                entity_id="weather:fixture",
                phenomenon="air_temperature_2m",
                value=30.0,
                unit="Cel",
                observed_at=NOW,
                state=DataState.OBSERVED,
                quality=QualityFlag.VALID,
                provenance=_provenance("heat"),
            ),
            Observation(
                id="obs:lqi",
                entity_id="air:fixture",
                phenomenon="berlin_lqi_grade",
                value=2,
                unit="1",
                observed_at=NOW,
                state=DataState.OBSERVED,
                quality=QualityFlag.SUSPECT,
                provenance=_provenance("exposure"),
            ),
        ),
        mobility=MobilitySnapshot(
            observed_at=NOW,
            retrieved_at=NOW,
            trip_updates=100,
            delayed_trip_updates=delayed,
            max_abs_delay_s=120,
            quality=QualityFlag.VALID,
            note="fixture",
        ),
        source_statuses={
            "dwd_open_data": _status("dwd_open_data"),
            "berlin_air_quality": _status("berlin_air_quality"),
            "vbb_gtfs_rt": _status("vbb_gtfs_rt"),
        },
    )


def test_only_changed_derived_branch_is_recomputed() -> None:
    builder = DerivedProductBuilder()
    previous = builder.build(_runtime(generated_at=NOW, delayed=25))

    outcome = DerivedRefreshCoordinator(builder=builder).refresh(
        _runtime(generated_at=LATER, delayed=50), previous
    )

    assert outcome.changed is True
    assert outcome.execution is not None
    assert outcome.execution.recomputed == ("derived:mobility:delay-share:current",)
    records = {record.id: record for record in outcome.state.records}
    assert records["derived:mobility:delay-share:current"].value == 0.5
    assert records["derived:mobility:delay-share:current"].computed_at == LATER
    assert records["derived:context:heat-air-quality:current"].computed_at == NOW


def test_runtime_timestamp_only_does_not_rewrite_derived_snapshot() -> None:
    builder = DerivedProductBuilder()
    previous = builder.build(_runtime(generated_at=NOW, delayed=25))

    outcome = DerivedRefreshCoordinator(builder=builder).refresh(
        _runtime(generated_at=LATER, delayed=25), previous
    )

    assert outcome.changed is False
    assert outcome.execution is None
    assert outcome.state == previous
