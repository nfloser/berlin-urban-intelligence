"""Incremental refresh orchestration for persisted derived information."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any

from berlin_urban_intelligence.knowledge.derivations import (
    DerivationDefinition,
    DerivationRecord,
)
from berlin_urban_intelligence.knowledge.execution import (
    DerivationExecutionReport,
    DerivationExecutor,
)
from berlin_urban_intelligence.runtime.derived import DerivedState
from berlin_urban_intelligence.runtime.derived_products import DerivedProductBuilder
from berlin_urban_intelligence.runtime.state import RuntimeState
from berlin_urban_intelligence.shared.observability import observe_operation

LOGGER = logging.getLogger("berlin_urban_intelligence.runtime.derived_refresh")


@dataclass(frozen=True)
class DerivedRefreshOutcome:
    state: DerivedState
    changed: bool
    execution: DerivationExecutionReport | None = None


class DerivedRefreshCoordinator:
    """Refresh only derived branches whose source-backed semantics changed.

    A topology change (newly available or disappeared product) is applied as a validated full
    snapshot replacement. With stable topology, the dependency executor receives a minimal set of
    upstream identifiers that explains changed records without invalidating branches whose desired
    semantic payload is unchanged.
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

    @staticmethod
    def _changed_input_ids(
        *,
        changed_record_ids: list[str],
        previous_records: dict[str, DerivationRecord],
    ) -> tuple[str, ...]:
        """Infer the narrowest external-input seed consistent with the desired snapshot.

        An input shared with a semantically unchanged record is not used to invalidate that branch:
        the freshly built desired snapshot already demonstrates that branch remained equivalent.
        If every input is shared, fall back to all inputs of changed records so a real change is
        never silently suppressed.
        """
        changed = set(changed_record_ids)
        unchanged_inputs = {
            input_item.id
            for record_id, record in previous_records.items()
            if record_id not in changed
            for input_item in record.inputs
        }
        all_changed_inputs = tuple(
            dict.fromkeys(
                input_item.id
                for record_id in changed_record_ids
                for input_item in previous_records[record_id].inputs
            )
        )
        narrowed = tuple(
            input_id for input_id in all_changed_inputs if input_id not in unchanged_inputs
        )
        return narrowed or all_changed_inputs

    def refresh(
        self,
        runtime: RuntimeState,
        previous: DerivedState | None,
    ) -> DerivedRefreshOutcome:
        with observe_operation(
            LOGGER,
            "derivation_refresh",
            agent="derived",
            source="runtime_state",
        ):
            return self._refresh(runtime, previous)

    def _refresh(
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
        if previous_definitions != desired_definitions or set(previous_records) != set(
            desired_records
        ):
            return DerivedRefreshOutcome(state=desired, changed=desired != previous)

        changed_record_ids = [
            record_id
            for record_id, candidate in desired_records.items()
            if self._semantic_payload(candidate)
            != self._semantic_payload(previous_records[record_id])
        ]
        if not changed_record_ids:
            return DerivedRefreshOutcome(state=previous, changed=False)

        changed_inputs = self._changed_input_ids(
            changed_record_ids=changed_record_ids,
            previous_records=previous_records,
        )

        def handler(
            _definition: DerivationDefinition, record: DerivationRecord
        ) -> DerivationRecord:
            return desired_records[record.id]

        handlers = {definition.id: handler for definition in desired.definitions}
        updated, execution = DerivationExecutor(
            previous,
            handlers=handlers,
            now_factory=lambda: runtime.generated_at,
        ).recompute(changed_inputs)
        return DerivedRefreshOutcome(state=updated, changed=True, execution=execution)
