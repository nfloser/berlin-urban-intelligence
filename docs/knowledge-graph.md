# Knowledge graph

The semantic layer is a projection of canonical application state, not an independent hidden truth store.

The project ontology under `knowledge/ontology/` defines a deliberately small Berlin Urban Intelligence vocabulary and reuses established vocabularies where useful: SOSA for observations, PROV-O for lineage and QUDT terms for quantities/units. SHACL artefacts encode structural expectations.

`KnowledgeGraph` projects canonical observations, entities, official-model features, network nodes/edges and evaluated forecasts into RDF. Canonical identifiers are retained so JSON/API objects and RDF resources can be traced to the same source object. Observation lineage uses PROV relationships rather than relying only on human-readable notes.

Topology-heavy algorithms remain in NetworkX/MultiDiGraph rather than being forced into RDF. RDF represents semantic relationships and provenance; routing/accessibility use a representation suited to weighted multi-edge networks. This separation is intentional.

Live and reference refresh commands can serialize RDF artefacts under `data/generated`. The current deployment remains file-backed; a future triple-store deployment can be introduced without changing agent contracts or epistemic semantics.

`python scripts/validate_knowledge.py` is part of deterministic CI and validates the ontology/knowledge artefacts before a commit is accepted.