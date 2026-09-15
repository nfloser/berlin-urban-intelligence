# Implementation Status

## Current phase

Phase 15 — evidence-driven v1.0 completion audit and independently scoped follow-up work.

## Current development work

Issue #15 / PR #28 closes the populated dashboard-inspector acceptance gap identified by the v1.0 audit. Deterministic acceptance state now persists minimal explicit reference, runtime/source-status and derived-lineage snapshots through the same typed stores used by the application. The composed nginx → FastAPI → persisted state → React/MapLibre browser path verifies derived definition/producer/upstream provenance/freshness, configured source metadata plus runtime availability/freshness/error semantics, real agent identity/capabilities/dependencies/health, snapshot reload diagnostics, existing map/detail behavior and baseline-versus-disruption routing.

Implementation head `0e49f7644406af54964300b44468ce253c0fe4f2` passed GitHub Actions run `34989105040`: `backend`, `frontend` and `containers` were all successful, and Playwright reported **6 passed**. The work also exposed and fixed a production-installation path defect for the source registry: `BUI_SOURCE_REGISTRY` is now an explicit configuration input and Compose points it to `/app/config/sources.yaml`. The remaining step for PR #28 is final documentation-head CI and merge.

Issue #14 remains separately **EXTERNAL/BLOCKED**. Its repository verification/degradation infrastructure is already merged on `main`, but the two captured point-in-time public Overpass attempts on 2026-09-15 both timed out before a real Berlin network could be produced: run `34979600413` hit a 180-second `ConnectTimeout` at `overpass-api.de`; run `34980820676` hit a 180-second `ReadTimeout` at `https://overpass.private.coffee/api`. Both failure artifacts recorded `synthetic_fallback=false`. A real non-empty network plus baseline route is still required before #14 can close.

## Recently completed work

- Issue #14 / PR #27 merged the real-road verification/degradation infrastructure without fabricating provider success. A dedicated road-network smoke path, strict canonical OSM readiness validation, opt-in provenance-visible routing imputation, real baseline-route verification contract and last-known-good failure semantics are now on `main`; #14 remains open because live Overpass acquisition is externally blocked.
- Issue #13 / PR #26 completed the real-agent metadata/composition boundary. All six real agents expose explicit name/domain/capability/input/output metadata; `AgentRegistry` owns capability resolution; Live State aggregates typed `AgentHealth` values supplied by the API composition boundary rather than invoking domain agents. Full protected CI passed before merge.
- Issue #12 / PR #23 closed semantic API parity: public graph serialization now includes persisted derived lineage and the API exposes bounded typed incoming/outgoing semantic relationship inspection. Full protected CI passed before merge.
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
- Source registry loading supports the explicit `BUI_SOURCE_REGISTRY` deployment path; Compose uses `/app/config/sources.yaml`, avoiding assumptions about package-install filesystem layout.
- All six real `AgentDescriptor` instances expose explicit names/domains plus capabilities and typed input/output contracts; domain agents retain explicit source dependencies where applicable.
- `AgentRegistry` validates required/optional agent dependencies, topological ordering and missing/cyclic dependencies, and owns unique capability resolution/ambiguity errors used by the orchestrator.
- Live State declares required dependencies on Mobility, Exposure, Heat, Energy and Resilience but does not own or invoke those agents. The API composition layer collects typed domain `AgentHealth` values and supplies them to `LiveStateAgent` for aggregation.
- Derived information retains explicit definitions, upstream lineage, freshness/quality and dependency status and supports dependency-aware incremental recomputation.
- The API RDF projection includes persisted derivation definitions/records and PROV upstream lineage in addition to runtime observations, reference objects and validated energy forecasts.
- `/api/v1/knowledge/relations/{resource_id}` queries the same in-memory semantic projection with deterministic incoming/outgoing relations and explicit total/returned/truncated metadata.
- FastAPI exposes domain state, provenance, source/agent health, resilience routing/scenario operations, derived/dependency/semantic inspection and bounded reference-map projections.
- The React/MapLibre dashboard exposes reference inspection, observation provenance, platform/derived inspection, deterministic workflows, heat scenarios and map-selected resilience route comparison.
- Reference-map rendering uses `/api/v1/map/reference` as a compact rendering projection and `/api/v1/map/reference/{layer}/{resource_id}` for full canonical detail inspection.
- Browser acceptance is part of the normal PR CI path through the composed nginx → FastAPI → persisted-state → React/MapLibre stack and now includes populated source/agent/derived/reload inspector verification.
- Canonical numerical contracts reject `NaN` and infinities; heat/energy scenario kinds require their explicit deltas; integrated assessment rejects stale/future/invalid heat baselines and energy forecasts outside their validity interval.
- Optional real road-network acquisition can be verified separately from deterministic CI. Its readiness contract requires non-empty OSM nodes/edges, valid coordinates/endpoints, positive routing attributes, ODbL/source provenance, provenance-visible imputation where enabled, and a real baseline route. Provider failure never becomes a synthetic success.

## Repository governance state

The `Protect main` repository ruleset is **Active** and targets the default branch. It has no bypass actors, blocks branch deletion and force/non-fast-forward pushes, requires pull requests, requires review-thread resolution, and uses strict required-status-check semantics.

The three merge-critical GitHub Actions checks are:

- `backend`
- `frontend`
- `containers`

All three are bound to the GitHub Actions integration.

## Current v1.0 evidence gaps

The authoritative detail is in [`verification.md`](verification.md). After #15 acceptance, the remaining concrete follow-up issues are:

1. #14 — **EXTERNAL/BLOCKED**: repository verification/degradation infrastructure is implemented, but a successful real Berlin OSM network plus baseline route is still missing because both captured public Overpass attempts timed out.
2. #16 — add accessibility and keyboard verification.
3. #17 — establish performance/load evidence.
4. #18 — establish repository/deployment security baseline.
5. #19 — extend structured observability across refresh/derivation/scenarios.
6. #20 — verify a reproducible real Berlin energy evaluation/forecast artefact.
7. #21 — verify multiple source-backed cross-domain workflows end to end.

Issue #15 is no longer an evidence gap once PR #28 merges: its persisted inspector behavior has complete composed browser acceptance.

## Known external constraints

- Current provider availability remains external to deterministic CI and is checked through separate smoke/evaluation workflows.
- OSM-backed routing remains source-dependent and must degrade explicitly when acquisition is unavailable; deterministic routing fixtures are not proof of current Berlin road-network acquisition. The current #14 blocker is backed by two explicit public Overpass timeout artifacts rather than inferred from fixture behavior.
- Real Berlin energy evidence depends on an accessible, semantically appropriate Stromnetz Berlin publication; external unavailability must remain explicit rather than being replaced with synthetic data.

## Completed reliability milestones

- Persisted snapshots can hot-reload into a running API.
- Invalid replacement snapshots preserve last-known-good state and expose diagnostics.
- Browser-level acceptance exists in CI and uses explicit acceptance-only reference/runtime/derived fixtures rather than a production synthetic fallback.
- Populated derived provenance/lineage, source health/error semantics, agent capabilities/dependencies/health and reload diagnostics are verified through the actual composed browser stack.
- Baseline and hypothetical route results are kept distinct and can be compared end to end.
- Map-layer readiness has an explicit browser-test signal and project-owned layers can fall back to a local background style when the external basemap style is unavailable.
- The bounded reference-map API reports per-layer totals, viewport matches, returned counts and truncation instead of silently implying completeness.
- Stale repository history is audited behavior-by-behavior before closure; required behavior is ported onto current `main` through new tests rather than merging obsolete integration history.
- `main` is protected by an active ruleset requiring PRs and all three project CI jobs.
- The repository maintains an explicit PASS/PARTIAL/EXTERNAL-BLOCKED/NOT VERIFIED completion matrix rather than treating implementation presence as proof of v1.0 readiness.
- Public semantic graph serialization and typed semantic relation inspection use the same validated snapshot projection, including derived lineage.
- Real-agent dependency/capability metadata is executable registry data rather than documentation-only metadata; Live State aggregation no longer creates an agent-to-agent call path.
- Real OSM road verification is reproducible as a separate smoke workflow with explicit failure evidence, endpoint selection, opt-in imputation and no synthetic production fallback.
- Installed Docker deployments resolve the source registry through an explicit configured path instead of relying on source-checkout-relative `__file__` assumptions.

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

1. Merge PR #28 only after the final documentation head again passes `backend`, `frontend` and `containers`; close #15 through that verified merge.
2. Keep #14 open as EXTERNAL/BLOCKED and rerun its live road smoke later when a public provider is responsive; do not substitute deterministic fixtures for live evidence.
3. Address #16–#19 as independent dashboard/operational quality PRs, preserving the same TDD/evidence discipline.
4. Verify the real Berlin energy gate #20 independently of deterministic model tests.
5. Complete #21 only after its dependent source/semantic evidence is sufficient.
6. Reassess the project-wide v1.0 completion gate only when `docs/verification.md` contains no unqualified critical gap.

## Important migration notes

Do not replace the existing source/agent/domain architecture. Provider acquisition remains outside request handlers. Canonical persisted state stays authoritative; RDF and bounded map GeoJSON are projections only. Cross-agent coordination belongs at composition/orchestration boundaries, while individual agents consume typed inputs and remain independently testable. Large reference snapshots should be reparsed only when their persisted file identity changes, while the browser should request only the active viewport and fetch full canonical objects on demand.
