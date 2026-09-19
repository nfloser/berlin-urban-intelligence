"""Persisted source-backed Berlin road-disruption state."""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from pydantic import ConfigDict, Field, model_validator

from berlin_urban_intelligence.runtime.atomic import atomic_write_text
from berlin_urban_intelligence.shared.contracts import (
    CanonicalModel,
    FreshnessStatus,
    Provenance,
    SpatialReference,
)


def _aware_utc(value: datetime, field_name: str) -> datetime:
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


class TrafficDisruption(CanonicalModel):
    """One source-backed VIZ road disruption without inferred traffic-speed effects."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    id: str = Field(min_length=1)
    subtype: str = Field(min_length=1)
    severity: str | None = None
    street: str | None = None
    section: str | None = None
    description: str = Field(min_length=1)
    direction: str | None = None
    valid_from: datetime
    valid_to: datetime
    source_updated_at: datetime
    is_future: bool | None = None
    network_reference_ids: tuple[str, ...] = ()
    is_full_closure: bool = False
    speed_penalty_factor: None = None
    spatial: SpatialReference
    provenance: Provenance

    @model_validator(mode="after")
    def validate_times_and_semantics(self) -> TrafficDisruption:
        start = _aware_utc(self.valid_from, "valid_from")
        end = _aware_utc(self.valid_to, "valid_to")
        updated = _aware_utc(self.source_updated_at, "source_updated_at")
        if end < start:
            raise ValueError("valid_to cannot be earlier than valid_from")
        object.__setattr__(self, "valid_from", start)
        object.__setattr__(self, "valid_to", end)
        object.__setattr__(self, "source_updated_at", updated)
        if self.is_full_closure != (self.severity == "Vollsperrung"):
            raise ValueError("is_full_closure must be derived exactly from severity=Vollsperrung")
        return self

    def active_at(self, when: datetime) -> bool:
        when_utc = _aware_utc(when, "when")
        return self.valid_from <= when_utc <= self.valid_to

    def model_geojson_feature(self) -> dict[str, Any]:
        return {
            "type": "Feature",
            "id": self.id,
            "properties": {
                "id": self.id,
                "subtype": self.subtype,
                "severity": self.severity,
                "street": self.street,
                "section": self.section,
                "content": self.description,
                "valid_from": self.valid_from.isoformat(),
                "valid_to": self.valid_to.isoformat(),
                "source_updated_at": self.source_updated_at.isoformat(),
                "is_full_closure": self.is_full_closure,
            },
            "geometry": self.spatial.geometry,
        }


class TrafficDisruptionState(CanonicalModel):
    """Atomic last-known-good snapshot plus explicit acquisition state."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    generated_at: datetime
    source_id: str = Field(min_length=1)
    disruptions: tuple[TrafficDisruption, ...] = ()
    last_success_at: datetime | None = None
    source_error: str | None = None
    freshness: FreshnessStatus = FreshnessStatus.UNKNOWN

    @model_validator(mode="after")
    def validate_times(self) -> TrafficDisruptionState:
        object.__setattr__(
            self,
            "generated_at",
            _aware_utc(self.generated_at, "generated_at"),
        )
        if self.last_success_at is not None:
            object.__setattr__(
                self,
                "last_success_at",
                _aware_utc(self.last_success_at, "last_success_at"),
            )
        return self


class TrafficDisruptionStateStore:
    """Atomic JSON store for current official VIZ road-disruption state."""

    def __init__(self, path: Path | str) -> None:
        self.path = Path(path)

    def save(self, state: TrafficDisruptionState) -> None:
        atomic_write_text(self.path, state.model_dump_json(indent=2))

    def load(self) -> TrafficDisruptionState | None:
        if not self.path.exists():
            return None
        return TrafficDisruptionState.model_validate_json(self.path.read_text(encoding="utf-8"))
