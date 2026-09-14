# Code quality

Code quality is enforced through executable CI gates rather than style guidance alone.

## Python gates

- **Ruff formatting**: `ruff format --check src tests scripts`
- **Ruff linting**: `ruff check src tests scripts`
- **Strict mypy**: `mypy src/berlin_urban_intelligence`
- **pytest + coverage**: behavioral verification and coverage reporting

The package targets Python 3.12 in Ruff configuration and uses strict mypy settings from `pyproject.toml`.

## Frontend gates

- `npm ci` from committed lockfile;
- `npm test` (Vitest);
- `npm run build`, which includes `tsc --noEmit` before Vite build.

## Semantic/data safety gates

- `validate_knowledge.py` checks ontology/semantic artefacts;
- `check_production_data.py` guards against synthetic fixture leakage into production paths;
- `check_secrets.py` provides a repository-level secret guard;
- FastAPI OpenAPI generation ensures API route/model definitions can be materialized.

## Design-quality expectations

Code review should additionally ask whether a change:

- preserves canonical state/provenance semantics;
- makes missing/failed data explicit;
- uses the correct CRS/time/unit boundary;
- avoids hidden provider calls in request handlers;
- keeps scenario data hypothetical;
- avoids unsupported accuracy/performance claims;
- has deterministic tests at the appropriate boundary; and
- updates documentation when behavior changes.

## Logging

Use the structured logging utilities rather than ad-hoc sensitive payload logging for platform operations. The formatter deliberately limits context fields. Avoid adding request bodies, credentials or full external payloads to normal logs.

## Dependency quality

New dependencies should have a clear architectural purpose and should not duplicate functionality already provided by the existing stack without justification. Optional heavy/provider-specific dependencies should remain optional where possible, following the current OSM pattern.

## Documentation quality

Documentation is considered part of correctness. Commands, paths, environment variables and endpoint behavior must be validated against the repository. Planned functionality must not be presented as implemented.
