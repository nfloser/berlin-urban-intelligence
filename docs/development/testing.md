# Testing strategy

Testing separates deterministic repository correctness from live external-provider compatibility.

## Deterministic backend tests

Backend tests use pytest and synthetic fixtures that are never read by production runtime paths. Current test areas include canonical contracts, API behavior, integrated assessment, data/source pipelines, energy evaluation, knowledge projection, reference acquisition, resilience calculations, scenarios, source-registry behavior and bounded reference-map projections.

The main command used by CI is:

```bash
pytest --cov=berlin_urban_intelligence --cov-report=term-missing
```

Coverage is reported as diagnostic evidence; the repository does not currently define a numeric coverage threshold as a release criterion.

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
- no synthetic composite score; and
- no production dependence on synthetic fixtures.

## Current testing gaps

The repository does not currently claim systematic load/performance testing, fault-injection against every provider, long-running soak testing, multi-process consistency testing, broad accessibility testing or security penetration testing. Browser acceptance covers the principal dashboard integration paths but is not a claim of exhaustive UI coverage.
