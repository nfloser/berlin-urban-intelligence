"""Semantic projection for first-class derived information and dependency lineage."""

from __future__ import annotations

import json

from rdflib import RDF, Literal, URIRef
from rdflib.namespace import XSD

from berlin_urban_intelligence.knowledge.graph import BUI, KnowledgeGraph, _resource
from berlin_urban_intelligence.runtime.derived import DerivedState


def project_derived_state(graph: KnowledgeGraph, state: DerivedState) -> dict[str, URIRef]:
    """Project definitions and derived records into the shared semantic graph.

    The canonical JSON state remains authoritative. RDF is a queryable semantic projection and
    therefore preserves definition identity, derivation/freshness status and PROV upstream links.
    """

    resources: dict[str, URIRef] = {}
    definitions: dict[str, URIRef] = {}
    for definition in state.definitions:
        subject = _resource(f"derivation-definition:{definition.id}")
        definitions[definition.id] = subject
        resources[definition.id] = subject
        graph.graph.add((subject, RDF.type, BUI.DerivationDefinition))
        graph.graph.add((subject, BUI.name, Literal(definition.name)))
        graph.graph.add((subject, BUI.description, Literal(definition.description)))
        graph.graph.add((subject, BUI.producerAgent, Literal(definition.producer_agent_id)))
        graph.graph.add((subject, BUI.producerVersion, Literal(definition.producer_version)))
        graph.graph.add((subject, BUI.algorithmVersion, Literal(definition.algorithm_version)))
        graph.graph.add((subject, BUI.outputKind, Literal(definition.output_kind)))

    for record in state.records:
        subject = _resource(record.id)
        resources[record.id] = subject
        graph.graph.add((subject, RDF.type, BUI.DerivedInformation))
        graph.graph.add((subject, BUI.derivationDefinition, definitions[record.definition_id]))
        graph.graph.add((subject, BUI.entity, _resource(record.entity_id)))
        graph.graph.add((subject, BUI.phenomenon, Literal(record.phenomenon)))
        if isinstance(record.value, (dict, list, tuple)):
            graph.graph.add(
                (
                    subject,
                    BUI.valueJSON,
                    Literal(json.dumps(record.value, separators=(",", ":"), sort_keys=True)),
                )
            )
        else:
            graph.graph.add((subject, BUI.value, Literal(record.value)))
        if record.unit:
            graph.graph.add((subject, BUI.unit, Literal(record.unit)))
        graph.graph.add((subject, BUI.qualityFlag, Literal(record.quality.value)))
        graph.graph.add((subject, BUI.freshnessStatus, Literal(record.freshness.value)))
        graph.graph.add((subject, BUI.derivationStatus, Literal(record.status.value)))
        graph.graph.add((subject, BUI.derivationContext, Literal(record.context.value)))
        if record.scenario_id:
            graph.graph.add((subject, BUI.scenarioId, Literal(record.scenario_id)))
        graph.graph.add(
            (subject, BUI.validAt, Literal(record.valid_at.isoformat(), datatype=XSD.dateTime))
        )
        graph.graph.add(
            (
                subject,
                BUI.computedAt,
                Literal(record.computed_at.isoformat(), datatype=XSD.dateTime),
            )
        )
        for item in record.inputs:
            graph.graph.add(
                (
                    subject,
                    BUI.derivationInput,
                    Literal(f"{item.role}:{item.id}"),
                )
            )
        graph._add_provenance(subject, record.id, record.provenance)

    return resources
