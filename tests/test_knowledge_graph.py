from datetime import UTC, datetime

from rdflib.namespace import PROV, RDF

from berlin_urban_intelligence.knowledge.graph import BUI, KnowledgeGraph
from berlin_urban_intelligence.shared.contracts import (
    DataState,
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
