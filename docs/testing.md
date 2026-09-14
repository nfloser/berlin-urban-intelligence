# Testing strategy

Development follows a red → green → refactor discipline for contracts, source boundaries and cross-domain behavior.

## Deterministic CI

The permanent GitHub Actions pipeline runs:

1. Python 3.12 environment setup.
2. Ruff format check.
3. Ruff lint.
4. strict mypy.
5. pytest with coverage reporting.
6. ontology/knowledge validation.
7. production synthetic-data guard.
8. secret guard.
9. OpenAPI generation.
10. Node 22 + `npm ci` using the committed lockfile.
11. frontend tests.
12. frontend production build.
13. Docker Compose configuration validation.
14. backend image build.
15. frontend image build.
16. running Compose backend/frontend HTTP smoke test, including the proxied `/health` route.

Normal tests do not require external providers. Fixture values remain test-only and must not be imported into production paths.

## Live verification

Live-source smoke testing is a separate scheduled/manual workflow because third-party outages, maintenance and schema changes are legitimate operational states rather than deterministic repository failures. A failed provider is reported as unavailable/schema-changed/decoder-unavailable; the smoke path never replaces it with generated urban data.

On **2026-09-14**, a real live smoke run passed against all three current live sources:

- Berliner Luftgütemessnetz: `available`, freshness `valid`;
- DWD: `available`, freshness `valid`;
- VBB GTFS-Realtime: `available`, freshness `valid`;
- 70 canonical observations produced.

The run also caught an upstream Berlin-air schema change before the adapter was updated, demonstrating why the live workflow is intentionally separate and retained as an operational compatibility check.

## High-risk coverage

Tests prioritize:

- timezone normalization and UTC boundaries;
- explicit units and WGS84/CRS validation;
- provider missing-value semantics;
- observed/scenario separation;
- current Berlin LQI station-envelope parsing;
- source availability vs freshness/last-success behavior;
- last-known-good retention;
- chronological energy splitting and leakage prevention;
- baseline/model metrics and dataset fingerprints;
- parallel network edges and immutable scenario overlays;
- facility-to-network snapping bounds;
- provenance and RDF projection;
- persistence/restart behavior;
- API degradation without state files;
- integrated assessment without a synthetic composite score;
- frontend unavailable-state and interaction semantics.