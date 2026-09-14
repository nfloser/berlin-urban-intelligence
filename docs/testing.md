# Testing strategy

Development follows a red → green → refactor discipline for contracts, source boundaries and cross-domain behavior.

## Deterministic CI

The normal GitHub Actions pipeline runs:

1. Ruff format check.
2. Ruff lint.
3. strict mypy.
4. pytest with coverage reporting.
5. ontology/knowledge validation.
6. production synthetic-data guard.
7. secret guard.
8. OpenAPI generation.
9. frontend tests and production build.
10. Docker Compose configuration and image builds after backend/frontend gates pass.

Normal tests must not require live external services. Fixture values live only under tests and are labelled as fixtures.

## Live verification

Live-source smoke testing is a separate workflow because third-party outages, maintenance and schema changes are real operational states rather than deterministic code failures. A failed live source must be reported as unavailable/schema-changed/decoder-unavailable; tests must never replace it with generated urban data.

## High-risk cases

Tests should prioritize time-zone handling, unit requirements, WGS84 bounds, observed/scenario separation, source schema parsing, energy leakage prevention, model/dataset fingerprints, parallel network edges, scenario immutability, provenance projection, persistence and degraded API behavior.
