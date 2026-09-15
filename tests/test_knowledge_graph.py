from datetime import UTC, datetime

from rdflib.namespace import PROV, RDF

from berlin_urban_intelligence.knowledge.derived_graph import project_derived_state
from berlin_urban_intelligence.knowledge.derivations import (
    DerivationDefinition,
    DerivationInput,
    DerivationRecord,
)
from berlin_urban_intelligence.knowledge.graph import BUI, KnowledgeGraph
from berlin_urban_intelligence.runtime.derived import DerivedState
from berlin_urban_intelligence.shared.contracts import (
    DataState,
    DerivationStatus,
    FreshnessStatus,
    Observation,
    Provenance,
    QualityFlag,
)

NOW = datetime(2026, 2, 1, 10, 0, tzinfo=UTC)


def test_observation_projection_preserves_state_and_provenance() -> None:
    provenance = Provenance(
        provider="fixture-provider",
        dataset="fixture-dataset",
        source_url="https://example.invalid/fixture",
        original_identifier="fixture-source-id",
        observation_time=NOW,
        retrieved_at=NOW,
        processed_at=NOW,
        processing_method="deterministic fixture mapping",
        agent="fixture-agent",
        agent_version="0.0-test",
    )
    observation = Observation(
        id="fixture:observation",
        entity_id="fixture:entity",
        phenomenon="fixture_temperature",
        value=20.0,
        unit="Cel",
        observed_at=NOW,
        state=DataState.OBSERVED,
        quality=QualityFlag.VALID,
        provenance=provenance,
    )
    graph = KnowledgeGraph()
    subject = graph.add_observation(observation)
    assert (subject, RDF.type, BUI.Observation) in graph.graph
    assert any(
        predicate == PROV.wasGeneratedBy
        for _, predicate, _ in graph.graph.triples((subject, None, None))
    )
    assert "observed" in graph.serialize()
    assert "fixture-provider" in graph.serialize()


def test_provenance_source_with_human_readable_names_serializes_as_valid_uri() -> None:
    provenance = Provenance(
        provider="Senatsverwaltung für Stadtentwicklung",
        dataset="Klimaanalysekarten 2022 (Umweltatlas)",
        source_url="https://example.invalid/climate",
        retrieved_at=NOW,
        processed_at=NOW,
        processing_method="fixture mapping",
        agent="fixture-agent",
        agent_version="0.0-test",
    )
    observation = Observation(
        id="fixture:observation:source-name",
        entity_id="fixture:entity",
        phenomenon="fixture_temperature",
        value=20.0,
        unit="Cel",
        observed_at=NOW,
        state=DataState.OBSERVED,
        quality=QualityFlag.VALID,
        provenance=provenance,
    )
    serialized = KnowledgeGraph()
    serialized.add_observation(observation)
    assert "Senatsverwaltung%20f%C3%BCr%20Stadtentwicklung" in serialized.serialize()


def test_derived_projection_exposes_definition_status_and_upstream_lineage() -> None:
    definition = DerivationDefinition(
        id="fixture-definition-v1",
        name="Fixture derivation",
        description="Deterministic semantic projection fixture.",
        producer_agent_id="fixture-agent",
        producer_version="1.0.0",
        algorithm_version="1.0.0",
        output_kind="fixture_context",
    )
    record = DerivationRecord(
        id="derived:fixture",
        definition_id=definition.id,
        entity_id="fixture:entity",
        phenomenon="fixture_context",
        value={"temperature": 20.0, "lqi": 2},
        valid_at=NOW,
        computed_at=NOW,
        quality=QualityFlag.VALID,
        freshness=FreshnessStatus.VALID,
        status=DerivationStatus.VALID,
        inputs=(DerivationInput(id="fixture:observation", role="temperature"),),
        provenance=Provenance(
            provider="Berlin Urban Intelligence",
            dataset="derived-information",
            source_url="https://example.invalid/derived",
            retrieved_at=NOW,
            processed_at=NOW,
            processing_method="fixture derivation",
            agent="fixture-agent",
            agent_version="1.0.0",
            model_version="fixture-definition-v1",
            upstream_ids=("fixture:observation",),
        ),
    )
    state = DerivedState(generated_at=NOW, definitions=(definition,), records=(record,))

    graph = KnowledgeGraph()
    resources = project_derived_state(graph, state)
    definition_subject = resources[definition.id]
    subject = resources[record.id]

    assert (definition_subject, RDF.type, BUI.DerivationDefinition) in graph.graph
    assert (subject, RDF.type, BUI.DerivedInformation) in graph.graph
    assert (subject, BUI.derivationDefinition, definition_subject) in graph.graph
    assert any(
        predicate == PROV.wasDerivedFrom and str(target).endswith("fixture/observation")
        for _, predicate, target in graph.graph.triples((subject, None, None))
    )
    serialized = graph.serialize()
    assert "fixture-definition-v1" in serialized
    assert "fixture_context" in serialized
    assert '"lqi":2' in serialized
