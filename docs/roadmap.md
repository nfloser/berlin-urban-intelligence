# Roadmap

The roadmap separates implemented capabilities from planned work. It is not a promise of dates or release order.

## Current capabilities — implemented

- versioned canonical Pydantic contracts with epistemic state, quality, units, UTC time, CRS and provenance;
- registered public-source metadata and provider-specific adapters;
- independent live acquisition for Berlin air quality, DWD meteorology and VBB GTFS-Realtime;
- slow-changing reference acquisition for official facilities, selected Climate Analysis 2022 layers and VBB static GTFS;
- optional OpenStreetMap road-network acquisition with explicit speed-imputation opt-in;
- last-known-good retention and separate availability/freshness/source-error semantics;
- Live State, Mobility, Exposure, Heat, Energy and Resilience agents;
- chronological energy forecasting evaluation against persistence and seasonal-naive baselines plus Ridge/gradient-boosting candidates;
- dataset-fingerprint/model binding for persisted energy forecasts;
- shortest-path, route-comparison and accessibility analysis over explicit network/facility inputs;
- explicit immutable scenario contracts and deterministic scenario transforms;
- deterministic fixed workflow orchestration;
- independent multi-domain scenario assessment with no composite score;
- RDF projection, ontology/SHACL artefacts and semantic validation;
- FastAPI state/analysis interface and React/MapLibre dashboard;
- structured request-operation logging;
- backend/frontend/container CI and separate source smoke workflows;
- research-grade documentation structure and reproducibility guidance.

## Short term — planned improvements

- keep frontend API declarations systematically aligned with generated OpenAPI contracts;
- expand API contract examples and automated request/response compatibility checks;
- improve generated snapshot metadata/version migration handling;
- add stronger documentation-link validation and documentation-site configuration when a publishing target is chosen;
- extend deterministic tests around persistence/reload, source-status edge cases and larger reference collections;
- formalize version/release/changelog process;
- add broader operational observability while preserving privacy-safe logging.

## Medium term — planned research/development

- rolling-origin and multi-horizon energy evaluation with calibrated uncertainty where methodologically justified;
- richer mobility/resilience costs from verified dynamic data;
- explicit facility access/entrance modelling and stronger network-quality validation;
- capability-based deterministic orchestration while preserving typed contracts;
- persistent semantic-store option with defined synchronization semantics;
- additional Berlin urban-domain agents/data sources through documented extension contracts;
- automated reproducible experiment artefact packaging;
- benchmark suites for cross-domain integration/failure isolation and representative Berlin-scale performance.

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
- hidden model/imputation choices that erase provenance.

## Roadmap maintenance

When a planned item becomes implemented, move it into current capabilities only after code, tests and documentation are present. If an item changes architecture or research assumptions, add/update the relevant ADR/evaluation documentation at the same time.
