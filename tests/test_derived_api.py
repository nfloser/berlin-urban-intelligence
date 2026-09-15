from datetime import UTC, datetime

from fastapi.testclient import TestClient

from berlin_urban_intelligence.api.app import create_app
from berlin_urban_intelligence.knowledge.derivations import (
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


def definition(definition_id: str, producer: str) -> DerivationDefinition:
    return DerivationDefinition(
        id=definition_id,
        name=definition_id,
        description=f"Fixture definition for {definition_id}",
        producer_agent_id=producer,
        producer_version="1.0.0",
        algorithm_version="1.0.0",
        output_kind=definition_id,
    )


def provenance(agent: str, *upstream_ids: str) -> Provenance:
    return Provenance(
        provider="Berlin Urban Intelligence",
        dataset="derived-information",
        source_url="https://github.com/nfloser/berlin-urban-intelligence",
        retrieved_at=NOW,
        processed_at=NOW,
        processing_method="fixture",
        agent=agent,
        agent_version="1.0.0",
        upstream_ids=upstream_ids,
    )


def record(record_id: str, definition_id: str, agent: str, input_id: str) -> DerivationRecord:
    return DerivationRecord(
        id=record_id,
        definition_id=definition_id,
        entity_id="berlin:test",
        phenomenon=definition_id,
        value="fixture",
        valid_at=NOW,
        computed_at=NOW,
        quality=QualityFlag.VALID,
        freshness=FreshnessStatus.VALID,
        status=DerivationStatus.VALID,
        inputs=(DerivationInput(id=input_id, role="input"),),
        provenance=provenance(agent, input_id),
    )


def client_with_derived_state(monkeypatch, tmp_path) -> TestClient:
    derived_path = tmp_path / "derived.json"
    heat = record("derived:heat", "heat-context", "heat", "obs:temperature")
    exposure = record("derived:exposure", "exposure-context", "exposure", heat.id)
    DerivedStateStore(derived_path).save(
        DerivedState(
            generated_at=NOW,
            definitions=(
                definition("heat-context", "heat"),
                definition("exposure-context", "exposure"),
            ),
            records=(heat, exposure),
        )
    )
    monkeypatch.setenv("BUI_DERIVED_STATE", str(derived_path))
    monkeypatch.setenv("BUI_RUNTIME_STATE", str(tmp_path / "missing-runtime.json"))
    monkeypatch.setenv("BUI_REFERENCE_STATE", str(tmp_path / "missing-reference.json"))
    monkeypatch.setenv("BUI_ENERGY_STATE", str(tmp_path / "missing-energy.json"))
    return TestClient(create_app())


def test_derived_records_are_queryable_with_definition_metadata(monkeypatch, tmp_path) -> None:
    with client_with_derived_state(monkeypatch, tmp_path) as client:
        response = client.get("/api/v1/derived")
    assert response.status_code == 200
    body = response.json()
    assert [item["id"] for item in body["records"]] == ["derived:heat", "derived:exposure"]
    assert {item["id"] for item in body["definitions"]} == {"heat-context", "exposure-context"}


def test_provenance_endpoint_exposes_declared_lineage(monkeypatch, tmp_path) -> None:
    with client_with_derived_state(monkeypatch, tmp_path) as client:
        response = client.get("/api/v1/provenance/derived:exposure")
    assert response.status_code == 200
    assert response.json()["upstream_ids"] == ["derived:heat"]
    assert response.json()["agent"] == "exposure"


def test_dependency_endpoint_traverses_derived_chain(monkeypatch, tmp_path) -> None:
    with client_with_derived_state(monkeypatch, tmp_path) as client:
        response = client.get("/api/v1/dependencies/derived:exposure")
        upstream_input = client.get("/api/v1/dependencies/obs:temperature")
    assert response.status_code == 200
    assert response.json()["upstream"] == ["obs:temperature", "derived:heat"]
    assert response.json()["downstream"] == []
    assert upstream_input.json()["upstream"] == []
    assert upstream_input.json()["downstream"] == ["derived:heat", "derived:exposure"]


def test_unknown_provenance_record_is_404(monkeypatch, tmp_path) -> None:
    with client_with_derived_state(monkeypatch, tmp_path) as client:
        response = client.get("/api/v1/provenance/not-present")
    assert response.status_code == 404
