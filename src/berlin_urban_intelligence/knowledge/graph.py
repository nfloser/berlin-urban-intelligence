"""Small semantic graph focused on cross-domain identity and provenance."""

from __future__ import annotations

from rdflib import Graph, Literal, Namespace, RDF, URIRef
from rdflib.namespace import PROV, XSD

from berlin_urban_intelligence.shared.contracts import Observation, UrbanEntity

BUI = Namespace("https://w3id.org/berlin-urban-intelligence/ontology#")
RES = Namespace("https://w3id.org/berlin-urban-intelligence/resource/")
SOSA = Namespace("http://www.w3.org/ns/sosa/")
QUDT = Namespace("http://qudt.org/schema/qudt/")


def _resource(identifier: str) -> URIRef:
    return RES[identifier.replace(":", "/")]


class KnowledgeGraph:
    def __init__(self) -> None:
        self.graph = Graph()
        self.graph.bind("bui", BUI)
        self.graph.bind("prov", PROV)
        self.graph.bind("sosa", SOSA)
        self.graph.bind("qudt", QUDT)

    def add_entity(self, entity: UrbanEntity) -> URIRef:
        subject = _resource(entity.id)
        self.graph.add((subject, RDF.type, BUI.UrbanEntity))
        self.graph.add((subject, BUI.entityType, Literal(entity.entity_type)))
        if entity.name:
            self.graph.add((subject, BUI.name, Literal(entity.name)))
        if entity.source_identifier:
            self.graph.add((subject, BUI.sourceIdentifier, Literal(entity.source_identifier)))
        return subject

    def add_observation(self, observation: Observation) -> URIRef:
        subject = _resource(observation.id)
        entity = _resource(observation.entity_id)
        source = _resource(f"source:{observation.provenance.provider}:{observation.provenance.dataset}")
        activity = _resource(f"activity:{observation.id}")
        self.graph.add((subject, RDF.type, BUI.Observation))
        self.graph.add((subject, RDF.type, SOSA.Observation))
        self.graph.add((subject, SOSA.hasFeatureOfInterest, entity))
        self.graph.add((subject, SOSA.observedProperty, Literal(observation.phenomenon)))
        self.graph.add((subject, BUI.dataState, Literal(observation.state.value)))
        self.graph.add((subject, BUI.qualityFlag, Literal(observation.quality.value)))
        self.graph.add((subject, BUI.value, Literal(observation.value)))
        if observation.unit:
            self.graph.add((subject, BUI.unit, Literal(observation.unit)))
        self.graph.add((subject, SOSA.resultTime, Literal(observation.observed_at.isoformat(), datatype=XSD.dateTime)))
        self.graph.add((source, RDF.type, PROV.Entity))
        self.graph.add((source, BUI.provider, Literal(observation.provenance.provider)))
        self.graph.add((source, BUI.dataset, Literal(observation.provenance.dataset)))
        self.graph.add((subject, PROV.wasDerivedFrom, source))
        self.graph.add((activity, RDF.type, PROV.Activity))
        self.graph.add((activity, BUI.agent, Literal(observation.provenance.agent)))
        self.graph.add((activity, BUI.agentVersion, Literal(observation.provenance.agent_version)))
        self.graph.add((subject, PROV.wasGeneratedBy, activity))
        for upstream_id in observation.provenance.upstream_ids:
            self.graph.add((subject, PROV.wasDerivedFrom, _resource(upstream_id)))
        return subject

    def serialize(self, format: str = "turtle") -> str:
        serialized = self.graph.serialize(format=format)
        return serialized.decode() if isinstance(serialized, bytes) else serialized
