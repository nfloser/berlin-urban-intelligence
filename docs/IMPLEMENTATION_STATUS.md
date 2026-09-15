# Implementation Status

## Current phase

Phase 13 — interactive dashboard completion and scalable reference-map delivery, while preserving the persisted-state and agent boundaries established by the runtime architecture.

## Current development work

Issue #2 / PR #8 migrates reference-map rendering from fixed 1,000-item canonical list requests to a bounded viewport projection. The branch remains under CI and review and is not considered complete until the full backend, frontend and container/browser acceptance workflow is green.

## Current architectural state

- Runtime, reference, energy and derived state are persisted separately and loaded through validated stores.
- Runtime/reference stores use temporary-file replacement for snapshot writes.
- The API snapshot controller watches persisted runtime, reference, energy and derived files and reloads changed snapshots without requiring a backend restart.
- Invalid replacement snapshots retain the previous validated in-process value and expose reload diagnostics instead of replacing good state.
- Agent/orchestrator state is rebuilt after validated snapshot changes.
- Derived information retains explicit definitions, upstream lineage and dependency status; deterministic orchestration still uses defined workflow mappings rather than claiming a fully dynamic planner.
- FastAPI exposes domain state, provenance, source/agent health, resilience routing/scenario operations, derived/dependency inspection and bounded reference-map projections.
- The React/MapLibre dashboard exposes reference inspection, observation provenance, platform/derived inspection, deterministic workflows, heat scenarios and map-selected resilience route comparison.
- Reference-map rendering uses `/api/v1/map/reference` as a compact rendering projection and `/api/v1/map/reference/{layer}/{resource_id}` for full canonical detail inspection.
- Browser acceptance is part of the normal PR CI path through the composed nginx → FastAPI → persisted-state → React/MapLibre stack.

## Known external constraints

- No mandatory external credential blocker is currently known for deterministic repository verification.
- Current live/reference provider availability remains external to deterministic CI and is checked by separate smoke workflows.
- OSM-backed routing remains source-dependent and must degrade explicitly when acquisition is unavailable.

## Known internal gaps

1. PR #8 must complete full CI and independent review before the viewport map migration can be merged.
2. The dependency graph is not yet a complete registry-driven execution backbone for every orchestrated capability; deterministic workflow mappings still exist.
3. `docs/verification.md` is not yet maintained as a repository-wide evidence matrix.
4. `main` is currently unprotected; repository-governance work is tracked separately in issue #5.
5. The repository does not yet claim systematic load/performance testing, long-running soak testing, multi-process consistency guarantees, exhaustive accessibility verification or security penetration testing.

## Completed reliability milestones

- Persisted snapshots can hot-reload into a running API.
- Invalid replacement snapshots preserve last-known-good state and expose diagnostics.
- Browser-level acceptance exists in CI and uses an explicit acceptance-only fixture rather than a production synthetic fallback.
- Baseline and hypothetical route results are kept distinct and can be compared end to end.
- Map-layer readiness has an explicit browser-test signal and the project-owned layers can fall back to a local background style when the external basemap style is unavailable.
- The bounded reference-map API reports per-layer totals, viewport matches, returned counts and truncation instead of silently implying completeness.

## Verification commands enforced by CI

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
```

The current feature branch must pass this complete set before PR #8 leaves draft status. A successful unit or build subset is not treated as proof of feature completion.

## Next concrete tasks

1. Complete CI and browser acceptance for PR #8, review the complete diff and resolve findings before merge.
2. Close or supersede the stale integration PR #1 after confirming it contains no unique required work (issue #3).
3. Address repository branch/CI governance in issue #5 without mixing it into the map feature.
4. Establish an evidence-based verification matrix for remaining platform completion gates.
5. Continue dependency/registry-driven orchestration work in independently scoped issues/PRs rather than a single catch-all change.

## Important migration notes

Do not replace the existing source/agent/domain architecture. Provider acquisition remains outside request handlers. Canonical persisted state stays authoritative; bounded map GeoJSON is a rendering projection only. Large reference snapshots should be reparsed only when their persisted file identity changes, while the browser should request only the active viewport and fetch full canonical objects on demand.
