# Knowledge graph

> This compatibility page is retained for existing links. The primary conceptual documentation is [concepts/system-concepts.md](concepts/system-concepts.md) and [data/provenance.md](data/provenance.md).

The semantic layer is a projection of canonical application state, not an independent hidden truth store or a second operational database.

The project ontology under `knowledge/ontology/` defines a deliberately small Berlin Urban Intelligence vocabulary. The current projection uses SOSA relationships for observations and PROV-O relationships for lineage. A QUDT namespace is bound by the graph implementation for semantic interoperability, but the current code represents units with project `bui:unit` literals rather than mapping them to QUDT unit IRIs. The repository therefore does not claim a complete QUDT quantity/unit model.

`KnowledgeGraph` projects canonical observations, entities, official-model features, network nodes/edges and evaluated forecasts into RDF. Persisted `DerivedState` is projected into the same graph through `project_derived_state`, including derivation definitions, derived records, status/freshness metadata and PROV upstream lineage. Canonical identifiers are retained so JSON/API objects and RDF resources can be traced to the same source object. Source and processing lineage are represented through semantic relationships rather than only human-readable notes.

`GET /api/v1/graph` materializes the current in-process projection from the validated runtime, reference, energy and derived snapshots. A missing optional state contributes no triples and is never replaced with synthetic semantic data.

`GET /api/v1/knowledge/relations/{resource_id}` provides a bounded typed inspection surface over that same graph. It reports deterministic incoming/outgoing relationships, distinguishes related resources from literals/blank nodes, exposes total/returned/truncated metadata and returns 404 when the requested canonical resource is absent. The endpoint is deliberately constrained; the platform does not expose arbitrary client-supplied SPARQL execution.

Topology-heavy algorithms remain in NetworkX `MultiDiGraph` structures instead of being forced into RDF. RDF is used for semantic relationships and provenance; weighted routing/accessibility use the graph representation suited to those calculations. This separation is intentional.

Live and reference refresh commands serialize RDF artefacts under `data/generated/`. The current deployment remains file-backed and does not include a persistent SPARQL/triplestore service. A future semantic store would need explicit synchronization and consistency semantics relative to canonical persisted state.

`python scripts/validate_knowledge.py` is part of deterministic CI and validates the ontology/knowledge artefacts before the repository verification pipeline succeeds. API integration tests additionally verify semantic parity for observations, reference entities, forecasts and persisted derivations, including bounded relation traversal.
