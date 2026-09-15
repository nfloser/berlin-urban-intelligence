from datetime import UTC, datetime, timedelta

from berlin_urban_intelligence.knowledge.derivations import (
    DerivationDefinition,
    DerivationInput,
    DerivationRecord,
)
from berlin_urban_intelligence.knowledge.execution import DerivationExecutor
from berlin_urban_intelligence.runtime.derived import DerivedState
from berlin_urban_intelligence.shared.contracts import (
    DerivationStatus,
    FreshnessStatus,
    Provenance,
    QualityFlag,
)

NOW = datetime(2026, 9, 15, 8, 0, tzinfo=UTC)
LATER = NOW + timedelta(minutes=5)


def definition(definition_id: str, agent_id: str) -> DerivationDefinition:
    return DerivationDefinition(
        id=definition_id,
        name=definition_id,
        description=f"Fixture definition for {definition_id}.",
        producer_agent_id=agent_id,
        producer_version="1.0.0",
        algorithm_version="1.0.0",
        output_kind=definition_id,
    )


def record(
    record_id: str,
    definition_id: str,
    input_ids: tuple[str, ...],
    value: str,
) -> DerivationRecord:
    return DerivationRecord(
        id=record_id,
        definition_id=definition_id,
        entity_id="berlin:fixture",
        phenomenon=definition_id,
        value=value,
        valid_at=NOW,
        computed_at=NOW,
        quality=QualityFlag.VALID,
        freshness=FreshnessStatus.VALID,
        status=DerivationStatus.VALID,
        inputs=tuple(DerivationInput(id=input_id, role="fixture") for input_id in input_ids),
        provenance=Provenance(
            provider="Berlin Urban Intelligence",
            dataset="derived-information",
            source_url="https://github.com/nfloser/berlin-urban-intelligence",
            retrieved_at=NOW,
            processed_at=NOW,
            processing_method="deterministic fixture derivation",
            agent=definition_id,
            agent_version="1.0.0",
            upstream_ids=input_ids,
        ),
    )


def state() -> DerivedState:
    return DerivedState(
        generated_at=NOW,
        definitions=(
            definition("heat-condition", "heat"),
            definition("exposure-impact", "exposure"),
            definition("mobility-context", "mobility"),
        ),
        records=(
            record("derived:heat", "heat-condition", ("obs:temperature",), "old-heat"),
            record("derived:exposure", "exposure-impact", ("derived:heat",), "old-exposure"),
            record("derived:mobility", "mobility-context", ("obs:mobility",), "unchanged"),
        ),
    )


def test_reexecution_recomputes_only_affected_products_in_dependency_order() -> None:
    calls: list[str] = []

    def heat_handler(definition: DerivationDefinition, previous: DerivationRecord) -> DerivationRecord:
        calls.append(definition.id)
        return previous.model_copy(
            update={"value": "new-heat", "computed_at": LATER, "valid_at": LATER}
        )

    def exposure_handler(
        definition: DerivationDefinition, previous: DerivationRecord
    ) -> DerivationRecord:
        calls.append(definition.id)
        return previous.model_copy(
            update={"value": "new-exposure", "computed_at": LATER, "valid_at": LATER}
        )

    updated, report = DerivationExecutor(
        state(),
        handlers={"heat-condition": heat_handler, "exposure-impact": exposure_handler},
        now_factory=lambda: LATER,
    ).recompute(("obs:temperature",))

    assert calls == ["heat-condition", "exposure-impact"]
    assert report.recomputed == ("derived:heat", "derived:exposure")
    assert report.failed == {}
    values = {item.id: item.value for item in updated.records}
    assert values == {
        "derived:heat": "new-heat",
        "derived:exposure": "new-exposure",
        "derived:mobility": "unchanged",
    }
    assert updated.generated_at == LATER


def test_failed_derivation_isolated_and_downstream_result_becomes_unavailable() -> None:
    calls: list[str] = []

    def failing_heat(
        definition: DerivationDefinition, previous: DerivationRecord
    ) -> DerivationRecord:
        calls.append(definition.id)
        raise RuntimeError("fixture failure")

    def exposure_handler(
        definition: DerivationDefinition, previous: DerivationRecord
    ) -> DerivationRecord:
        calls.append(definition.id)
        return previous

    updated, report = DerivationExecutor(
        state(),
        handlers={"heat-condition": failing_heat, "exposure-impact": exposure_handler},
        now_factory=lambda: LATER,
    ).recompute(("obs:temperature",))

    assert calls == ["heat-condition"]
    assert report.failed == {"derived:heat": "RuntimeError: fixture failure"}
    assert report.unavailable == ("derived:exposure",)
    by_id = {item.id: item for item in updated.records}
    assert by_id["derived:heat"].status is DerivationStatus.FAILED
    assert by_id["derived:heat"].freshness is FreshnessStatus.STALE
    assert by_id["derived:exposure"].status is DerivationStatus.UNAVAILABLE
    assert by_id["derived:exposure"].freshness is FreshnessStatus.UNAVAILABLE
    assert by_id["derived:mobility"].status is DerivationStatus.VALID


def test_missing_handler_leaves_product_stale_instead_of_claiming_current_data() -> None:
    updated, report = DerivationExecutor(
        state(), handlers={}, now_factory=lambda: LATER
    ).recompute(("obs:temperature",))

    by_id = {item.id: item for item in updated.records}
    assert report.missing_handlers == ("derived:heat",)
    assert by_id["derived:heat"].status is DerivationStatus.STALE
    assert by_id["derived:heat"].freshness is FreshnessStatus.STALE
    assert by_id["derived:exposure"].status is DerivationStatus.UNAVAILABLE
