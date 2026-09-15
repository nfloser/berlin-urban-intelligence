# Implementation Status

## Current phase

Phase 15 — evidence-driven v1.0 completion audit and independently scoped follow-up work.

## Current development work

Issue #12 / PR #23 closes the semantic API parity gap identified by the v1.0 verification audit. The API now builds one RDF projection from validated runtime, reference, energy and derived snapshots, and exposes bounded typed incoming/outgoing semantic relationship inspection without introducing a second source of truth or unrestricted SPARQL execution.

## Recently completed work

- Issue #11 / PR #22 established `docs/verification.md` as the repository-wide completion evidence matrix, corrected orchestration/snapshot documentation drift and converted remaining gaps into independently scoped issues. Full protected CI passed before merge.
- Issue #2 / PR #8 replaced fixed 1,000-item map slices with bounded viewport-backed reference projection and canonical detail inspection. Final backend, frontend and Docker/Compose/Playwright CI passed before merge.
- Issue #3 audited stale PR #1 instead of blindly closing or merging it. Three still-needed invariants were recovered tests-first in PR #9: finite canonical numerical values, required heat/energy scenario parameters, and current/valid scenario baselines. PR #9 passed complete CI and merged; PR #1 was then closed without merge or history deletion.
- Issue #5 / PR #10 established the protected repository workflow. `Protect main` is active, has no bypass actors, requires pull requests/review-thread resolution and strictly requires GitHub Actions checks `backend`, `frontend` and `containers`.

## Current architectural state

- Runtime, reference, energy and derived state are persisted separately and loaded through validated stores.
- Runtime/reference stores use temporary-file replacement for snapshot writes.
- The API snapshot controller watches persisted runtime, reference, energy and derived files and reloads changed snapshots without requiring a backend restart.
- Invalid replacement snapshots retain the previous validated in-process value and expose reload diagnostics instead of replacing good state.
- Agent/orchestrator state is rebuilt after validated snapshot changes.
- `AgentRegistry` validates identifiers/dependencies and the orchestrator resolves workflow capabilities through the registry; real-agent metadata/cross-agent aggregation boundaries still need completion in issue #13.
- Derived information retains explicit definitions, upstream lineage, freshness/quality and dependency status and supports dependency-aware incremental recomputation.
- The API RDF projection now includes persisted derivation definitions/records and PROV upstream lineage in addition to runtime observations, reference objects and validated energy forecasts.
- `/api/v1/knowledge/relations/{resource_id}` queries the same in-memory semantic projection with deterministic incoming/outgoing relations and explicit total/returned/truncated metadata.
- FastAPI exposes domain state, provenance, source/agent health, resilience routing/scenario operations, derived/dependency/semantic inspection and bounded reference-map projections.
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

All three are bound to the GitHub Actions integration.

## Current v1.0 evidence gaps

The authoritative detail is in [`verification.md`](verification.md). After semantic API parity is closed, the remaining concrete follow-up issues are:

1. #13 — complete agent metadata and enforce orchestration boundaries.
2. #14 — verify real Berlin road-network acquisition and resilience readiness.
3. #15 — complete populated dashboard inspector browser acceptance.
4. #16 — add accessibility and keyboard verification.
5. #17 — establish performance/load evidence.
6. #18 — establish repository/deployment security baseline.
7. #19 — extend structured observability across refresh/derivation/scenarios.
8. #20 — verify a reproducible real Berlin energy evaluation/forecast artefact.
9. #21 — verify multiple source-backed cross-domain workflows end to end.

## Known external constraints

- Current provider availability remains external to deterministic CI and is checked through separate smoke/evaluation workflows.
- OSM-backed routing remains source-dependent and must degrade explicitly when acquisition is unavailable; deterministic routing fixtures are not proof of current Berlin road-network acquisition.
- Real Berlin energy evidence depends on an accessible, semantically appropriate Stromnetz Berlin publication; external unavailability must remain explicit rather than being replaced with synthetic data.

## Completed reliability milestones

- Persisted snapshots can hot-reload into a running API.
- Invalid replacement snapshots preserve last-known-good state and expose diagnostics.
- Browser-level acceptance exists in CI and uses an explicit acceptance-only fixture rather than a production synthetic fallback.
- Baseline and hypothetical route results are kept distinct and can be compared end to end.
- Map-layer readiness has an explicit browser-test signal and project-owned layers can fall back to a local background style when the external basemap style is unavailable.
- The bounded reference-map API reports per-layer totals, viewport matches, returned counts and truncation instead of silently implying completeness.
- Stale repository history is audited behavior-by-behavior before closure; required behavior is ported onto current `main` through new tests rather than merging obsolete integration history.
- `main` is protected by an active ruleset requiring PRs and all three project CI jobs.
- The repository maintains an explicit PASS/PARTIAL/NOT VERIFIED completion matrix rather than treating implementation presence as proof of v1.0 readiness.
- Public semantic graph serialization and typed semantic relation inspection now use the same validated snapshot projection, including derived lineage.

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

1. Finish issue #12 through final protected CI/review and merge.
2. Address #13 next: complete real-agent metadata and remove direct cross-agent invocation from the Live State boundary.
3. Run/implement the external real-data verification gates #14 and #20 without converting provider failure into synthetic success.
4. Close dashboard/operational quality gaps #15–#19 in independent PRs.
5. Complete #21 only after its dependent source/semantic evidence is sufficient.
6. Reassess the project-wide v1.0 completion gate only when `docs/verification.md` contains no unqualified critical gap.

## Important migration notes

Do not replace the existing source/agent/domain architecture. Provider acquisition remains outside request handlers. Canonical persisted state stays authoritative; RDF and bounded map GeoJSON are projections only. Large reference snapshots should be reparsed only when their persisted file identity changes, while the browser should request only the active viewport and fetch full canonical objects on demand.
