"""First-class contracts for explainable derived information."""

from __future__ import annotations

from datetime import UTC, datetime
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, model_validator

from berlin_urban_intelligence.shared.contracts import (
    DerivationStatus,
    FreshnessStatus,
    Provenance,
    QualityFlag,
)


class DerivationContext(StrEnum):
    BASELINE = "baseline"
    SCENARIO = "scenario"


class DerivationInput(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    id: str = Field(min_length=1)
    role: str = Field(min_length=1)
    required: bool = True


class DerivationDefinition(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    id: str = Field(min_length=1)
    name: str = Field(min_length=1)
    description: str = Field(min_length=1)
    producer_agent_id: str = Field(min_length=1)
    producer_version: str = Field(min_length=1)
    algorithm_version: str = Field(min_length=1)
    output_kind: str = Field(min_length=1)


class DerivationRecord(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    id: str = Field(min_length=1)
    definition_id: str = Field(min_length=1)
    entity_id: str = Field(min_length=1)
    phenomenon: str = Field(min_length=1)
    value: Any
    unit: str | None = None
    valid_at: datetime
    computed_at: datetime
    quality: QualityFlag
    freshness: FreshnessStatus
    status: DerivationStatus
    inputs: tuple[DerivationInput, ...] = Field(min_length=1)
    provenance: Provenance
    context: DerivationContext = DerivationContext.BASELINE
    scenario_id: str | None = None

    @model_validator(mode="after")
    def validate_record(self) -> DerivationRecord:
        for field_name in ("valid_at", "computed_at"):
            value = getattr(self, field_name)
            if value.tzinfo is None or value.utcoffset() is None:
                raise ValueError(f"{field_name} must be timezone-aware")
            object.__setattr__(self, field_name, value.astimezone(UTC))

        input_ids = tuple(item.id for item in self.inputs)
        if len(set(input_ids)) != len(input_ids):
            raise ValueError("derivation inputs must be unique")
        if not set(input_ids).issubset(set(self.provenance.upstream_ids)):
            raise ValueError("provenance upstream_ids must cover all declared derivation inputs")
        if self.context is DerivationContext.SCENARIO and not self.scenario_id:
            raise ValueError("scenario derivations require scenario_id")
        if self.context is DerivationContext.BASELINE and self.scenario_id is not None:
            raise ValueError("baseline derivations must not carry scenario_id")
        return self
