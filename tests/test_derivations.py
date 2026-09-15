from datetime import UTC, datetime

import pytest
from pydantic import ValidationError

from berlin_urban_intelligence.knowledge.derivations import (
    DerivationContext,
    DerivationDefinition,
    DerivationInput,
    DerivationRecord,
)
from berlin_urban_intelligence.runtime.derived import DerivedState, DerivedStateStore
from berlin_urban_intelligence.shared.contracts import (
    DerivationStatus,
    FreshnessStatus,
    Provenance,
    QualityFlag,
)

NOW = datetime(2026, 9, 15, 8, 0, tzinfo=UTC)


def provenance(*upstream_ids: str) -> Provenance:
    return Provenance(
        provider="Berlin Urban Intelligence",
        dataset="derived-information",
        source_url="https://github.com/nfloser/berlin-urban-intelligence",
        retrieved_at=NOW,
        processed_at=NOW,
        processing_method="deterministic fixture derivation",
        agent="heat",
        agent_version="1.0.0",
        model_version="heat-impact-v1",
        upstream_ids=upstream_ids,
    )


def definition() -> DerivationDefinition:
    return DerivationDefinition(
        id="heat-impact-v1",
        name="Heat impact context",
        description="Fixture derived information contract.",
        producer_agent_id="heat",
        producer_version="1.0.0",
        algorithm_version="1.0.0",
        output_kind="heat_impact",
    )


def record() -> DerivationRecord:
    return DerivationRecord(
        id="derived:heat:fixture",
        definition_id="heat-impact-v1",
        entity_id="weather-station:fixture",
        phenomenon="heat_impact",
        value="elevated",
        valid_at=NOW,
        computed_at=NOW,
        quality=QualityFlag.VALID,
        freshness=FreshnessStatus.VALID,
        status=DerivationStatus.VALID,
        inputs=(DerivationInput(id="obs:temperature", role="temperature"),),
        provenance=provenance("obs:temperature"),
    )


def test_record_requires_provenance_to_cover_declared_inputs() -> None:
    with pytest.raises(ValidationError, match="provenance upstream_ids"):
        DerivationRecord(
            **record().model_dump(exclude={"provenance"}),
            provenance=provenance("different:input"),
        )


def test_scenario_context_requires_scenario_id() -> None:
    with pytest.raises(ValidationError, match="scenario_id"):
        DerivationRecord(
            **record().model_dump(exclude={"context", "scenario_id"}),
            context=DerivationContext.SCENARIO,
        )


def test_derived_state_round_trip_preserves_definition_and_lineage(tmp_path) -> None:
    path = tmp_path / "derived.json"
    store = DerivedStateStore(path)
    state = DerivedState(generated_at=NOW, definitions=(definition(),), records=(record(),))

    store.save(state)

    loaded = store.load()
    assert loaded == state
    assert loaded is not None
    assert loaded.records[0].inputs[0].id == "obs:temperature"
    assert loaded.records[0].provenance.upstream_ids == ("obs:temperature",)


def test_derived_state_rejects_record_with_unknown_definition() -> None:
    with pytest.raises(ValidationError, match="unknown derivation definition"):
        DerivedState(generated_at=NOW, records=(record(),))
