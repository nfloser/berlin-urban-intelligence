# Knowledge graph

The semantic layer is a projection of canonical application state, not an independent hidden truth store.

The project ontology under `knowledge/ontology/` defines a deliberately small Berlin Urban Intelligence vocabulary and reuses established vocabularies where useful: SOSA for observations, PROV-O for lineage and QUDT terms for quantities/units. SHACL artefacts encode structural expectations.

`KnowledgeGraph` converts observations, entities, official-model features, network objects and forecasts into RDF. Canonical identifiers are retained so JSON/API objects and RDF resources can be traced to the same source object.

Topology-heavy algorithms remain in NetworkX rather than being forced into RDF. RDF expresses semantic relationships and provenance; graph algorithms use a representation suited to weighted routing. This separation is intentional.

The current foundation serializes RDF artefacts to files. A triple-store deployment can be added later without changing agent contracts.
