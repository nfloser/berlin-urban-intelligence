"""Persisted, non-live Berlin reference state.

Reference state stores authoritative entity locations and official model outputs separately from
live observations. Loading a climate layer therefore never turns it into an observation.
"""

from __future__ import annotations

import os
from datetime import UTC, datetime
from pathlib import Path

from pydantic import BaseModel, ConfigDict, Field, model_validator

from berlin_urban_intelligence.shared.contracts import CriticalFacility, NetworkEdge, NetworkNode, OfficialModelFeature, UrbanEntity


class ReferenceState(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    generated_at: datetime
    critical_facilities: tuple[CriticalFacility, ...] = ()
    official_model_features: tuple[OfficialModelFeature, ...] = ()
    transport_stops: tuple[UrbanEntity, ...] = ()
    network_nodes: tuple[NetworkNode, ...] = ()
    network_edges: tuple[NetworkEdge, ...] = ()
    errors: dict[str, str] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_time(self) -> "ReferenceState":
        if self.generated_at.tzinfo is None or self.generated_at.utcoffset() is None:
            raise ValueError("generated_at must be timezone-aware")
        object.__setattr__(self, "generated_at", self.generated_at.astimezone(UTC))
        return self


class ReferenceStateStore:
    """Atomic JSON store for retrievable, provenance-bearing Berlin reference layers."""

    def __init__(self, path: Path | str) -> None:
        self.path = Path(path)

    def save(self, state: ReferenceState) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        temporary = self.path.with_suffix(self.path.suffix + ".tmp")
        temporary.write_text(state.model_dump_json(indent=2), encoding="utf-8")
        os.replace(temporary, self.path)

    def load(self) -> ReferenceState | None:
        if not self.path.exists():
            return None
        return ReferenceState.model_validate_json(self.path.read_text(encoding="utf-8"))
