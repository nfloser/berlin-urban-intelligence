# Integration and acceptance status

Implemented in this revision: missing FastAPI application; all documented read endpoints; explicit scenario assessment and route endpoints; persisted live/reference/energy assembly; React dashboard, MapLibre map, provenance and source views; frontend container/proxy; deterministic backend/frontend tests; corrections for invalid RDF identifiers, non-finite observations, missing scenario parameters, stale scenario baselines and dependency rollback.

This is a working integration increment, not a completed v1.0 research platform. Remaining masterprompt gates: PostGIS/Fuseki-backed persistence and deployment; complete city-agnostic provider configuration; full numerical mobility/exposure integration; comprehensive real reference-layer and energy evaluation runs; browser end-to-end CI and broader domain adapter coverage; verified container and live-source acceptance across all domains. External source outages remain visible and cannot be resolved by synthesizing measurements.

Standalone prototypes are not loaded as runtime dependencies. Before migrating additional functionality, inspect the current prototype commit and translate it into canonical contracts with tests; older chat descriptions are not evidence that a prototype is complete.
