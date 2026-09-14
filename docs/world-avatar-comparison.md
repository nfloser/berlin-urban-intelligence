# Relationship to The World Avatar

Berlin Urban Intelligence is independently implemented. It is inspired by broad architectural ideas demonstrated in The World Avatar and related agent-based knowledge-graph work: specialised agents, semantic interoperability, provenance, composable derivations and separation of data acquisition from higher-level reasoning.

It does **not** copy The World Avatar codebase, claim compatibility, claim affiliation with Cambridge CARES/University of Cambridge, or require a Java agent stack/triple-store architecture.

The project deliberately uses a smaller Python/TypeScript monorepo and typed in-process boundaries for the research foundation. RDF is a semantic projection, while weighted routing remains in NetworkX. These are pragmatic design choices for reproducibility and inspectability at the current scale.

If later research requires distributed agents or a dedicated knowledge-graph service, the canonical contracts and provenance model provide migration boundaries without pretending that v0.1 already has that deployment topology.
