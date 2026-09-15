# Architecture

Berlin Urban Intelligence is a modular monorepo for an agent-extensible urban digital twin. The monorepo is an integration boundary rather than a domain monolith: domain agents remain independently testable and communicate through versioned canonical contracts.

## Layers

1. **Source adapters** isolate external APIs/files and make schema assumptions explicit.
2. **Canonical contracts** carry value, unit, UTC time, CRS where spatial, epistemic state, quality and provenance.
3. **Domain agents** implement Live State, Mobility, Environmental Exposure, Urban Heat, Energy Forecasting and Resilience capabilities.
4. **Runtime/reference/energy/derived stores** persist atomic JSON state; fast-changing observations, slower reference layers, evaluated forecasts and derived information remain separate.
5. **Derived-information execution** represents deterministic derivation definitions, explicit upstream inputs, freshness/status and dependency-aware re-execution without fabricating unavailable inputs.
6. **Knowledge projection** maps canonical objects and derived lineage to RDF using project vocabulary plus SOSA, PROV-O and QUDT where applicable.
7. **Scenario engine** creates explicitly hypothetical values or network overlays without mutating observed/reference state.
8. **Deterministic orchestrator** plans and executes typed workflows; an LLM is not required.
9. **Integrated assessment** combines available heat, energy and resilience dimensions without inventing a composite city score.
10. **FastAPI and dashboard** expose inspectable state, provenance, source/agent status, bounded reference-map projections, derived lineage and analysis results.

## Invariants

- Production paths never synthesize missing urban measurements.
- `observed`, `official_modelled`, `project_modelled`, `forecast`, `derived`, `interpolated` and `scenario` are not interchangeable.
- Numeric cross-agent values require explicit units.
- Datetimes crossing agent boundaries are timezone-aware and normalized to UTC.
- WGS84 is used for interchange; Berlin metric calculations use an explicit projected CRS, EPSG:25833 by default.
- Scenario operations use copied/overlay state and cannot rewrite the baseline.
- Source availability, freshness and last-known-good state are represented separately.
- Reference acquisition retains valid data per source when an independent reference source fails.
- Invalid replacement snapshots do not overwrite the last valid in-process snapshot.
- Derived products are emitted only when their required source-backed inputs exist and retain explicit upstream lineage.
- Energy forecasts are accepted only when evaluation/model metadata and dataset fingerprints match.
- A bounded map projection is never presented as complete when the API reports per-layer truncation.

## Runtime topology

Acquisition is explicit and separate from API serving:

- `scripts/refresh_live.py` writes `data/runtime/state.json`, `data/runtime/derived.json` and live/derived RDF.
- `scripts/refresh_reference.py` writes `data/runtime/reference.json` and reference RDF.
- `scripts/evaluate_energy.py` writes `data/runtime/energy.json` after chronological evaluation.
- the API never contacts source providers during normal request handling;
- a snapshot controller watches persisted runtime, reference, energy and derived files and reloads only changed snapshots;
- successfully validated replacements atomically rebuild the affected in-process state/agents/orchestrator;
- invalid replacements preserve the previous valid in-process snapshot and are exposed through reload diagnostics;
- the frontend consumes only API outputs and polls the system snapshot token so a validated persisted-state update becomes visible without restarting the backend or manually refreshing the page.

The reload boundary deliberately remains behind persisted state. Provider acquisition therefore stays outside HTTP request handlers, while a long-running API can still observe successfully written snapshots without a process restart. Large reference snapshots are reparsed only when file identity changes.

## Dashboard interaction boundary

The MapLibre dashboard distinguishes compact rendering data, canonical inspection and hypothetical analysis:

- `/api/v1/map/reference` is a bounded WGS84 GeoJSON projection of persisted facilities, transport stops and official climate-model features for the active map viewport;
- viewport requests carry explicit per-layer `total`, `matched`, `returned` and `truncated` metadata, and the UI surfaces truncation rather than implying completeness;
- map movement triggers a new bbox request; request generations prevent a slower older response from overwriting a newer viewport;
- clicking a rendered reference object resolves its layer/id and fetches the complete canonical object from `/api/v1/map/reference/{layer}/{resource_id}` before opening the metadata/provenance inspector;
- the compact map projection therefore does not replace canonical reference state and does not need to duplicate full provenance into every rendered feature;
- route origin/destination selection is a separate interaction mode that resolves clicks to persisted network nodes through the API;
- baseline and scenario routes are rendered independently so a hypothetical network disruption cannot visually replace the baseline without an explicit comparison;
- if the external basemap style cannot load, a local background style keeps project-owned reference and route layers usable;
- observation provenance, derived lineage, source status, agent capabilities/dependencies and snapshot reload diagnostics remain separately inspectable.

## Verification boundary

Deterministic unit/integration tests do not depend on external provider availability. CI additionally starts the composed backend/frontend stack and uses a small explicitly synthetic **acceptance-test-only** reference snapshot to exercise the real persistence → FastAPI → nginx → React/MapLibre path. Browser acceptance verifies viewport-backed reference loading, canonical map-object inspection and baseline-vs-disruption routing. This fixture is not bundled or selected as a production fallback. Current provider compatibility remains the responsibility of separate live-source smoke workflows.
