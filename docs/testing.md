# Testing strategy

> This compatibility page is retained for existing links. The primary testing documentation is [development/testing.md](development/testing.md), and release/completion evidence is tracked in [verification.md](verification.md).

Development follows a red → green → refactor discipline for behavioral changes. Deterministic repository CI is separated from live external-provider compatibility.

## Required pull-request CI

The protected `main` ruleset requires all three GitHub Actions jobs on the final PR head:

### `backend`

1. Python 3.12 environment setup.
2. Ruff format check.
3. Ruff lint.
4. strict mypy.
5. pytest with coverage reporting.
6. ontology/knowledge validation.
7. production synthetic-data guard.
8. secret guard.
9. OpenAPI generation.

### `frontend`

1. Node 22 + `npm ci` using the committed lockfile.
2. frontend unit tests.
3. TypeScript/Vite production build.

### `containers`

After backend/frontend succeed:

1. install a pinned isolated Playwright runner;
2. validate Docker Compose configuration;
3. build the backend image;
4. seed an explicit deterministic acceptance-only reference snapshot;
5. build the frontend image;
6. start the composed backend/frontend stack;
7. verify backend, frontend and nginx-proxied health routes; and
8. run Playwright through nginx against the real FastAPI/persisted-state/React/MapLibre stack.

Current browser acceptance covers explicit unavailable state, deterministic workflow inspection, viewport-backed reference loading/reload, canonical map-object detail/provenance, fail-closed viewport errors, and baseline-vs-edge-closure route comparison. Populated derived/source/agent/reload-inspector acceptance is tracked in issue #15.

Normal deterministic tests do not require external providers. Fixture values remain test-only and must not be imported into production paths.

## Live verification

Live-source smoke testing is a separate scheduled/manual workflow because third-party outages, maintenance and schema changes are legitimate operational states rather than deterministic repository failures. A failed provider is reported as unavailable/schema-changed/decoder-unavailable; the smoke path never replaces it with generated urban data.

On **2026-09-14**, a real live smoke run passed against the three current live sources:

- Berliner Luftgütemessnetz: `available`, freshness `valid`;
- DWD: `available`, freshness `valid`;
- VBB GTFS-Realtime: `available`, freshness `valid`;
- 70 canonical observations produced.

The manual reference smoke verifies official facilities, climate features and VBB static stops, but it does not enable optional OSM road acquisition. Real Berlin road-network verification is tracked in issue #14.

## High-risk coverage

Tests prioritize:

- timezone normalization and UTC boundaries;
- explicit units, finite numerics and WGS84/CRS validation;
- provider missing-value semantics;
- observed/forecast/scenario separation;
- current Berlin LQI station-envelope parsing;
- source availability vs freshness/last-success behavior;
- last-known-good retention and validated hot reload;
- chronological energy splitting and leakage prevention;
- baseline/model metrics and dataset fingerprints;
- dependency cycles/stale propagation and incremental derivation execution;
- parallel network edges and immutable scenario overlays;
- facility-to-network snapping bounds;
- provenance and RDF projection;
- API degradation without state files;
- integrated assessment without a synthetic composite score;
- bounded viewport map semantics and stale-request races; and
- browser-level route/scenario interaction.

## Known verification gaps

Systematic performance/load/soak evidence, broad accessibility verification, the security baseline, full operational observability, real OSM road-network evidence, current real Berlin energy evaluation and several cross-domain/browser-inspector gates remain open. The authoritative status and issue links are maintained in [verification.md](verification.md).
