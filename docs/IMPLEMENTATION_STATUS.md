# Implementation Status

## Current phase

Phase 14 — repository governance and evidence-driven completion work after the interactive dashboard/reference-map milestone.

## Current development work

Issue #5 formalizes the required Issue → Branch → PR → CI → Review → Merge workflow. Repository owner configuration has now activated the `Protect main` ruleset; the branch records the verified technical state and the repository workflow that future work must follow.

## Recently completed work

- Issue #2 / PR #8 replaced fixed 1,000-item map slices with bounded viewport-backed reference projection and canonical detail inspection. Final backend, frontend and Docker/Compose/Playwright CI passed before merge.
- Issue #3 audited stale PR #1 instead of blindly closing or merging it. Three still-needed invariants were recovered tests-first in PR #9: finite canonical numerical values, required heat/energy scenario parameters, and current/valid scenario baselines. PR #9 passed complete CI and merged; PR #1 was then closed without merge or history deletion.

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
- Canonical numerical contracts reject `NaN` and infinities; heat/energy scenario kinds require their explicit deltas; integrated assessment rejects stale/future/invalid heat baselines and energy forecasts outside their validity interval.

## Repository governance state

The `Protect main` repository ruleset is **Active** and targets the default branch. It has no bypass actors, blocks branch deletion and force/non-fast-forward pushes, requires pull requests, requires review-thread resolution, and uses strict required-status-check semantics.

The three merge-critical GitHub Actions checks are:

- `backend`
- `frontend`
- `containers`

All three are bound to the GitHub Actions integration. Future substantive development is therefore technically constrained to the documented issue-linked branch/PR workflow rather than relying only on convention.

## Known external constraints

- No mandatory external credential blocker is currently known for deterministic repository verification.
- Current live/reference provider availability remains external to deterministic CI and is checked by separate smoke workflows.
- OSM-backed routing remains source-dependent and must degrade explicitly when acquisition is unavailable.

## Known internal gaps

1. `docs/verification.md` is not yet maintained as a repository-wide evidence matrix.
2. The dependency graph is not yet a complete registry-driven execution backbone for every orchestrated capability; deterministic workflow mappings still exist.
3. The repository does not yet claim systematic load/performance testing, long-running soak testing, multi-process consistency guarantees, exhaustive accessibility verification or security penetration testing.
4. The project-wide v1.0 completion gate has not been declared passed.

## Completed reliability milestones

- Persisted snapshots can hot-reload into a running API.
- Invalid replacement snapshots preserve last-known-good state and expose diagnostics.
- Browser-level acceptance exists in CI and uses an explicit acceptance-only fixture rather than a production synthetic fallback.
- Baseline and hypothetical route results are kept distinct and can be compared end to end.
- Map-layer readiness has an explicit browser-test signal and project-owned layers can fall back to a local background style when the external basemap style is unavailable.
- The bounded reference-map API reports per-layer totals, viewport matches, returned counts and truncation instead of silently implying completeness.
- Stale repository history is audited behavior-by-behavior before closure; required behavior is ported onto current `main` through new tests rather than merging obsolete integration history.
- `main` is protected by an active ruleset requiring PRs and all three project CI jobs.

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

Passing only a subset is not treated as proof that a PR is merge-ready.

## Next concrete tasks

1. Establish `docs/verification.md` as an evidence-based matrix for remaining platform completion gates.
2. Continue dependency/registry-driven orchestration work in independently scoped issues/PRs.
3. Continue final performance, accessibility, security and live-provider acceptance work without overstating project completion.
4. Reassess the project-wide v1.0 completion gate only after the evidence matrix has no unqualified critical gaps.

## Important migration notes

Do not replace the existing source/agent/domain architecture. Provider acquisition remains outside request handlers. Canonical persisted state stays authoritative; bounded map GeoJSON is a rendering projection only. Large reference snapshots should be reparsed only when their persisted file identity changes, while the browser should request only the active viewport and fetch full canonical objects on demand.
