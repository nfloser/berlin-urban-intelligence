"""Dependency-aware execution for persisted derived information.

The executor deliberately operates on explicit derivation records rather than hidden callbacks or
agent side effects. Only products downstream of changed inputs are considered. Failures are isolated
and downstream products are marked unavailable rather than being presented as current information.
"""

from __future__ import annotations

from collections.abc import Callable, Mapping
from datetime import UTC, datetime

from pydantic import BaseModel, ConfigDict

from berlin_urban_intelligence.knowledge.derivations import (
    DerivationDefinition,
    DerivationRecord,
)
from berlin_urban_intelligence.runtime.derived import DerivedState
from berlin_urban_intelligence.shared.contracts import DerivationStatus, FreshnessStatus

DerivationHandler = Callable[[DerivationDefinition, DerivationRecord], DerivationRecord]


class DerivationExecutionReport(BaseModel):
    """Machine-readable result of one deterministic cascade execution."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    changed_inputs: tuple[str, ...]
    affected: tuple[str, ...]
    recomputed: tuple[str, ...] = ()
    failed: dict[str, str] = {}
    unavailable: tuple[str, ...] = ()
    missing_handlers: tuple[str, ...] = ()


class DerivationExecutor:
    """Recompute only affected derived products in validated dependency order."""

    _BLOCKING_STATUSES = {
        DerivationStatus.STALE,
        DerivationStatus.RECOMPUTING,
        DerivationStatus.FAILED,
        DerivationStatus.UNAVAILABLE,
    }

    def __init__(
        self,
        state: DerivedState,
        *,
        handlers: Mapping[str, DerivationHandler],
        now_factory: Callable[[], datetime] | None = None,
    ) -> None:
        self._state = state
        self._handlers = dict(handlers)
        self._now_factory = now_factory or (lambda: datetime.now(UTC))

    def _now(self) -> datetime:
        value = self._now_factory()
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("now_factory must return a timezone-aware datetime")
        return value.astimezone(UTC)

    @staticmethod
    def _validated_candidate(
        previous: DerivationRecord,
        candidate: DerivationRecord,
    ) -> DerivationRecord:
        validated = DerivationRecord.model_validate(candidate.model_dump())
        if validated.id != previous.id:
            raise ValueError("derivation handler must preserve record id")
        if validated.definition_id != previous.definition_id:
            raise ValueError("derivation handler must preserve definition id")
        return validated

    def recompute(
        self, changed_input_ids: tuple[str, ...] | list[str]
    ) -> tuple[DerivedState, DerivationExecutionReport]:
        changed = tuple(dict.fromkeys(changed_input_ids))
        if any(not input_id for input_id in changed):
            raise ValueError("changed input ids must not be empty")

        now = self._now()
        graph = self._state.dependency_graph()
        affected = graph.affected_order(changed)
        records = {record.id: record for record in self._state.records}
        definitions = {definition.id: definition for definition in self._state.definitions}

        recomputed: list[str] = []
        failed: dict[str, str] = {}
        unavailable: list[str] = []
        missing_handlers: list[str] = []

        for record_id in affected:
            previous = records[record_id]
            blocking_inputs = [
                item.id
                for item in previous.inputs
                if item.id in records and records[item.id].status in self._BLOCKING_STATUSES
            ]
            if blocking_inputs:
                records[record_id] = previous.model_copy(
                    update={
                        "status": DerivationStatus.UNAVAILABLE,
                        "freshness": FreshnessStatus.UNAVAILABLE,
                    }
                )
                unavailable.append(record_id)
                continue

            handler = self._handlers.get(previous.definition_id)
            if handler is None:
                records[record_id] = previous.model_copy(
                    update={
                        "status": DerivationStatus.STALE,
                        "freshness": FreshnessStatus.STALE,
                    }
                )
                missing_handlers.append(record_id)
                continue

            definition = definitions[previous.definition_id]
            try:
                candidate = handler(definition, previous)
                records[record_id] = self._validated_candidate(previous, candidate)
                recomputed.append(record_id)
            except Exception as exc:
                records[record_id] = previous.model_copy(
                    update={
                        "status": DerivationStatus.FAILED,
                        "freshness": FreshnessStatus.STALE,
                    }
                )
                failed[record_id] = f"{type(exc).__name__}: {exc}"

        updated = DerivedState(
            generated_at=now,
            definitions=self._state.definitions,
            records=tuple(records[record.id] for record in self._state.records),
        )
        report = DerivationExecutionReport(
            changed_inputs=changed,
            affected=affected,
            recomputed=tuple(recomputed),
            failed=failed,
            unavailable=tuple(unavailable),
            missing_handlers=tuple(missing_handlers),
        )
        return updated, report
