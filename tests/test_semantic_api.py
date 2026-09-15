from datetime import UTC, datetime, timedelta

from fastapi.testclient import TestClient
from rdflib import Graph, URIRef
from rdflib.namespace import PROV, RDF

from berlin_urban_intelligence.agents.energy import ForecastArtifact, ModelMetric
from berlin_urban_intelligence.api.app import create_app
from berlin_urban_intelligence.energy.state import EnergyState, EnergyStateStore
from berlin_urban_intelligence.knowledge.derivations import (
    DerivationDefinition,
    DerivationInput,
    DerivationRecord,
)
from berlin_urban_intelligence.knowledge.graph import BUI, SOSA
from berlin_urban_intelligence.runtime.derived import DerivedState, DerivedStateStore
from berlin_urban_intelligence.runtime.reference import ReferenceState, ReferenceStateStore
from berlin_urban_intelligence.runtime.state import RuntimeState, RuntimeStateStore
from berlin_urban_intelligence.shared.contracts import (
    CriticalFacility,
    DataState,
    DerivationStatus,
    FreshnessStatus,
    Observation,
    Provenance,
    QualityFlag,
    SpatialReference,
)

NOW = datetime(2026, 9, 15, 10, 0, tzinfo=UTC)
RESOURCE_BASE = "https://w3id.org/berlin-urban-intelligence/resource/"


def provenance(
    *, agent: str, dataset: str = "fixture", upstream_ids: tuple[str, ...] = ()
) -> Provenance:
    return Provenance(
        provider="fixture-provider",
        dataset=dataset,
        source_url="https://example.invalid/fixture",
        retrieved_at=NOW,
        processed_at=NOW,
        processing_method="deterministic semantic API fixture",
        agent=agent,
        agent_version="1.0.0",
        upstream_ids=upstream_ids,
    )


def client_with_semantic_state(monkeypatch, tmp_path) -> TestClient:
    runtime_path = tmp_path / "runtime.json"
    reference_path = tmp_path / "reference.json"
    energy_path = tmp_path / "energy.json"
    derived_path = tmp_path / "derived.json"

    observation = Observation(
        id="obs:temperature",
        entity_id="station:fixture",
        phenomenon="air_temperature_2m",
        value=20.0,
        unit="Cel",
        observed_at=NOW,
        state=DataState.OBSERVED,
        quality=QualityFlag.VALID,
        provenance=provenance(agent="heat", dataset="temperature-fixture"),
    )
    RuntimeStateStore(runtime_path).save(
        RuntimeState(generated_at=NOW, observations=(observation,))
    )

    facility = CriticalFacility(
        id="facility:hospital",
        name="Fixture Hospital",
        category="hospital",
        quality=QualityFlag.VALID,
        provenance=provenance(agent="reference", dataset="facility-fixture"),
        spatial=SpatialReference(
            crs="EPSG:4326",
            geometry={"type": "Point", "coordinates": [13.405, 52.52]},
        ),
    )
    ReferenceStateStore(reference_path).save(
        ReferenceState(generated_at=NOW, critical_facilities=(facility,))
    )

    evaluation = ModelMetric(
        model_id="fixture-model",
        mae=1.0,
        rmse=1.2,
        evaluation_start=NOW - timedelta(days=2),
        evaluation_end=NOW - timedelta(days=1),
        dataset_fingerprint="fixture-fingerprint",
        baseline_model_id="persistence",
        baseline_mae=1.5,
    )
    forecast = ForecastArtifact(
        forecast_id="forecast:energy",
        model_id=evaluation.model_id,
        entity_id="grid:berlin",
        value=100.0,
        unit="MW",
        issued_at=NOW,
        valid_at=NOW + timedelta(hours=1),
        dataset_fingerprint=evaluation.dataset_fingerprint,
        source_dataset="energy-fixture",
        source_url="https://example.invalid/energy",
    )
    EnergyStateStore(energy_path).save(
        EnergyState(generated_at=NOW, evaluation=evaluation, forecasts=(forecast,))
    )

    definition = DerivationDefinition(
        id="context-v1",
        name="Fixture context",
        description="Semantic API fixture derivation.",
        producer_agent_id="heat",
        producer_version="1.0.0",
        algorithm_version="1.0.0",
        output_kind="fixture_context",
    )
    record = DerivationRecord(
        id="derived:context",
        definition_id=definition.id,
        entity_id="berlin:fixture",
        phenomenon="fixture_context",
        value={"temperature": 20.0},
        valid_at=NOW,
        computed_at=NOW,
        quality=QualityFlag.VALID,
        freshness=FreshnessStatus.VALID,
        status=DerivationStatus.VALID,
        inputs=(DerivationInput(id=observation.id, role="temperature"),),
        provenance=provenance(
            agent="heat",
            dataset="derived-fixture",
            upstream_ids=(observation.id,),
        ),
    )
    DerivedStateStore(derived_path).save(
        DerivedState(generated_at=NOW, definitions=(definition,), records=(record,))
    )

    monkeypatch.setenv("BUI_RUNTIME_STATE", str(runtime_path))
    monkeypatch.setenv("BUI_REFERENCE_STATE", str(reference_path))
    monkeypatch.setenv("BUI_ENERGY_STATE", str(energy_path))
    monkeypatch.setenv("BUI_DERIVED_STATE", str(derived_path))
    return TestClient(create_app())


def _relation(
    body: dict[str, object], predicate_uri: str, related_suffix: str
) -> dict[str, object]:
    relations = body["relations"]
    assert isinstance(relations, list)
    return next(
        item
        for item in relations
        if item["predicate_uri"] == predicate_uri
        and str(item["related_value"]).endswith(related_suffix)
    )


def test_graph_endpoint_includes_persisted_derived_state(monkeypatch, tmp_path) -> None:
    with client_with_semantic_state(monkeypatch, tmp_path) as client:
        response = client.get("/api/v1/graph")

    assert response.status_code == 200
    graph = Graph().parse(data=response.text, format="turtle")
    derived = URIRef(f"{RESOURCE_BASE}derived/context")
    definition = URIRef(f"{RESOURCE_BASE}derivation-definition/context-v1")
    upstream = URIRef(f"{RESOURCE_BASE}obs/temperature")

    assert (derived, RDF.type, BUI.DerivedInformation) in graph
    assert (derived, BUI.derivationDefinition, definition) in graph
    assert (derived, PROV.wasDerivedFrom, upstream) in graph


def test_relationship_endpoint_exposes_outgoing_and_incoming_semantic_links(
    monkeypatch, tmp_path
) -> None:
    with client_with_semantic_state(monkeypatch, tmp_path) as client:
        derived = client.get("/api/v1/knowledge/relations/derived:context")
        observation = client.get("/api/v1/knowledge/relations/obs:temperature")

    assert derived.status_code == 200
    derived_body = derived.json()
    assert derived_body["resource_id"] == "derived:context"
    assert derived_body["returned"] <= derived_body["total"]
    upstream = _relation(derived_body, str(PROV.wasDerivedFrom), "obs/temperature")
    assert upstream["direction"] == "outgoing"
    assert upstream["related_kind"] == "resource"

    assert observation.status_code == 200
    observation_body = observation.json()
    generated = _relation(observation_body, str(PROV.wasDerivedFrom), "derived/context")
    assert generated["direction"] == "incoming"
    assert generated["related_kind"] == "resource"


def test_relationship_endpoint_covers_observation_reference_and_forecast_resources(
    monkeypatch, tmp_path
) -> None:
    with client_with_semantic_state(monkeypatch, tmp_path) as client:
        observation = client.get("/api/v1/knowledge/relations/obs:temperature").json()
        facility = client.get("/api/v1/knowledge/relations/facility:hospital").json()
        forecast = client.get("/api/v1/knowledge/relations/forecast:energy").json()

    observed_entity = _relation(observation, str(SOSA.hasFeatureOfInterest), "station/fixture")
    assert observed_entity["related_kind"] == "resource"
    facility_type = _relation(facility, str(RDF.type), "ontology#CriticalFacility")
    assert facility_type["related_kind"] == "resource"
    forecast_type = _relation(forecast, str(RDF.type), "ontology#Forecast")
    assert forecast_type["related_kind"] == "resource"


def test_relationship_endpoint_is_bounded_and_reports_truncation(monkeypatch, tmp_path) -> None:
    with client_with_semantic_state(monkeypatch, tmp_path) as client:
        response = client.get("/api/v1/knowledge/relations/derived:context?limit=1")

    assert response.status_code == 200
    body = response.json()
    assert body["total"] > 1
    assert body["returned"] == 1
    assert body["truncated"] is True
    assert len(body["relations"]) == 1


def test_relationship_endpoint_limit_is_hard_bounded(monkeypatch, tmp_path) -> None:
    with client_with_semantic_state(monkeypatch, tmp_path) as client:
        response = client.get("/api/v1/knowledge/relations/derived:context?limit=501")
    assert response.status_code == 422


def test_relationship_endpoint_has_typed_openapi_response(monkeypatch, tmp_path) -> None:
    with client_with_semantic_state(monkeypatch, tmp_path) as client:
        schema = client.get("/openapi.json").json()

    response_schema = schema["paths"]["/api/v1/knowledge/relations/{resource_id}"]["get"][
        "responses"
    ]["200"]["content"]["application/json"]["schema"]
    assert response_schema["$ref"].endswith("/SemanticRelations")


def test_unknown_semantic_resource_is_404(monkeypatch, tmp_path) -> None:
    with client_with_semantic_state(monkeypatch, tmp_path) as client:
        response = client.get("/api/v1/knowledge/relations/not-present")
    assert response.status_code == 404


def test_semantic_relationship_lookup_without_persisted_state_is_404(monkeypatch, tmp_path) -> None:
    monkeypatch.setenv("BUI_RUNTIME_STATE", str(tmp_path / "missing-runtime.json"))
    monkeypatch.setenv("BUI_REFERENCE_STATE", str(tmp_path / "missing-reference.json"))
    monkeypatch.setenv("BUI_ENERGY_STATE", str(tmp_path / "missing-energy.json"))
    monkeypatch.setenv("BUI_DERIVED_STATE", str(tmp_path / "missing-derived.json"))

    with TestClient(create_app()) as client:
        response = client.get("/api/v1/knowledge/relations/not-present")
    assert response.status_code == 404
