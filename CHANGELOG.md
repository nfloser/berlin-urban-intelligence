# Changelog

All notable project changes are documented in this file. The project follows Semantic Versioning for published stable releases.

## [Unreleased]

### Added

- automatic critical-facility route monitoring derived from the current persisted road/reference snapshot;
- snapshot-bound backend caching with recomputation only when reference state changes;
- bounded `/api/v1/resilience/critical-routes` API with geometry, travel time, distance, edge IDs, source/licence provenance and explicit unavailable/degraded states;
- persistent MapLibre critical-route layer with automatic 15-second dashboard refresh, visibility control, route highlighting and keyboard-accessible inspection;
- explicit `traffic_data_available=false` semantics so persisted road weights are never presented as real-time congestion data;
- deterministic backend and composed Playwright coverage for automatic routing, reload invalidation, source degradation, unreachable facilities and map rendering;
- official Berlin VIZ editorial road-disruption ingestion with atomic persisted state, source-content freshness, last-known-good semantics and bounded API exposure;
- disruption-aware normal and monitored routing where active fresh `Vollsperrung` records can trigger deterministic rerouting or blocked state while other restrictions remain visible without invented speed penalties;
- map-first navigation with floating origin/destination search, arbitrary map-point selection, automatic nearest-road-node resolution, automatic route calculation/fit, effective ETA/distance, Swap/Clear and state-colored routes;
- inspectable VIZ road-disruption map layers plus persisted-place search for critical facilities and VBB stops;
- browser acceptance for the complete search → VIZ closure → automatic reroute workflow.

### Limitations

- real-time congestion-speed telemetry is not integrated; VIZ provides source-backed incidents/closures, not Google Maps-equivalent floating-car speeds;
- text search currently covers persisted facilities/stops rather than arbitrary-address geocoding; arbitrary locations can still be selected directly on the map;
- monitored routes require a routable persisted road network and critical facilities in at least two categories.

## [1.0.0] - 2026-09-16

First stable release of Berlin Urban Intelligence as a research-oriented, agent-extensible urban intelligence and digital-twin integration platform for Berlin.

### Added

- typed canonical Pydantic contracts for epistemic/data state, provenance, quality, freshness, units, CRS and UTC timestamps;
- independent live acquisition for Berlin air quality, DWD weather and VBB GTFS-Realtime plus slow-changing official reference acquisition;
- six domain/aggregation agents: Live State, Mobility, Exposure, Heat, Energy and Resilience;
- registry-driven deterministic capability resolution and dependency ordering without requiring an LLM for execution;
- persisted runtime, reference, energy and derived state with atomic replacement, validation and last-known-good semantics;
- dependency-aware derived-information model with provenance, upstream lineage, quality/freshness propagation and incremental recomputation;
- two verified source-backed descriptive cross-domain products: Heat + Air Quality and Mobility + Air Quality;
- leakage-safe energy evaluation against persistence/seasonal baselines and candidate models, with dataset-fingerprint-bound forecast artefacts;
- real Berlin energy evidence from a clean official 2024 Stromnetz Berlin high-voltage load publication;
- optional OpenStreetMap road-network acquisition with explicit speed/travel-time imputation provenance, strict readiness checks and real resilience routing evidence;
- resilience routing, route comparison, facility snapping/accessibility and immutable disruption overlays;
- explicit hypothetical heat, energy-demand, network-disruption and infrastructure-degradation scenarios;
- RDF projection, ontology/SHACL artefacts, semantic lineage and bounded relationship inspection APIs;
- FastAPI backend and React/TypeScript/MapLibre dashboard with analytical map, provenance, derived, platform and routing/scenario inspection surfaces;
- snapshot-aware runtime hot reload for validated runtime/reference/energy/derived state;
- structured low-cardinality observability for request, source-refresh, reload, derivation-refresh and scenario operations;
- security baseline covering loopback-default exposure, container hardening, browser security headers, exception-message redaction and dependency audits;
- practical accessibility baseline with keyboard-accessible principal workflows, non-pointer routing and automated Axe regression checks for representative states;
- reproducible performance evidence with bounded map output behavior and explicitly documented scaling limits;
- protected backend/frontend/container CI with Compose and full nginx → FastAPI → persisted state → React/Playwright acceptance;
- scoped live-source, reference, real-energy, road-network, security and performance evidence workflows;
- research, architecture, data, evaluation, reproducibility, security, observability, accessibility and verification documentation;
- MIT project-source licence.

### Verification highlights

- the repository-wide v1 evidence matrix is **PASS** for the declared v1 scope;
- PR #35 final head passed protected CI run `35093468008` across backend, frontend and containers/Compose/Playwright;
- independent real-energy run `35093467950` passed all official-source probes and the real 2024 evaluation/agent/API path;
- live road-network run `35091544852` acquired a real Berlin OSM `drive` graph for Mitte with 740 canonical nodes and 1,800 canonical edges, retained ODbL/provider and imputation provenance, recorded `synthetic_fallback=false`, and completed a baseline route through the existing `ResilienceAgent`;
- deterministic repository checks preserve explicit unavailable/error behavior rather than fabricating production measurements or fallback topology.

### Known limitations

- upstream public-source and Overpass availability is external and is not guaranteed by this release;
- real-energy evidence is historical 2024 high-voltage network load, not current total Berlin demand or a live grid-control forecast;
- cross-domain products are descriptive co-reporting and do not establish causality, correlation, exposure or a universal city score;
- automated accessibility evidence is not a formal WCAG conformance claim;
- hosted-runner performance evidence is not a production-capacity guarantee;
- authentication/authorization, multi-tenant public-cloud operation and municipal operational authority are outside the v1.0.0 scope;
- calibrated energy prediction intervals, persistent production semantic-store operation and distributed/federated agent deployment remain future work.

### Release process

Version metadata, README release claims, changelog and versioned release notes are protected by `tests/test_release_metadata.py`. A release tag is created only from the reviewed and CI-verified merged release commit.