"""Persisted derived-information state separated from live/reference/model/scenario state."""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

from pydantic import BaseModel, ConfigDict, model_validator

from berlin_urban_intelligence.knowledge.derivations import DerivationDefinition, DerivationRecord
from berlin_urban_intelligence.runtime.atomic import atomic_write_text
from berlin_urban_intelligence.shared.dependencies import DependencyGraph


class DerivedState(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    generated_at: datetime
    definitions: tuple[DerivationDefinition, ...] = ()
    records: tuple[DerivationRecord, ...] = ()

    @model_validator(mode="after")
    def validate_state(self) -> DerivedState:
        if self.generated_at.tzinfo is None or self.generated_at.utcoffset() is None:
            raise ValueError("generated_at must be timezone-aware")
        object.__setattr__(self, "generated_at", self.generated_at.astimezone(UTC))

        definition_ids = [definition.id for definition in self.definitions]
        if len(set(definition_ids)) != len(definition_ids):
            raise ValueError("derivation definition ids must be unique")
        record_ids = [record.id for record in self.records]
        if len(set(record_ids)) != len(record_ids):
            raise ValueError("derivation record ids must be unique")
        known_definitions = set(definition_ids)
        for record in self.records:
            if record.definition_id not in known_definitions:
                raise ValueError(
                    f"record {record.id} references unknown derivation definition: "
                    f"{record.definition_id}"
                )
        return self

    def dependency_graph(self) -> DependencyGraph:
        graph = DependencyGraph()
        for record in self.records:
            graph.add_derivation(record.id, tuple(item.id for item in record.inputs))
            graph.set_status(record.id, record.status)
        return graph


class DerivedStateStore:
    def __init__(self, path: Path | str) -> None:
        self.path = Path(path)

    def save(self, state: DerivedState) -> None:
        atomic_write_text(self.path, state.model_dump_json(indent=2))

    def load(self) -> DerivedState | None:
        if not self.path.exists():
            return None
        return DerivedState.model_validate_json(self.path.read_text(encoding="utf-8"))
