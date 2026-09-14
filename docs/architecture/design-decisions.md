# Architectural design decisions

Accepted ADRs are stored in [`docs/adr/`](../adr/). This page provides a navigable summary and records consequences that are visible in the current implementation.

## Modular monorepo

**Decision:** maintain the integration platform in one repository while retaining domain modules and typed boundaries.

**Context:** historical prototypes differ in implementation maturity and runtime assumptions. Direct runtime coupling to multiple repositories would complicate reproducibility, version compatibility and CI.

**Alternatives:** independent services/repositories for every domain; direct imports from prototype repositories.

**Rationale:** one repository provides one versioned contract surface and one verification pipeline while preserving modular source boundaries.

**Consequences:** deployment is simpler and contract changes can be tested atomically, but repository-level CI grows as more domains are integrated. Service isolation and independent release cadence are deferred.

See [ADR 001](../adr/001-monorepo.md).

## Typed in-process contracts before distributed transport

**Decision:** establish Pydantic canonical contracts as the interoperability layer before adding remote messaging.

**Context:** semantic ambiguity is a larger current risk than service transport.

**Alternatives:** event bus/message schemas first; ad-hoc dictionaries; shared database tables without typed domain contracts.

**Rationale:** frozen validated models make state, units, time and provenance explicit and directly testable.

**Consequences:** the current agent model is in-process. Future distribution must preserve the same semantics and contract-version expectations rather than bypass them.

See [ADR 002](../adr/002-typed-contracts.md).

## Explicit epistemic state

**Decision:** model observed, official-modelled, project-modelled, forecast, derived/interpolated and scenario values distinctly.

**Context:** urban integration can otherwise make predictions or model layers appear as measurements.

**Rationale:** state-specific contracts and validation provide machine-readable boundaries.

**Consequences:** integrations require more metadata and may expose incomplete state rather than convenient defaults, but downstream interpretation is more defensible.

## Separate persistence for runtime, reference and energy state

**Decision:** persist fast-changing observations/realtime mobility, slow-changing reference layers and evaluated forecasts in separate stores.

**Context:** these data classes have different acquisition cadence, failure behavior and validity semantics.

**Alternatives:** one combined city-state JSON/database record.

**Rationale:** separate stores prevent static schedules/model layers/forecasts from masquerading as live state and allow independent refresh workflows.

**Consequences:** consumers must combine stores explicitly. The API performs that composition at startup and therefore requires restart/reload to observe replaced snapshots.

## Explicit acquisition outside request handling

**Decision:** API handlers serve persisted state and do not fetch upstream providers during ordinary requests.

**Rationale:** deterministic request behavior, bounded latency and testability are more important for the current research platform than transparent request-time freshness.

**Consequences:** data freshness depends on refresh operations external to the backend process. Deployment automation must schedule those operations if continuous updates are desired.

## Deterministic orchestration without LLM dependency

**Decision:** supported workflow kinds map to fixed agent sets and `requires_llm` remains false.

**Context:** language interpretation is not required for the numerical/domain core and would complicate reproducibility if made mandatory.

**Alternatives:** runtime LLM planning or unconstrained agent self-selection.

**Rationale:** deterministic routing is inspectable and repeatable.

**Consequences:** new workflow combinations must currently be added explicitly in code. A future language layer may translate user requests into typed workflow/scenario requests but must not generate domain facts.

## No synthetic composite city score

**Decision:** integrated assessment reports dimensions independently and fixes `composite_score` to `null`.

**Context:** combining heat, energy and resilience into one score requires value judgements and a validated weighting model.

**Rationale:** an unvalidated aggregate would hide uncertainty and imply comparability not established by the current research.

**Consequences:** consumers receive a more complex multi-dimensional result but retain the information needed for domain-specific interpretation.

## Optional, explicitly qualified OSM network

**Decision:** OpenStreetMap road acquisition is optional and non-authoritative; speed imputation requires explicit opt-in.

**Rationale:** OSM provides valuable network coverage but has community-maintained completeness and attribute limitations. Treating inferred speeds as observations would violate provenance rules.

**Consequences:** default reference acquisition may not provide routing topology. Resilience capabilities are conditional on a network snapshot, and optional modelling choices must remain provenance-visible.

## Energy forecast fingerprint binding

**Decision:** registered forecasts must match the evaluated model ID and dataset fingerprint.

**Context:** model metrics are not meaningful if a forecast is silently produced from a different data snapshot.

**Rationale:** content fingerprinting ties evaluation evidence to the artefact presented downstream.

**Consequences:** forecast publication is stricter and can fail closed when metadata does not match. This is intentional.

## Decision process for future changes

A new ADR is appropriate when a change affects cross-domain contracts, persistence boundaries, deployment topology, data-state semantics, orchestration, source authority assumptions or evaluation methodology. Implementation-specific refactoring that does not alter those responsibilities normally does not require an ADR.
