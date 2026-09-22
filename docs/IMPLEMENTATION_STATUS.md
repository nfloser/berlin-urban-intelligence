# Implementation Status

## Current phase

Phase 25 — **official VIZ disruption-aware map-first navigation**.

The stable v1.0 evidence baseline remains PASS. Post-v1 issue #38 / PR #39 established automatic critical-route monitoring. Issue #40 / PR #41 extends that routing surface with current official Berlin VIZ editorial disruption state and a practical navigation-first MapLibre experience.

## Current feature work

PR #41 follows the same TDD/evidence workflow. Live source probing first rejected the legacy VIZ endpoint for operational routing because its provider timestamps were stale in 2026, then distinguished the current Landesmeldestelle feed from the VIZ editorial feed. The editorial feed is used for route impact because it is current and exposes explicit severity semantics.

The implementation now:

- validates and persists official VIZ editorial road disruptions independently from runtime/reference state;
- keeps provider retrieval success separate from provider-content freshness using `tstore`;
- retains last-known-good disruption state on provider/schema failure;
- prevents stale traffic state from modifying routes;
- removes road edges only for active source records with exact severity `Vollsperrung`;
- avoids shared-node false-positive edge closures through projected, distance-bounded matching;
- preserves baseline route/time and separately exposes effective disrupted/rerouted/blocked results;
- applies the same VIZ-aware behavior to user-selected origin → destination routes and automatic critical routes;
- hot-reloads traffic-disruption snapshots without backend restart;
- exposes bounded traffic-disruption and persisted-place search APIs;
- refreshes VIZ state through the persistent Compose refresh worker;
- presents a full-viewport map-first route planner with origin/destination search, arbitrary map-point selection, automatic nearest-node resolution, automatic route calculation and fit-to-route, effective ETA/distance, Swap/Clear and state-colored routing;
- renders VIZ full closures in red and other source-backed disruptions in amber with inspectable validity/detail;
- keeps the analytical/research surfaces and hypothetical disruption workflow separate from observed VIZ state.

The feature deliberately does **not** claim Google Maps-equivalent live congestion speeds or arbitrary-address geocoding. `traffic_data_available=false` remains authoritative for congestion-speed telemetry. Partial restrictions are not assigned inferred delay multipliers.

Implementation head `806ca896891c650e380e43adab6be650524fb35c` passed protected CI run `35757018243` across backend, frontend and containers. The composed nginx → FastAPI → persisted reference/traffic state → React/MapLibre path passed **11/11 Playwright cases** in 34.0 s, including the new map-first navigation/rerouting path and all prior map, scenario, accessibility and security regression paths. The same head also has successful current VIZ live-source smoke and independent real-energy evidence runs.

## Verified v1 evidence baseline

### Protected application CI

PR #35 final head `342d57c71886ac65686c8dcd35d8553b4507a962` passed protected CI run `35093468008`:

- `backend` — PASS;
- `frontend` — PASS;
- `containers` — PASS, including Docker/Compose and the nginx → FastAPI → persisted state → React/Playwright path.

### Real Berlin energy

Independent run `35093467950` passed the official-source probes and the real 2024 evaluation, persistence, Energy Agent and API exposure path.

`docs/energy-real-evidence.md` remains authoritative for source semantics and measured results. The accepted reproducible source is the clean official 2024 Stromnetz Berlin high-voltage annual curve. The inspected 2025 publications with a 96-row upstream `#BEZUG!` timestamp block remain deliberately rejected rather than silently repaired.

### Real Berlin road network

Live run `35091544852` exercised the strict road-network path for `Mitte, Berlin, Germany`, network type `drive`, with explicit OSMnx speed/travel-time derivation.

Two public Overpass endpoints exceeded the configured attempt budget and their failure evidence was retained. `https://overpass-api.de/api` then returned a real graph that passed the readiness contract:

- 740 canonical nodes;
- 1,800 canonical edges;
- `OpenStreetMap contributors` / ODbL 1.0 provenance;
- provenance-visible speed/travel-time imputation;
- `synthetic_fallback=false`.

The existing `ResilienceAgent` completed the baseline route `osm-node:10087214573` → `osm-node:13043292535` at approximately **2.139 seconds**. Evidence artifact `10445300085` has SHA-256 `8672bb1325b80c76d54a5722d78cbc7135ad3d9626432796e1e1bb8b20e1595c`.

This is point-in-time provider compatibility/readiness evidence, not a guarantee of permanent public Overpass availability.

## Current architectural state

- Runtime, reference, energy, derived and traffic-disruption state are persisted separately and loaded through validated stores.
- Snapshot control hot-reloads validated replacements; invalid replacements retain last-known-good state and expose diagnostics.
- Six real agents expose explicit domains, capabilities, contracts, dependencies and health.
- Cross-agent coordination remains at registry/orchestration/composition boundaries rather than hidden inside domain agents.
- Registry-driven deterministic workflows resolve capabilities and enforce dependency ordering without requiring an LLM.
- Derived information retains definitions, upstream lineage, provenance, producer/algorithm version, freshness/quality and dependency status with incremental recomputation.
- Source-backed cross-domain products are omitted when required inputs are absent; no synthetic replacement score is generated.
- RDF projection and bounded semantic relationship inspection use validated persisted state.
- FastAPI exposes system/source/agent/domain/reference/scenario/derived/dependency/semantic/map and resilience surfaces.
- The React/MapLibre dashboard now uses a map-first navigation surface with persisted-place search, arbitrary map-point routing, source-backed VIZ disruption visualization, automatic disruption-aware rerouting and effective ETA/distance while retaining reference/provenance, platform/derived, deterministic workflow, scenario and critical-route inspection.
- Critical resilience routing has an equivalent coordinate-driven keyboard path over the same routing APIs; automatic monitored critical routes additionally expose a keyboard-selectable inspector.
- Browser acceptance runs against the composed application stack and includes pinned Axe accessibility scanning for representative states.
- Structured observability covers request, source-refresh, reload, derivation-refresh and scenario boundaries with safe low-cardinality fields.
- Security and dependency-audit workflows remain separate from application-domain logic.
- Real-source evidence workflows download provider data during the run and do not convert those publications into committed production fallbacks.

## Repository governance state

The `Protect main` ruleset is active on the default branch, has no bypass actors, blocks destructive branch changes, requires pull-request/review-thread resolution and uses strict required-status-check semantics.

The three merge-critical correctness checks remain:

- `backend`
- `frontend`
- `containers`

Security, real-source, performance and other evidence workflows are additional scoped evidence; they do not weaken or replace protected correctness checks.

## v1.0.0 release contract

The release candidate must satisfy all of the following before merge/tagging:

- `VERSION`, `pyproject.toml` and README all declare `1.0.0`;
- README states the MIT project-source licence and separates external dataset terms;
- `CHANGELOG.md` contains a dated `1.0.0` entry;
- `docs/releases/v1.0.0.md` records capabilities, verification evidence, operating notes and limitations;
- central docs do not retain stale `0.1.0`, `NOT READY` or pre-merge PR #35 status claims;
- protected backend/frontend/container checks pass on the final release-candidate head;
- review finds no unresolved correctness, documentation, compatibility, security or release-process findings;
- the release PR is squash-merged before the `v1.0.0` tag/GitHub release is created;
- the published release must point to the verified merged commit and use the reviewed versioned release notes.

## Known external and scope constraints

- Public-provider availability is external to deterministic CI and can regress after release.
- OSM-backed routing must degrade explicitly when acquisition is unavailable; no generated production topology substitutes for a provider failure.
- Cross-domain contexts are descriptive co-reporting only and do not establish causality, correlation or exposure.
- Current reproducible energy evidence is historical 2024 high-voltage network load, not current total Berlin demand.
- Automated accessibility tooling does not prove full assistive-technology usability or formal WCAG conformance.
- GitHub-hosted benchmark timings are not production-capacity guarantees.
- Complete RDF serialization is a bulk/research operation in the current in-memory topology, not a high-QPS production endpoint.
- Municipal operational authority, safety-critical use, authenticated multi-tenant deployment and distributed/federated runtime operation are outside the v1.0.0 claim boundary.

## Verification commands enforced by protected CI

```text
ruff format --check src tests scripts
ruff check src tests scripts
mypy src/berlin_urban_intelligence
pytest --cov=berlin_urban_intelligence --cov-report=term-missing
python scripts/validate_knowledge.py
python scripts/check_production_data.py
python scripts/check_secrets.py
FastAPI OpenAPI generation
frontend: npm test
frontend: npm run build
docker compose config
docker build (backend + frontend)
docker compose health/proxy checks
Playwright browser acceptance against the composed stack
Axe critical/serious configured WCAG A/AA regression scan in principal dashboard states
```

Separate scoped workflows cover dependency security audits, live/reference providers, real Berlin energy, real Berlin road-network readiness and performance measurements.

## Next concrete tasks

1. Complete the v1.0.0 release-documentation alignment on PR #37.
2. Run the complete protected CI on the final release-candidate head.
3. Perform an independent PR review, correct any findings and re-run affected checks.
4. Mark PR #37 review-ready and squash-merge only when the final head is green and review-clean.
5. Publish GitHub release/tag `v1.0.0` from the verified merged commit using the reviewed `docs/releases/v1.0.0.md` content.
6. Verify the published release target, release notes and issue #36 closure evidence.

## Important migration notes

Do not replace the existing source/agent/domain architecture. Provider acquisition remains outside request handlers. Canonical persisted state stays authoritative; RDF and bounded map GeoJSON are projections only. Cross-agent coordination belongs at composition/orchestration boundaries, while individual agents consume typed inputs and remain independently testable. Cross-domain additions must preserve independent source values/timestamps and explicit provenance rather than hiding them behind composite scores. Performance optimizations must preserve data/provenance semantics. Accessibility changes must preserve semantic native controls and equivalent non-pointer paths. Real-source adapters must reject ambiguous provider semantics rather than inventing timestamps, units or Berlin-wide interpretations.