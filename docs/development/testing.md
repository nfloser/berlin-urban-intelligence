# Testing strategy

Testing separates deterministic repository correctness from live external-provider compatibility.

## Deterministic backend tests

Backend tests use pytest and synthetic fixtures that are never read by production runtime paths. Current test areas include canonical contracts, API behavior, integrated assessment, data/source pipelines, energy evaluation, knowledge projection, reference acquisition, resilience calculations, scenarios, source-registry behavior and bounded reference-map projections.

The main command used by CI is:

```bash
pytest --cov=berlin_urban_intelligence --cov-report=term-missing
```

Coverage is reported as diagnostic evidence; the repository does not currently define a numeric coverage threshold as a release criterion.

Road-network unit/integration tests additionally verify canonical OSM readiness, endpoint consistency, ODbL/source provenance, explicit opt-in speed/travel-time imputation, baseline routing, provider/schema degradation and last-known-good retention without synthetic fallback.

## Frontend tests

The frontend uses Vitest:

```bash
cd frontend
npm test
npm run build
```

The build command runs TypeScript checking (`tsc --noEmit`) before Vite production build, so type errors fail the build even when unit tests pass.

Map-specific unit tests cover viewport URL construction, invalid bounding boxes, per-layer truncation metadata, mixed-feature projection into independent MapLibre sources, encoded canonical-detail paths and stale-request generation handling.

## Static and semantic verification

CI additionally runs:

```bash
ruff format --check src tests scripts
ruff check src tests scripts
mypy src/berlin_urban_intelligence
python scripts/validate_knowledge.py
python scripts/check_production_data.py
python scripts/check_secrets.py
```

It also generates the FastAPI OpenAPI schema, ensuring route/model construction remains valid.

## Container and browser acceptance

After backend and frontend jobs pass, CI validates the Compose file, builds both images, seeds a deterministic acceptance-only reference snapshot, starts the composed services and verifies the real deployment path:

- backend `/health` responds;
- frontend root responds;
- frontend nginx successfully proxies `/health` to the backend;
- Playwright loads the dashboard through nginx against the real FastAPI process;
- a hypothetical heat assessment remains explicit about unavailable dimensions;
- deterministic orchestration remains inspectable when source-backed agents are unavailable;
- the reference map loads compact GeoJSON for the current bbox rather than fixed 1,000-item canonical lists;
- navigation triggers another reference viewport request;
- clicking a rendered facility fetches its complete canonical detail object and exposes provenance in the UI; and
- map-selected routing compares the deterministic baseline with an explicit edge-closure scenario.

The acceptance fixture is created only inside CI and is not a production fallback. Browser tests therefore validate integration behavior without claiming live provider availability or city-wide data completeness.

## Live-source smoke

`.github/workflows/live-source-smoke.yml` is separate from deterministic CI. It runs manually and on a schedule (`17 4 * * 2,5`) with Python 3.12 and invokes `scripts/live_smoke.py` against current external live sources.

A live-source failure can therefore represent an upstream outage or schema change without making deterministic tests nondeterministic.

## Reference-source smoke

`.github/workflows/reference-smoke-once.yml` can be run manually and verifies current official reference acquisition for facilities, selected climate features and static VBB stops. It asserts that reference errors are empty and that the expected reference collections are non-empty. It does not enable optional OSM acquisition.

The filename and trigger reflect that this workflow is not currently a permanent scheduled reference-monitoring pipeline.

## Road-network smoke

`.github/workflows/road-network-smoke.yml` is the separate manual/scheduled verification path for optional real OSM road acquisition. It installs `.[osm]` and runs `scripts/road_network_smoke.py` against a real Berlin scope with explicit OSMnx speed/travel-time derivation.

A passing road-network smoke must produce non-empty canonical nodes/edges with valid OSM provenance, prove endpoint consistency and positive routing attributes, and complete a deterministic baseline route through the existing `ResilienceAgent`. The smoke emits JSON evidence and never substitutes a synthetic network.

The Overpass delivery endpoint may be configured explicitly. This is not silent failover: the selected endpoint is visible in the smoke evidence/provenance and the previous OSMnx setting is restored after the fetch.

On 2026-09-15 two real GitHub-hosted attempts remained externally blocked: run `34979600413` timed out connecting to `overpass-api.de`, and run `34980820676` timed out reading from `https://overpass.private.coffee/api`, both after 180 seconds. Failure artifacts were uploaded and both evidence payloads recorded `synthetic_fallback=false`. Because neither run produced non-empty real nodes/edges or a live baseline route, issue #14 remains open. See `docs/road-network-verification.md`.

## Test-driven development expectations

For behavioral changes, use the following order where practical:

1. state the expected behavior or invariant;
2. add/update a deterministic test that fails for the missing behavior;
3. implement the smallest coherent change;
4. run relevant focused tests, then the broader verification set;
5. update affected documentation; and
6. commit the behavior/test/documentation together when they represent one logical change.

Tests should verify observable semantics rather than private implementation details where possible.

## High-risk invariants

Particular attention should remain on:

- timezone-aware/UTC boundaries;
- units and CRS validation;
- missing-value semantics;
- separation of observations, forecasts and scenarios;
- source availability vs freshness vs last success;
- last-known-good retention;
- leakage-free chronological energy features/splits;
- model/dataset fingerprint binding;
- network parallel edges and immutable scenario overlays;
- facility snapping distance limits;
- persistence/restart behavior;
- bounded map projections never being presented as complete when truncated;
- stale viewport responses not replacing newer map state;
- route-selection clicks remaining separate from reference-object inspection;
- OSM provider/Overpass failure never being hidden by generated road topology;
- no synthetic composite score; and
- no production dependence on synthetic fixtures.

## Current testing gaps

The repository does not currently claim systematic load/performance testing, fault-injection against every provider, long-running soak testing, multi-process consistency testing, broad accessibility testing or security penetration testing. Browser acceptance covers the principal dashboard integration paths but is not a claim of exhaustive UI coverage. A successful real OSM Berlin road-network smoke is also still outstanding because the captured public Overpass attempts timed out externally.