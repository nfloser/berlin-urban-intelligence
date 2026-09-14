"""Semantic projection of canonical cross-domain identity, state and provenance.

High-volume measurements do not need to live entirely in RDF. This graph stores compact semantic
state and lineage records and can be persisted or published to a SPARQL-capable store later without
changing the canonical agent contracts.
"""

from __future__ import annotations

import json

from rdflib import RDF, Graph, Literal, Namespace, URIRef
from rdflib.namespace import PROV, XSD

from berlin_urban_intelligence.shared.contracts import (
    DerivedValue,
    Forecast,
    NetworkEdge,
    NetworkNode,
    Observation,
    OfficialModelFeature,
    Provenance,
    ScenarioValue,
    UrbanEntity,
)

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
        class_map = {
            "critical_facility": BUI.CriticalFacility,
            "district": BUI.District,
            "building": BUI.Building,
            "transport_stop": BUI.TransportStop,
            "network_node": BUI.NetworkNode,
            "network_edge": BUI.NetworkEdge,
        }
        self.graph.add((subject, RDF.type, class_map.get(entity.entity_type, BUI.UrbanEntity)))
        self.graph.add((subject, BUI.entityType, Literal(entity.entity_type)))
        if entity.name:
            self.graph.add((subject, BUI.name, Literal(entity.name)))
        if entity.source_identifier:
            self.graph.add((subject, BUI.sourceIdentifier, Literal(entity.source_identifier)))
        if entity.spatial and entity.spatial.geometry:
            self.graph.add((subject, BUI.crs, Literal(entity.spatial.crs)))
            self.graph.add(
                (
                    subject,
                    BUI.geometryGeoJSON,
                    Literal(
                        json.dumps(entity.spatial.geometry, separators=(",", ":"), sort_keys=True)
                    ),
                )
            )
        return subject

    def _add_provenance(self, subject: URIRef, item_id: str, provenance: Provenance) -> None:
        provider = provenance.provider
        dataset = provenance.dataset
        agent = provenance.agent
        agent_version = provenance.agent_version
        model_version = provenance.model_version
        upstream_ids = provenance.upstream_ids
        source_url = provenance.source_url

        source = _resource(f"source:{provider}:{dataset}")
        activity = _resource(f"activity:{item_id}")
        self.graph.add((source, RDF.type, BUI.DataSource))
        self.graph.add((source, RDF.type, PROV.Entity))
        self.graph.add((source, BUI.provider, Literal(provider)))
        self.graph.add((source, BUI.dataset, Literal(dataset)))
        self.graph.add((source, BUI.sourceURL, Literal(str(source_url))))
        self.graph.add((subject, PROV.wasDerivedFrom, source))
        self.graph.add((activity, RDF.type, PROV.Activity))
        self.graph.add((activity, BUI.agent, Literal(agent)))
        self.graph.add((activity, BUI.agentVersion, Literal(agent_version)))
        if model_version:
            self.graph.add((activity, BUI.modelVersion, Literal(model_version)))
        self.graph.add((subject, PROV.wasGeneratedBy, activity))
        for upstream_id in upstream_ids:
            self.graph.add((subject, PROV.wasDerivedFrom, _resource(upstream_id)))

    def add_observation(self, observation: Observation) -> URIRef:
        subject = _resource(observation.id)
        entity = _resource(observation.entity_id)
        self.graph.add((subject, RDF.type, BUI.Observation))
        self.graph.add((subject, RDF.type, SOSA.Observation))
        self.graph.add((subject, SOSA.hasFeatureOfInterest, entity))
        self.graph.add((subject, SOSA.observedProperty, Literal(observation.phenomenon)))
        self.graph.add((subject, BUI.dataState, Literal(observation.state.value)))
        self.graph.add((subject, BUI.qualityFlag, Literal(observation.quality.value)))
        self.graph.add((subject, BUI.value, Literal(observation.value)))
        if observation.unit:
            self.graph.add((subject, BUI.unit, Literal(observation.unit)))
        self.graph.add(
            (
                subject,
                SOSA.resultTime,
                Literal(observation.observed_at.isoformat(), datatype=XSD.dateTime),
            )
        )
        self._add_provenance(subject, observation.id, observation.provenance)
        return subject

    def add_derived_value(self, value: DerivedValue) -> URIRef:
        subject = _resource(value.id)
        self.graph.add((subject, RDF.type, BUI.DerivedValue))
        self.graph.add((subject, BUI.entity, _resource(value.entity_id)))
        self.graph.add((subject, BUI.phenomenon, Literal(value.phenomenon)))
        self.graph.add((subject, BUI.value, Literal(value.value)))
        self.graph.add((subject, BUI.dataState, Literal(value.state.value)))
        self.graph.add((subject, BUI.qualityFlag, Literal(value.quality.value)))
        self.graph.add(
            (subject, BUI.validAt, Literal(value.valid_at.isoformat(), datatype=XSD.dateTime))
        )
        if value.unit:
            self.graph.add((subject, BUI.unit, Literal(value.unit)))
        for dependency in value.dependencies:
            self.graph.add((subject, PROV.wasDerivedFrom, _resource(dependency)))
        self._add_provenance(subject, value.id, value.provenance)
        return subject

    def add_forecast(self, forecast: Forecast) -> URIRef:
        subject = _resource(forecast.id)
        self.graph.add((subject, RDF.type, BUI.Forecast))
        self.graph.add((subject, BUI.entity, _resource(forecast.entity_id)))
        self.graph.add((subject, BUI.phenomenon, Literal(forecast.phenomenon)))
        self.graph.add((subject, BUI.value, Literal(forecast.value)))
        self.graph.add((subject, BUI.dataState, Literal(forecast.state.value)))
        self.graph.add((subject, BUI.qualityFlag, Literal(forecast.quality.value)))
        self.graph.add(
            (subject, BUI.issuedAt, Literal(forecast.issued_at.isoformat(), datatype=XSD.dateTime))
        )
        self.graph.add(
            (subject, BUI.validAt, Literal(forecast.valid_at.isoformat(), datatype=XSD.dateTime))
        )
        self.graph.add((subject, BUI.unit, Literal(forecast.unit)))
        if forecast.lower_bound is not None:
            self.graph.add((subject, BUI.lowerBound, Literal(forecast.lower_bound)))
            self.graph.add((subject, BUI.upperBound, Literal(forecast.upper_bound)))
        self._add_provenance(subject, forecast.id, forecast.provenance)
        return subject

    def add_scenario_value(self, value: ScenarioValue, *, baseline_id: str) -> URIRef:
        if not baseline_id:
            raise ValueError("scenario projection requires an explicit baseline_id")
        subject = _resource(value.id)
        self.graph.add((subject, RDF.type, BUI.ScenarioValue))
        self.graph.add((subject, BUI.phenomenon, Literal(value.phenomenon)))
        self.graph.add((subject, BUI.value, Literal(value.value)))
        self.graph.add((subject, BUI.dataState, Literal(value.state.value)))
        self.graph.add((subject, BUI.scenarioId, Literal(value.scenario_id)))
        self.graph.add((subject, BUI.baseline, _resource(baseline_id)))
        if value.unit:
            self.graph.add((subject, BUI.unit, Literal(value.unit)))
        return subject

    def add_official_model_feature(self, feature: OfficialModelFeature) -> URIRef:
        subject = _resource(feature.id)
        self.graph.add((subject, RDF.type, BUI.OfficialModelFeature))
        self.graph.add((subject, BUI.entity, _resource(feature.entity_id)))
        self.graph.add((subject, BUI.modelName, Literal(feature.model_name)))
        self.graph.add((subject, BUI.featureType, Literal(feature.feature_type)))
        self.graph.add((subject, BUI.dataState, Literal(feature.state.value)))
        self.graph.add((subject, BUI.qualityFlag, Literal(feature.quality.value)))
        self.graph.add((subject, BUI.crs, Literal(feature.spatial.crs)))
        self.graph.add(
            (
                subject,
                BUI.geometryGeoJSON,
                Literal(
                    json.dumps(feature.spatial.geometry, separators=(",", ":"), sort_keys=True)
                ),
            )
        )
        self.graph.add(
            (
                subject,
                BUI.propertiesJSON,
                Literal(
                    json.dumps(
                        feature.properties, separators=(",", ":"), sort_keys=True, default=str
                    )
                ),
            )
        )
        self._add_provenance(subject, feature.id, feature.provenance)
        return subject

    def add_network_node(self, node: NetworkNode) -> URIRef:
        subject = _resource(node.id)
        self.graph.add((subject, RDF.type, BUI.NetworkNode))
        if node.longitude is not None and node.latitude is not None:
            self.graph.add((subject, BUI.longitude, Literal(node.longitude)))
            self.graph.add((subject, BUI.latitude, Literal(node.latitude)))
            self.graph.add((subject, BUI.crs, Literal("EPSG:4326")))
        if node.provenance is not None:
            self._add_provenance(subject, node.id, node.provenance)
        return subject

    def add_network_edge(self, edge: NetworkEdge) -> URIRef:
        subject = _resource(edge.id)
        self.graph.add((subject, RDF.type, BUI.NetworkEdge))
        self.graph.add((subject, BUI.sourceNode, _resource(edge.source)))
        self.graph.add((subject, BUI.targetNode, _resource(edge.target)))
        self.graph.add((subject, BUI.travelTimeSeconds, Literal(edge.travel_time_s)))
        self.graph.add((subject, BUI.lengthMetres, Literal(edge.length_m)))
        self.graph.add((subject, BUI.bidirectional, Literal(edge.bidirectional)))
        if edge.provenance is not None:
            self._add_provenance(subject, edge.id, edge.provenance)
        return subject

    def serialize(self, format: str = "turtle") -> str:
        serialized = self.graph.serialize(format=format)
        return serialized.decode() if isinstance(serialized, bytes) else serialized
