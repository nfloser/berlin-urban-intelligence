# Architecture

This repository integrates six domain agents behind versioned canonical contracts. External HTTP clients normalize provider payloads; agents preserve epistemic state and provenance; JSON stores persist independently acquired live, reference and energy state. FastAPI loads validated snapshots on each request so refreshes become visible without a process restart. React consumes this API through a same-origin proxy.

The knowledge graph is a projection, not the primary database. Routing runs against an explicit NetworkX multigraph; scenario overlays copy the baseline graph. The deterministic orchestrator reports domain availability, while the assessment service executes heat, energy and facility-accessibility calculations. A workflow availability report is not a numerical cross-domain assessment.

The current deployment uses filesystem snapshots and in-process RDF. It does not yet provide PostGIS persistence, a managed Fuseki service, distributed agent scheduling or a complete city configuration abstraction. Berlin-specific adapters remain separate from shared contracts, but changing city still requires provider integration work. These are explicit remaining masterprompt requirements, not implemented infrastructure.
