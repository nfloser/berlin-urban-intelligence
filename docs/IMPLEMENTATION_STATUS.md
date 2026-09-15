# Implementation Status

## Current phase

Phase 12 — runtime snapshot refresh and API reload, followed by dependency-driven orchestration integration.

## Last completed milestone

Baseline audit on `main` at `ba0570b`: CI is green and the composed backend/frontend HTTP smoke test is part of CI. The repository already contains typed canonical contracts, six domain agents, persisted runtime/reference/energy state, deterministic workflow mappings, semantic RDF projection, resilience routing/scenario support, FastAPI and a React/MapLibre dashboard.

## Current architectural state

- Persisted runtime/reference/energy state is loaded when the API lifespan starts.
- Runtime and reference stores use temporary-file replacement for snapshot writes.
- The API keeps the loaded snapshots and agent instances in `app.state` for the process lifetime.
- A small dependency graph implementation exists, but it is not yet the execution backbone of the orchestrator.
- The orchestrator still relies on fixed workflow-to-agent mappings.
- Dashboard/API support already exists for domain health, source state and resilience route/scenario interaction.

## Known external blockers

- No mandatory external credential blocker is known from the baseline audit.
- OSM-backed routing remains source-dependent and must degrade explicitly when the upstream acquisition path is unavailable.

## Known internal blockers

1. New persisted snapshots are not visible to the running API until restart.
2. Invalid replacement snapshots need explicit last-known-good reload behavior and diagnostics.
3. Dependency metadata/staleness is not yet integrated into deterministic orchestration and user-facing inspection.
4. Browser-level acceptance coverage is not yet part of the current CI workflow.
5. `docs/verification.md` is not yet maintained as an evidence-based completion matrix.

## Next concrete tasks

1. Add a tested snapshot reload controller that detects changed runtime/reference/energy files without reloading unchanged large snapshots.
2. Preserve last-known-good state when a changed snapshot is invalid and expose reload diagnostics.
3. Rebuild agents/orchestrator atomically after successful snapshot changes.
4. Update API/docs and verify through CI.
5. Continue with dependency graph validation, registry-driven agents and dependency-aware orchestration.

## Last successful verification commands

Verified by GitHub Actions CI run `34886257900` for `ba0570b`:

```text
ruff format --check src tests scripts
ruff check src tests scripts
mypy src/berlin_urban_intelligence
pytest --cov=berlin_urban_intelligence --cov-report=term-missing
python scripts/validate_knowledge.py
python scripts/check_production_data.py
python scripts/check_secrets.py
frontend: npm test
frontend: npm run build
docker compose config
docker build (backend + frontend)
docker compose HTTP health smoke
```

## Important migration notes

Do not replace the existing source/agent/domain architecture. Runtime reload must sit behind the existing persisted-state boundary and must not move provider acquisition into request handlers. Large reference snapshots should only be reparsed when their file identity changes.
