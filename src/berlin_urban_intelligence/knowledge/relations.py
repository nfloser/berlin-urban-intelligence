"""Bounded semantic relationship inspection over the canonical RDF projection.

The canonical persisted JSON states remain authoritative. This module only queries the in-memory
RDF projection already produced from those states and deliberately exposes a constrained relation
surface rather than arbitrary SPARQL execution.
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field
from rdflib import BNode, Literal as RDFLiteral, URIRef

from berlin_urban_intelligence.knowledge.graph import KnowledgeGraph, _resource


class SemanticRelation(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    direction: Literal["incoming", "outgoing"]
    predicate_uri: str = Field(min_length=1)
    related_kind: Literal["resource", "literal", "blank_node"]
    related_value: str
    related_datatype: str | None = None
    related_language: str | None = None


class SemanticRelations(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    resource_id: str = Field(min_length=1)
    resource_uri: str = Field(min_length=1)
    total: int = Field(ge=0)
    returned: int = Field(ge=0)
    truncated: bool
    relations: tuple[SemanticRelation, ...]


def _relation(
    *,
    direction: Literal["incoming", "outgoing"],
    predicate: URIRef,
    related: object,
) -> SemanticRelation:
    if isinstance(related, URIRef):
        kind: Literal["resource", "literal", "blank_node"] = "resource"
        datatype = None
        language = None
    elif isinstance(related, RDFLiteral):
        kind = "literal"
        datatype = str(related.datatype) if related.datatype else None
        language = related.language
    elif isinstance(related, BNode):
        kind = "blank_node"
        datatype = None
        language = None
    else:
        kind = "literal"
        datatype = None
        language = None

    return SemanticRelation(
        direction=direction,
        predicate_uri=str(predicate),
        related_kind=kind,
        related_value=str(related),
        related_datatype=datatype,
        related_language=language,
    )


def resource_relations(
    graph: KnowledgeGraph,
    resource_id: str,
    *,
    limit: int = 100,
) -> SemanticRelations | None:
    """Return deterministic incoming/outgoing relationships for one canonical resource.

    ``None`` means that the projected graph contains no occurrence of the requested resource.
    Results are sorted before truncation so repeated calls over the same snapshot are stable.
    """

    if limit < 1:
        raise ValueError("limit must be positive")

    resource = _resource(resource_id)
    relations = [
        _relation(direction="outgoing", predicate=predicate, related=related)
        for _, predicate, related in graph.graph.triples((resource, None, None))
    ]
    relations.extend(
        _relation(direction="incoming", predicate=predicate, related=related)
        for related, predicate, _ in graph.graph.triples((None, None, resource))
    )
    if not relations:
        return None

    relations.sort(
        key=lambda item: (
            item.direction,
            item.predicate_uri,
            item.related_kind,
            item.related_value,
            item.related_datatype or "",
            item.related_language or "",
        )
    )
    total = len(relations)
    selected = tuple(relations[:limit])
    return SemanticRelations(
        resource_id=resource_id,
        resource_uri=str(resource),
        total=total,
        returned=len(selected),
        truncated=total > len(selected),
        relations=selected,
    )
