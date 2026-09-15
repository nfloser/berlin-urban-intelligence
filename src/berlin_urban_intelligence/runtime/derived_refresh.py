"""Incremental refresh orchestration for persisted derived information."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from berlin_urban_intelligence.knowledge.derivations import DerivationRecord
from berlin_urban_intelligence.knowledge.execution import (
    DerivationExecutionReport,
    DerivationExecutor,
)
from berlin_urban_intelligence.runtime.derived import DerivedState
from berlin_urban_intelligence.runtime.derived_products import DerivedProductBuilder
from berlin_urban_intelligence.runtime.state import RuntimeState


@dataclass(frozen=True)
class DerivedRefreshOutcome:
    state: DerivedState
    changed: bool
    execution: DerivationExecutionReport | None = None


class DerivedRefreshCoordinator:
    """Refresh only derived branches whose source-backed semantics changed.

    A topology change (newly available or disappeared product) is applied as a validated full
    snapshot replacement. With stable topology, the dependency executor receives only the old
    upstream identifiers of products whose semantic payload changed, which gives deterministic
    cascading re-execution in dependency order.
    """

    def __init__(self, *, builder: DerivedProductBuilder | None = None) -> None:
        self.builder = builder or DerivedProductBuilder()

    @staticmethod
    def _semantic_payload(record: DerivationRecord) -> dict[str, Any]:
        payload = record.model_dump(exclude={"computed_at", "provenance"})
        payload["provenance"] = record.provenance.model_dump(
            exclude={"retrieved_at", "processed_at"}
        )
        return payload

    def refresh(
        self,
        runtime: RuntimeState,
        previous: DerivedState | None,
    ) -> DerivedRefreshOutcome:
        desired = self.builder.build(runtime)
        if previous is None:
            return DerivedRefreshOutcome(state=desired, changed=True)

        previous_definitions = {item.id for item in previous.definitions}
        desired_definitions = {item.id for item in desired.definitions}
        previous_records = {item.id: item for item in previous.records}
        desired_records = {item.id: item for item in desired.records}
        if previous_definitions != desired_definitions or set(previous_records) != set(desired_records):
            return DerivedRefreshOutcome(state=desired, changed=desired != previous)

        changed_record_ids = [
            record_id
            for record_id, candidate in desired_records.items()
            if self._semantic_payload(candidate) != self._semantic_payload(previous_records[record_id])
        ]
        if not changed_record_ids:
            return DerivedRefreshOutcome(state=previous, changed=False)

        changed_inputs = tuple(
            dict.fromkeys(
                input_item.id
                for record_id in changed_record_ids
                for input_item in previous_records[record_id].inputs
            )
        )

        def handler(_definition: object, record: DerivationRecord) -> DerivationRecord:
            return desired_records[record.id]

        handlers = {definition.id: handler for definition in desired.definitions}
        updated, execution = DerivationExecutor(
            previous,
            handlers=handlers,
            now_factory=lambda: runtime.generated_at,
        ).recompute(changed_inputs)
        return DerivedRefreshOutcome(state=updated, changed=True, execution=execution)
