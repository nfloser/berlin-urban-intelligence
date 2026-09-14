# Knowledge graph

> This compatibility page is retained for existing links. The primary conceptual documentation is [concepts/system-concepts.md](concepts/system-concepts.md) and [data/provenance.md](data/provenance.md).

The semantic layer is a projection of canonical application state, not an independent hidden truth store or a second operational database.

The project ontology under `knowledge/ontology/` defines a deliberately small Berlin Urban Intelligence vocabulary. The current projection uses SOSA relationships for observations and PROV-O relationships for lineage. A QUDT namespace is bound by the graph implementation for semantic interoperability, but the current code represents units with project `bui:unit` literals rather than mapping them to QUDT unit IRIs. The repository therefore does not claim a complete QUDT quantity/unit model.

`KnowledgeGraph` projects canonical observations, entities, official-model features, network nodes/edges and evaluated forecasts into RDF. Canonical identifiers are retained so JSON/API objects and RDF resources can be traced to the same source object. Source and processing lineage are represented through PROV relationships rather than only human-readable notes.

Topology-heavy algorithms remain in NetworkX `MultiDiGraph` structures instead of being forced into RDF. RDF is used for semantic relationships and provenance; weighted routing/accessibility use the graph representation suited to those calculations. This separation is intentional.

Live and reference refresh commands serialize RDF artefacts under `data/generated/`. The current deployment remains file-backed and does not include a persistent SPARQL/triplestore service. A future semantic store would need explicit synchronization and consistency semantics relative to canonical persisted state.

`python scripts/validate_knowledge.py` is part of deterministic CI and validates the ontology/knowledge artefacts before the repository verification pipeline succeeds.
