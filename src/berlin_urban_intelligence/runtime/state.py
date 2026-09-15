"""Persisted canonical runtime state."""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

from pydantic import BaseModel, ConfigDict, Field, model_validator

from berlin_urban_intelligence.agents.mobility import MobilitySnapshot
from berlin_urban_intelligence.runtime.atomic import atomic_write_text
from berlin_urban_intelligence.shared.contracts import Observation
from berlin_urban_intelligence.shared.source_status import SourceRuntimeStatus


class RuntimeState(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    generated_at: datetime
    observations: tuple[Observation, ...] = ()
    mobility: MobilitySnapshot | None = None
    source_statuses: dict[str, SourceRuntimeStatus] = Field(default_factory=dict)
    errors: dict[str, str] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_time(self) -> RuntimeState:
        if self.generated_at.tzinfo is None or self.generated_at.utcoffset() is None:
            raise ValueError("generated_at must be timezone-aware")
        object.__setattr__(self, "generated_at", self.generated_at.astimezone(UTC))
        return self


class RuntimeStateStore:
    """Atomic JSON store for the latest canonical runtime state."""

    def __init__(self, path: Path | str) -> None:
        self.path = Path(path)

    def save(self, state: RuntimeState) -> None:
        atomic_write_text(self.path, state.model_dump_json(indent=2))

    def load(self) -> RuntimeState | None:
        if not self.path.exists():
            return None
        return RuntimeState.model_validate_json(self.path.read_text(encoding="utf-8"))
