# Knowledge graph

`KnowledgeGraph` projects observations, forecasts, entities, network topology and explicit scenario values using the project vocabulary, SOSA and PROV-O. Resource identifiers are percent-encoded without collapsing distinct colon and slash identifiers. Provider labels containing spaces therefore serialize correctly.

GET `/api/v1/graph` returns Turtle from currently persisted state. The repository includes an executable latest-observation SPARQL query and SHACL shapes. The integration test validates a source-shaped DWD fixture against SHACL and executes the query after RDF round-trip serialization.

`python scripts/validate_knowledge.py` checks ontology syntax and required classes. This command alone does not validate arbitrary runtime graphs against SHACL. The service does not expose unrestricted SPARQL execution or automatically publish into Fuseki.
