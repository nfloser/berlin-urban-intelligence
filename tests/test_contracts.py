from datetime import UTC, datetime

import pytest
from pydantic import ValidationError

from berlin_urban_intelligence.shared.contracts import (
    DataState,
    DerivedValue,
    Forecast,
    Observation,
    Provenance,
    QualityFlag,
    ScenarioValue,
    SpatialReference,
)

NOW = datetime(2026, 1, 15, 12, 0, tzinfo=UTC)


def provenance() -> Provenance:
    return Provenance(
        provider="fixture-provider",
        dataset="fixture-dataset",
        source_url="https://example.invalid/fixture",
        retrieved_at=NOW,
        processed_at=NOW,
        processing_method="deterministic test fixture",
        agent="fixture-agent",
        agent_version="0.0-test",
    )


def test_numeric_observation_requires_unit() -> None:
    with pytest.raises(ValidationError, match="explicit unit"):
        Observation(
            id="fixture:obs",
            entity_id="fixture:entity",
            phenomenon="temperature",
            value=20.0,
            observed_at=NOW,
            state=DataState.OBSERVED,
            quality=QualityFlag.VALID,
            provenance=provenance(),
        )


def test_observation_cannot_claim_scenario_state() -> None:
    with pytest.raises(ValidationError, match="cannot use forecast, scenario or unavailable"):
        Observation(
            id="fixture:obs",
            entity_id="fixture:entity",
            phenomenon="temperature",
            value=20.0,
            unit="Cel",
            observed_at=NOW,
            state=DataState.SCENARIO,
            quality=QualityFlag.VALID,
            provenance=provenance(),
        )


def test_naive_time_is_rejected() -> None:
    with pytest.raises(ValidationError, match="timezone-aware"):
        Observation(
            id="fixture:obs",
            entity_id="fixture:entity",
            phenomenon="temperature",
            value=20.0,
            unit="Cel",
            observed_at=datetime(2026, 1, 15, 12, 0),
            state=DataState.OBSERVED,
            quality=QualityFlag.VALID,
            provenance=provenance(),
        )


@pytest.mark.parametrize("value", [float("nan"), float("inf"), float("-inf")])
def test_observation_rejects_non_finite_numeric_values(value: float) -> None:
    with pytest.raises(ValidationError):
        Observation(
            id="fixture:obs",
            entity_id="fixture:entity",
            phenomenon="temperature",
            value=value,
            unit="Cel",
            observed_at=NOW,
            state=DataState.OBSERVED,
            quality=QualityFlag.VALID,
            provenance=provenance(),
        )


@pytest.mark.parametrize("value", [float("nan"), float("inf"), float("-inf")])
def test_derived_value_rejects_non_finite_numeric_values(value: float) -> None:
    with pytest.raises(ValidationError):
        DerivedValue(
            id="fixture:derived",
            entity_id="fixture:entity",
            phenomenon="heat_signal",
            value=value,
            unit="1",
            valid_at=NOW,
            state=DataState.DERIVED,
            quality=QualityFlag.VALID,
            provenance=provenance(),
        )


@pytest.mark.parametrize("value", [float("nan"), float("inf"), float("-inf")])
def test_forecast_rejects_non_finite_numeric_values(value: float) -> None:
    with pytest.raises(ValidationError):
        Forecast(
            id="fixture:forecast",
            entity_id="fixture:entity",
            phenomenon="load",
            value=value,
            unit="MW",
            issued_at=NOW,
            valid_at=NOW,
            quality=QualityFlag.VALID,
            provenance=provenance(),
        )


@pytest.mark.parametrize("value", [float("nan"), float("inf"), float("-inf")])
def test_scenario_value_rejects_non_finite_numeric_values(value: float) -> None:
    with pytest.raises(ValidationError):
        ScenarioValue(
            id="fixture:scenario",
            phenomenon="temperature_delta",
            value=value,
            unit="Cel",
            scenario_id="fixture:scenario-id",
        )


def test_wgs84_coordinates_are_bounded() -> None:
    with pytest.raises(ValidationError, match="outside longitude/latitude bounds"):
        SpatialReference(
            crs="EPSG:4326",
            geometry={"type": "Point", "coordinates": [300.0, 52.5]},
        )


def test_valid_wgs84_geometry_survives_validation() -> None:
    spatial = SpatialReference(
        crs="EPSG:4326",
        geometry={"type": "Point", "coordinates": [13.405, 52.52]},
    )
    assert spatial.crs == "EPSG:4326"
