# Roadmap

The roadmap separates implemented capabilities from planned work. It is not a promise of dates or release order.

## Current capabilities — implemented in v1.0.0

- versioned canonical Pydantic contracts with epistemic state, quality, units, UTC time, CRS and provenance;
- registered public-source metadata and provider-specific adapters;
- independent live acquisition for Berlin air quality, DWD meteorology and VBB GTFS-Realtime;
- slow-changing reference acquisition for official facilities, selected Climate Analysis 2022 layers and VBB static GTFS;
- optional OpenStreetMap road-network acquisition with explicit speed/travel-time imputation provenance and strict readiness validation;
- last-known-good retention and separate availability/freshness/source-error semantics;
- Live State, Mobility, Exposure, Heat, Energy and Resilience agents;
- registry-driven deterministic capability resolution and dependency ordering;
- first-class persisted derivations, dependency DAGs, lineage, quality/freshness propagation and incremental recomputation;
- two verified source-backed descriptive cross-domain products: Heat + Air Quality and Mobility + Air Quality;
- chronological energy forecasting evaluation against persistence and seasonal-naive baselines plus Ridge/gradient-boosting candidates;
- dataset-fingerprint/model binding for persisted energy forecasts and reproducible real Berlin energy evidence;
- shortest-path, route-comparison and accessibility analysis over explicit network/facility inputs, including point-in-time real Berlin OSM readiness/routing evidence;
- explicit immutable scenario contracts and deterministic scenario transforms;
- independent multi-domain scenario assessment with no composite score;
- RDF projection, ontology/SHACL artefacts, derived lineage and bounded semantic relationship inspection;
- FastAPI state/analysis interfaces and a React/MapLibre analytical dashboard;
- snapshot-aware hot reload for validated runtime/reference/energy/derived state;
- structured privacy-conscious request/source/reload/derivation/scenario observability;
- security baseline with loopback-default exposure, container hardening, browser headers, error redaction and dependency audits;
- practical accessibility baseline with keyboard-accessible principal workflows, non-pointer routing and automated Axe regression coverage;
- reproducible performance/scaling evidence with bounded map responses and explicit capacity limitations;
- protected backend/frontend/container CI plus separate scoped source, security, real-data and performance evidence workflows;
- research-grade documentation, verification matrix and reproducibility guidance;
- Semantic Versioning release metadata, changelog and versioned release-note contract enforced by regression test;
- MIT project-source licence.

## Current post-v1 development — implemented

- automatic critical-facility route monitoring over the current persisted weighted road network;
- snapshot-bound route recomputation only when validated reference state changes;
- bounded critical-route API with source/licence provenance and explicit unavailable/degraded semantics;
- persistent MapLibre route visualization with 15-second dashboard polling, route selection and keyboard-accessible inspection;
- explicit separation between dynamic platform-state refresh and real-time road traffic telemetry; current route costs do not claim live congestion.

## Short term — planned improvements

- keep frontend API declarations systematically aligned with generated OpenAPI contracts;
- expand API contract examples and automated request/response compatibility checks;
- improve generated snapshot metadata/version migration handling;
- add stronger documentation-link validation and documentation-site configuration when a publishing target is chosen;
- extend deterministic tests around persistence/reload, source-status edge cases and larger reference collections;
- add broader operational observability while preserving privacy-safe logging;
- define a repeatable publication/archive path for reproducible experiment and release artefacts.

## Medium term — planned research/development

- rolling-origin and multi-horizon energy evaluation with calibrated uncertainty where methodologically justified;
- richer mobility/resilience costs from verified dynamic data;
- explicit facility access/entrance modelling and stronger network-quality validation;
- persistent semantic-store option with defined synchronization semantics;
- additional Berlin urban-domain agents/data sources through documented extension contracts;
- automated reproducible experiment artefact packaging;
- benchmark suites for cross-domain integration/failure isolation and representative Berlin-scale performance;
- systematic API/authentication design if deployment expands beyond the current trusted single-host research boundary.

## Long term — research directions

- distributed/federated deployment of independently versioned domain agents;
- formal contract/version negotiation and distributed provenance;
- historical-event validation of cross-domain disruption scenarios;
- comparative architecture evaluation against meaningful integration baselines;
- analyst/user studies on provenance, uncertainty and scenario communication;
- optional natural-language interpretation into typed workflow/scenario requests with no authority to generate domain facts;
- publication-ready evaluation of the architecture as an agent-extensible federated urban digital-twin platform.

## Explicitly not on the roadmap without new methodology/evidence

The project should not add the following merely for apparent completeness:

- fabricated values for unavailable domains;
- an unexplained universal Berlin score;
- causal claims from simple cross-domain association;
- non-Berlin data presented as Berlin operational state;
- forecast-performance claims without reproducible evaluation;
- hidden model/imputation choices that erase provenance;
- permanent-provider, formal-accessibility or production-capacity claims unsupported by evidence.

## Roadmap maintenance

When a planned item becomes implemented, move it into current capabilities only after code, tests and documentation are present. If an item changes architecture, public stable contracts or research assumptions, update the relevant ADR/evaluation/release documentation at the same time and apply Semantic Versioning to published releases.