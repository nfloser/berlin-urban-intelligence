"""Versioned canonical contracts shared across all agents.

The contracts deliberately carry epistemic state, quality and provenance alongside values.
A number without those fields is not a valid cross-agent observation in this project.
"""

from __future__ import annotations

from datetime import UTC, datetime
from enum import StrEnum
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, HttpUrl, model_validator
from pyproj import CRS
from shapely.geometry import shape

CONTRACT_VERSION = "1.0.0"


class DataState(StrEnum):
    OBSERVED = "observed"
    OFFICIAL_MODELLED = "official_modelled"
    PROJECT_MODELLED = "project_modelled"
    FORECAST = "forecast"
    DERIVED = "derived"
    INTERPOLATED = "interpolated"
    SCENARIO = "scenario"
    UNKNOWN = "unknown"
    UNAVAILABLE = "unavailable"
    STALE = "stale"


class QualityFlag(StrEnum):
    VALID = "valid"
    SUSPECT = "suspect"
    PARTIAL = "partial"
    STALE = "stale"
    INVALID = "invalid"
    UNKNOWN = "unknown"


class AvailabilityStatus(StrEnum):
    AVAILABLE = "available"
    DEGRADED = "degraded"
    UNAVAILABLE = "unavailable"
    UNKNOWN = "unknown"


class FreshnessStatus(StrEnum):
    VALID = "valid"
    STALE = "stale"
    UNKNOWN = "unknown"
    UNAVAILABLE = "unavailable"


class DerivationStatus(StrEnum):
    VALID = "valid"
    STALE = "stale"
    RECOMPUTING = "recomputing"
    FAILED = "failed"
    UNAVAILABLE = "unavailable"


class CanonicalModel(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    contract_version: str = CONTRACT_VERSION


def _require_aware(value: datetime, field_name: str) -> datetime:
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


class Provenance(CanonicalModel):
    provider: str = Field(min_length=1)
    dataset: str = Field(min_length=1)
    source_url: HttpUrl
    original_identifier: str | None = None
    observation_time: datetime | None = None
    retrieved_at: datetime
    processed_at: datetime
    processing_method: str | None = None
    agent: str = Field(min_length=1)
    agent_version: str = Field(min_length=1)
    model_version: str | None = None
    source_licence: str | None = None
    quality_note: str | None = None
    upstream_ids: tuple[str, ...] = ()

    @model_validator(mode="after")
    def validate_times(self) -> "Provenance":
        for name in ("observation_time", "retrieved_at", "processed_at"):
            value = getattr(self, name)
            if value is not None:
                object.__setattr__(self, name, _require_aware(value, name))
        if self.processed_at < self.retrieved_at:
            raise ValueError("processed_at cannot be earlier than retrieved_at")
        return self


class SpatialReference(CanonicalModel):
    crs: str = Field(default="EPSG:4326", min_length=1)
    geometry: dict[str, Any] | None = None

    @model_validator(mode="after")
    def validate_spatial_reference(self) -> "SpatialReference":
        try:
            crs = CRS.from_user_input(self.crs)
        except Exception as exc:
            raise ValueError(f"unknown CRS: {self.crs}") from exc
        if self.geometry is None:
            return self
        try:
            geometry = shape(self.geometry)
        except Exception as exc:
            raise ValueError("geometry must be valid GeoJSON geometry") from exc
        if geometry.is_empty or not geometry.is_valid:
            raise ValueError("geometry must be non-empty and geometrically valid")
        if crs.to_epsg() == 4326:
            min_x, min_y, max_x, max_y = geometry.bounds
            if min_x < -180 or max_x > 180 or min_y < -90 or max_y > 90:
                raise ValueError("EPSG:4326 geometry coordinates are outside longitude/latitude bounds")
        return self


class TimeInterval(CanonicalModel):
    start: datetime
    end: datetime

    @model_validator(mode="after")
    def validate_interval(self) -> "TimeInterval":
        object.__setattr__(self, "start", _require_aware(self.start, "start"))
        object.__setattr__(self, "end", _require_aware(self.end, "end"))
        if self.end < self.start:
            raise ValueError("end cannot be earlier than start")
        return self


class UrbanEntity(CanonicalModel):
    id: str = Field(min_length=1)
    entity_type: str = Field(min_length=1)
    name: str | None = None
    spatial: SpatialReference | None = None
    source_identifier: str | None = None


class Observation(CanonicalModel):
    id: str = Field(min_length=1)
    entity_id: str = Field(min_length=1)
    phenomenon: str = Field(min_length=1)
    value: float | int | str | bool
    unit: str | None = None
    observed_at: datetime
    state: DataState
    quality: QualityFlag
    provenance: Provenance
    spatial: SpatialReference | None = None

    @model_validator(mode="after")
    def validate_observation(self) -> "Observation":
        object.__setattr__(self, "observed_at", _require_aware(self.observed_at, "observed_at"))
        if isinstance(self.value, (int, float)) and not isinstance(self.value, bool) and not self.unit:
            raise ValueError("numeric observations require an explicit unit")
        if self.state in {DataState.FORECAST, DataState.SCENARIO, DataState.UNAVAILABLE}:
            raise ValueError("Observation cannot use forecast, scenario or unavailable data state")
        return self


class DerivedValue(CanonicalModel):
    id: str = Field(min_length=1)
    entity_id: str = Field(min_length=1)
    phenomenon: str = Field(min_length=1)
    value: float | int | str | bool
    unit: str | None = None
    valid_at: datetime
    state: Literal[DataState.DERIVED, DataState.INTERPOLATED, DataState.PROJECT_MODELLED]
    quality: QualityFlag
    provenance: Provenance
    dependencies: tuple[str, ...] = ()
    derivation_status: DerivationStatus = DerivationStatus.VALID

    @model_validator(mode="after")
    def validate_value(self) -> "DerivedValue":
        object.__setattr__(self, "valid_at", _require_aware(self.valid_at, "valid_at"))
        if isinstance(self.value, (int, float)) and not isinstance(self.value, bool) and not self.unit:
            raise ValueError("numeric derived values require an explicit unit")
        return self


class Forecast(CanonicalModel):
    id: str = Field(min_length=1)
    entity_id: str = Field(min_length=1)
    phenomenon: str = Field(min_length=1)
    value: float
    unit: str
    issued_at: datetime
    valid_at: datetime
    state: Literal[DataState.FORECAST] = DataState.FORECAST
    quality: QualityFlag
    provenance: Provenance
    lower_bound: float | None = None
    upper_bound: float | None = None

    @model_validator(mode="after")
    def validate_forecast(self) -> "Forecast":
        object.__setattr__(self, "issued_at", _require_aware(self.issued_at, "issued_at"))
        object.__setattr__(self, "valid_at", _require_aware(self.valid_at, "valid_at"))
        if self.valid_at < self.issued_at:
            raise ValueError("valid_at cannot be earlier than issued_at")
        if (self.lower_bound is None) != (self.upper_bound is None):
            raise ValueError("forecast uncertainty bounds must be supplied together")
        if self.lower_bound is not None and not (self.lower_bound <= self.value <= self.upper_bound):
            raise ValueError("forecast value must lie inside uncertainty bounds")
        return self


class ScenarioValue(CanonicalModel):
    id: str = Field(min_length=1)
    phenomenon: str = Field(min_length=1)
    value: float | int | str | bool
    unit: str | None = None
    state: Literal[DataState.SCENARIO] = DataState.SCENARIO
    scenario_id: str = Field(min_length=1)


class OfficialModelFeature(CanonicalModel):
    id: str = Field(min_length=1)
    entity_id: str = Field(min_length=1)
    model_name: str = Field(min_length=1)
    feature_type: str = Field(min_length=1)
    properties: dict[str, Any] = Field(default_factory=dict)
    state: Literal[DataState.OFFICIAL_MODELLED] = DataState.OFFICIAL_MODELLED
    quality: QualityFlag
    provenance: Provenance
    spatial: SpatialReference


class NetworkNode(CanonicalModel):
    id: str = Field(min_length=1)
    longitude: float | None = Field(default=None, ge=-180, le=180)
    latitude: float | None = Field(default=None, ge=-90, le=90)
    provenance: Provenance | None = None

    @model_validator(mode="after")
    def validate_coordinates(self) -> "NetworkNode":
        if (self.longitude is None) != (self.latitude is None):
            raise ValueError("longitude and latitude must be supplied together")
        return self


class NetworkEdge(CanonicalModel):
    id: str = Field(min_length=1)
    source: str = Field(min_length=1)
    target: str = Field(min_length=1)
    travel_time_s: float = Field(gt=0)
    length_m: float = Field(gt=0)
    bidirectional: bool = True
    provenance: Provenance | None = None


class CriticalFacility(UrbanEntity):
    entity_type: str = "critical_facility"
    category: str
    confidence: str | None = None
    quality: QualityFlag = QualityFlag.UNKNOWN
    provenance: Provenance | None = None


class AgentDescriptor(CanonicalModel):
    id: str
    version: str
    description: str
    capabilities: tuple[str, ...]
    input_contracts: tuple[str, ...] = ()
    output_contracts: tuple[str, ...] = ()
    source_dependencies: tuple[str, ...] = ()


class AgentHealth(CanonicalModel):
    agent_id: str
    status: AvailabilityStatus
    checked_at: datetime
    freshness: FreshnessStatus = FreshnessStatus.UNKNOWN
    quality: QualityFlag = QualityFlag.UNKNOWN
    detail: str | None = None

    @model_validator(mode="after")
    def validate_checked_at(self) -> "AgentHealth":
        object.__setattr__(self, "checked_at", _require_aware(self.checked_at, "checked_at"))
        return self
