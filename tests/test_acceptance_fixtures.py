from berlin_urban_intelligence.shared.contracts import (
    AvailabilityStatus,
    DerivationStatus,
    FreshnessStatus,
)
from scripts.write_acceptance_fixtures import build_derived_fixture, build_runtime_fixture


def test_runtime_acceptance_fixture_exposes_explicit_source_failure_semantics() -> None:
    runtime = build_runtime_fixture()

    status = runtime.source_statuses["berlin_air_quality"]
    assert status.availability is AvailabilityStatus.UNAVAILABLE
    assert status.freshness is FreshnessStatus.STALE
    assert status.error_code == "SOURCE_UNAVAILABLE"
    assert status.last_successful_retrieval is not None
    assert status.latest_observation_time is not None
    assert runtime.errors == {}


def test_derived_acceptance_fixture_exposes_lineage_without_production_fallback() -> None:
    derived = build_derived_fixture()

    assert len(derived.definitions) == 1
    definition = derived.definitions[0]
    assert definition.name == "Acceptance mobility delay share"
    assert definition.producer_agent_id == "mobility"

    assert len(derived.records) == 1
    record = derived.records[0]
    assert record.definition_id == definition.id
    assert record.freshness is FreshnessStatus.STALE
    assert record.status is DerivationStatus.VALID
    assert [item.id for item in record.inputs] == ["observation:acceptance:mobility-input"]
    assert record.provenance.upstream_ids == ("observation:acceptance:mobility-input",)
    assert record.provenance.provider == "Berlin Urban Intelligence acceptance fixture"
    assert record.provenance.dataset == "acceptance derived lineage"
    assert "Synthetic test fixture" in (record.provenance.quality_note or "")
