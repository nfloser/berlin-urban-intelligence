"""Atomic persistence for evaluated Berlin energy models and forecast artefacts."""

from __future__ import annotations

import os
from datetime import UTC, datetime
from pathlib import Path

from pydantic import BaseModel, ConfigDict, model_validator

from berlin_urban_intelligence.agents.energy import ForecastArtifact, ModelMetric


class EnergyState(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    generated_at: datetime
    evaluation: ModelMetric
    forecasts: tuple[ForecastArtifact, ...] = ()
    notes: tuple[str, ...] = ()

    @model_validator(mode="after")
    def validate_state(self) -> EnergyState:
        if self.generated_at.tzinfo is None or self.generated_at.utcoffset() is None:
            raise ValueError("generated_at must be timezone-aware")
        object.__setattr__(self, "generated_at", self.generated_at.astimezone(UTC))
        for forecast in self.forecasts:
            if forecast.model_id != self.evaluation.model_id:
                raise ValueError("persisted forecast model_id must match evaluation model_id")
            if forecast.dataset_fingerprint != self.evaluation.dataset_fingerprint:
                raise ValueError("persisted forecast fingerprint must match evaluation fingerprint")
        return self


class EnergyStateStore:
    """Write energy artefacts atomically so incomplete files are never served by the API."""

    def __init__(self, path: Path | str) -> None:
        self.path = Path(path)

    def save(self, state: EnergyState) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        temporary = self.path.with_suffix(self.path.suffix + ".tmp")
        temporary.write_text(state.model_dump_json(indent=2), encoding="utf-8")
        os.replace(temporary, self.path)

    def load(self) -> EnergyState | None:
        if not self.path.exists():
            return None
        return EnergyState.model_validate_json(self.path.read_text(encoding="utf-8"))
