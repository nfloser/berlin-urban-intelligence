# v1.0 verification evidence matrix

This document is the evidence-driven completion gate for Berlin Urban Intelligence. It distinguishes implemented architecture from behavior that is actually verified.

## Status vocabulary

- **PASS** — the required behavior is implemented and backed by deterministic repository evidence and, where the gate is inherently operational, appropriate end-to-end/live evidence.
- **PARTIAL** — meaningful implementation/evidence exists, but an explicit acceptance requirement remains unverified or incomplete.
- **EXTERNAL/BLOCKED** — completion depends on an external provider or environment and the repository cannot legitimately fabricate success.
- **NOT VERIFIED** — the repository has no sufficient verification evidence for the gate.
- **NOT READY** — aggregate release/completion status while any critical gate is not PASS.

A unit test, architecture diagram or successful build is not by itself proof of end-to-end or scientific correctness. Point-in-time live smoke evidence proves provider compatibility only at that timestamp.

## Audit baseline

This matrix was established from current repository code, tests, documentation and GitHub Actions while addressing issue #11 on 2026-09-15 and is updated as independently scoped completion issues are verified.

Recent complete deterministic acceptance evidence includes:

- PR #8: viewport-backed map/detail inspection and route disruption acceptance, with backend/frontend/container/browser CI green before merge;
- PR #9: restored canonical/scenario invariants, with backend/frontend/container/browser CI green before merge;
- PR #10: repository governance documentation on final head `5b7f830691a8637f86d8fd8f2c0d7d6ec2ac7e3f`, GitHub Actions run `34962033938`, all required jobs `backend`, `frontend`, and `containers` successful;
- PR #22: repository-wide verification matrix and documentation-drift correction, merged after all protected checks passed;
- PR #23 / issue #12: RED integration tests first reproduced missing derived graph parity and missing relationship queries; subsequent code passed format/lint, strict mypy and the complete pytest suite before final documentation/CI verification;
- active repository ruleset `Protect main` requires those three GitHub Actions checks with strict/up-to-date branch semantics and no bypass actors.

The permanent CI contract is `.github/workflows/ci.yml`. Live-source compatibility is intentionally separated into `.github/workflows/live-source-smoke.yml`; reference-source compatibility has a separate manual workflow.

## Evidence matrix

| Gate | Status | Current evidence | Remaining evidence / issue |
|---|---|---|---|
| Modular source → canonical → agent/API architecture | **PASS** | `docs/architecture.md`; adapter/runtime/agent separation under `src/berlin_urban_intelligence/`; provider acquisition remains outside request handlers. | Reassess only if boundaries are changed. |
| Canonical contracts, epistemic state, UTC, units, CRS and finite numerics | **PASS** | `shared/contracts.py`; `tests/test_contracts.py`; PR #9 restored rejection of `NaN`/±infinity. | None for current contract version. |
| Provenance retained across canonical values | **PASS** | `Provenance` contract; adapter/data-pipeline tests; RDF projection; map canonical detail inspector; `docs/data/provenance.md`; semantic relationship queries expose PROV links. | Re-test when new provenance-bearing resource types are added. |
| No fabricated production measurements/fallbacks | **PASS** | Explicit unavailable/unknown semantics; `scripts/check_production_data.py`; deterministic fixtures are CI-only; runtime/source tests and docs. | Continue enforcing on future integrations. |
| Live DWD/Berlin LQI/VBB acquisition, freshness and failure semantics | **PASS** | `runtime/refresh.py`; source-status models/tests; scheduled/manual `live-source-smoke.yml`; point-in-time successful live smoke documented for 2026-09-14. | Provider availability can regress externally; scheduled smoke remains operational evidence, not a permanent guarantee. |
| Official facility/climate/VBB-static reference acquisition | **PARTIAL** | `ReferenceRefreshCoordinator`, `ReferenceAcquisitionCoordinator`; deterministic reference tests; `reference-smoke-once.yml` verifies non-empty facilities/climate/stops when run. | Workflow is not permanent scheduled monitoring and does not cover OSM road topology. Real network completion is #14. |
| Atomic persisted state and last-known-good replacement semantics | **PASS** | `runtime/atomic.py`, state stores, `runtime/reload.py`; `tests/test_atomic_storage.py`, `tests/test_api.py`; invalid replacement keeps previous validated in-process state. | Multi-process synchronized rollout is outside current single-process deployment guarantee. |
| Automatic runtime/reference/energy/derived hot reload | **PASS** | `_ApiStateController` watches all four persisted states before requests; frontend snapshot-token polling; API regression tests. | Compatibility documentation drift found by the audit has been corrected. |
| Source-specific cadence / persistent live refresh worker | **PASS** | `runtime/worker.py`; `scripts/refresh_live.py --interval-seconds`; Compose `refresh` service defaults to configurable 300 s interval; reference/energy operations remain separate. | No claim that every slow source is auto-scheduled. |
| Six domain/aggregation agents exist and expose health | **PASS** | Live State, Mobility, Exposure, Heat, Energy, Resilience agents; `/api/v1/agents` and `/agents/health`; deterministic domain/API tests. | Metadata/dependency-boundary quality is a separate partial gate (#13). |
| Real-agent descriptor completeness and cross-agent boundary discipline | **PARTIAL** | `AgentDescriptor` supports name/domain/contracts/source/agent dependencies; `AgentRegistry` validates dependency order/cycles; orchestrator resolves capabilities. | Several real descriptors still omit optional name/domain metadata and `LiveStateAgent` directly owns/invokes other agents. Fix in #13. |
| Registry-driven deterministic workflow resolution | **PASS** | `orchestrator/engine.py` resolves `_WORKFLOW_CAPABILITIES` through `AgentRegistry` and dependency order; `tests/test_orchestrator.py`, `tests/test_agent_registry.py`. | Re-test as new agent dependencies/capabilities are introduced. |
| Derivation definitions, provenance, freshness/status and dependency DAG | **PASS** | `knowledge/derivations.py`, `runtime/derived.py`, `shared/dependencies.py`; derivation/dependency tests cover cycles, stale propagation and execution failures. | Cross-domain breadth is separate (#21). |
| Dependency-aware incremental derived recomputation | **PASS** | `runtime/derived_refresh.py`, `knowledge/execution.py`; `tests/test_derived_refresh.py`, `tests/test_derivation_execution.py`; unaffected records are retained. | None for current persisted derived products. |
| Source-backed derived products avoid synthetic fallback/composite score | **PASS** | `DerivedProductBuilder` emits VBB delayed-update share and Heat + Air Quality descriptive context only when inputs exist; `tests/test_derived_products.py`. | Multiple cross-domain end-to-end workflows remain partial (#21). |
| Semantic RDF projection of canonical state | **PASS** | `knowledge/graph.py`, ontology/shapes, `tests/test_knowledge_graph.py`, `scripts/validate_knowledge.py`; API graph builds from validated runtime/reference/energy/derived state. | Re-test when semantic resource types change. |
| Derived lineage in semantic projection | **PASS** | `knowledge/derived_graph.py` projects derivation definitions/records and PROV lineage; `refresh_live.py` includes it in generated RDF; `/api/v1/graph` now projects persisted `DerivedState`; `tests/test_semantic_api.py` verifies definition and upstream lineage triples. | None for current derived graph contract. |
| Semantic relationships used as an inspectable/queryable API capability | **PASS** | `knowledge/relations.py`; `/api/v1/knowledge/relations/{resource_id}` returns bounded deterministic incoming/outgoing RDF relations with node kind and truncation metadata; integration tests cover observation, facility, forecast, derived, missing resource and bounding. | No unrestricted SPARQL endpoint is claimed or required for current scope. |
| Real Berlin road-network/reference completeness | **PARTIAL** | OSM acquisition adapter/coordinator and deterministic network/routing tests exist; CI acceptance uses an explicit test-only network fixture. | Existing reference smoke does not enable OSM and therefore does not prove non-empty live Berlin network nodes/edges. #14. |
| Resilience routing/accessibility and immutable disruption overlays | **PASS** | `agents/resilience.py`; parallel-edge, snapping and scenario tests; Playwright baseline 100 s → disrupted 160 s acceptance fixture. | Scientific/operational quality remains conditional on real road/reference data (#14). |
| Scenario validation and baseline isolation | **PASS** | `scenario_engine/`; scenario tests; PR #9 requires explicit heat/energy deltas and rejects stale/future/invalid baselines; route overlays copy baseline graph. | None for current supported scenario kinds. |
| Baseline/scenario/difference presented distinctly in dashboard | **PASS** | Map-selected route comparison renders baseline/scenario and delta; Playwright verifies 100 s baseline, 160 s scenario, +60 s/+60%. | Extend inspector/browser breadth in #15. |
| Berlin Energy evaluation/forecast implementation | **PASS** | Leakage-safe chronological pipeline, baseline/candidate metrics, dataset fingerprint binding and `EnergyAgent` acceptance checks have deterministic tests. | This gate covers software behavior, not proof of a current real Berlin run. |
| Current reproducible real Berlin energy artefact | **PARTIAL** | Explicit Stromnetz Berlin input path and semantics are documented; no UCI data is exposed as Berlin. | Point-in-time real acquisition/evaluation/persistence/API evidence is not yet recorded. #20. |
| Multiple defensible source-backed cross-domain workflows | **PARTIAL** | Heat + Air Quality descriptive context is persisted; integrated assessment can coordinate Heat/Energy/Resilience independently without a composite score. | At least a second populated real/persisted cross-domain workflow and browser evidence remain unverified; depends partly on #20. #21. |
| Partial failure isolation across cross-domain assessment | **PASS** | `IntegratedAssessmentService` returns per-dimension unavailable/error state rather than fabricating or failing the whole response; assessment tests cover missing/stale baselines. | Re-test when new workflows are added. |
| API exposes system/source/agent/domain/reference/scenario/derived/dependency/map/semantic surfaces | **PASS** | FastAPI routes and OpenAPI generation gate; API/map/derived/semantic tests; bounded list/map/relation endpoints. | Reassess when API contracts expand. |
| Map-optimized bounded reference API | **PASS** | `/api/v1/map/reference` bbox filtering, per-layer total/matched/returned/truncated metadata, canonical detail endpoint; API/unit/browser tests. | Performance under large real snapshots is not benchmarked (#17). |
| Dashboard analytical map and layer interaction | **PASS** | MapLibre viewport loads, layer toggles, canonical object inspection, routing selection, scenario overlay and external-style fallback are implemented/tested. | Broad accessibility is #16. |
| Dashboard provenance/derived/platform inspector implementation | **PASS** | `DerivedInspector`, `PlatformInspector`, canonical reference inspector and source/agent endpoints exist; frontend unit/build checks pass. | Full populated browser acceptance of derived/source/agent/reload inspectors is still missing (#15). |
| End-to-end browser acceptance of principal workflow chain | **PARTIAL** | Playwright covers startup, explicit unavailable state, workflow inspection, viewport map/detail provenance, fail-closed viewport reload and baseline-vs-disruption routing. | Populated derived lineage, source/agent status and reload diagnostics are not yet exercised end to end. #15. |
| Docker/Compose single-host deployment topology | **PASS** | Backend, frontend and persistent refresh services; CI validates Compose, builds both images, starts stack, checks backend/frontend/proxy and runs Playwright. | This is not a horizontally scaled/multi-tenant deployment guarantee. |
| CI quality gates and protected merge workflow | **PASS** | Ruff format/lint, strict mypy, pytest+coverage, knowledge validation, production-data guard, secret guard, OpenAPI, frontend test/build, Docker/Compose/Playwright; active `Protect main` ruleset requires `backend`, `frontend`, `containers`. | Keep ruleset/check names synchronized with workflow changes. |
| Structured API request observability | **PASS** | JSON formatter, operation ID, request error state and duration, `X-Operation-Id`; allow-listed logging fields avoid arbitrary payload context. | Broader operational observability is separate below. |
| Refresh/derivation/scenario structured observability | **PARTIAL** | Core logging primitive exists. | Systematic source-refresh, reload, derivation and scenario operation events/durations are not proven. #19. |
| Security baseline | **PARTIAL** | Non-root backend container, typed validation, custom secret guard, no current source credentials; operational docs explicitly state unauthenticated research topology. | No `SECURITY.md`, dependency vulnerability audit or complete security baseline. #18. |
| Performance/load/soak evidence | **NOT VERIFIED** | Architecture has bounded map endpoints and in-memory scaling notes only. | Establish reproducible measurements/thresholds in #17. |
| Accessibility evidence | **NOT VERIFIED** | Semantic labels/roles exist and browser tests use them. | No broad automated accessibility or keyboard-only acceptance claim. #16. |
| Documentation/reproducibility consistency | **PASS** | Primary docs, deterministic commands, source registry, architecture/evaluation/research sections and verification matrix are present; issue #11 corrected stale restart/orchestrator claims and issue #12 documents the semantic API contract. | Maintain documentation in the same feature PR when contracts/behavior change. |
| Release/version readiness | **NOT READY** | Package remains `0.1.0`; ordinary feature/governance changes correctly do not create releases. | Do not create a v1.0 release while any critical gate above is PARTIAL/NOT VERIFIED/EXTERNAL. |

## Critical open work before v1.0 can be considered

The current overall gate is **NOT READY**. After completion of the semantic API parity work in #12, the following issues remain known evidence gaps:

- #13 — complete real-agent metadata and remove direct cross-agent invocation;
- #14 — verify real Berlin road-network acquisition and resilience readiness;
- #15 — complete browser acceptance for provenance/derived/platform inspectors;
- #16 — add dashboard accessibility verification and keyboard acceptance;
- #17 — establish API/map performance and load baselines;
- #18 — establish repository/deployment security baseline;
- #19 — extend structured observability across refresh/derivation/scenario operations;
- #20 — verify reproducible real Berlin energy evaluation with real source data;
- #21 — verify multiple source-backed cross-domain workflows end to end.

These issues are intentionally separate. Passing one must not silently change another gate to PASS.

## Completion rule

A future v1.0 readiness review may set the aggregate gate to **PASS** only when:

1. every critical row is PASS or explicitly accepted as a documented non-goal for the intended v1 deployment/research scope;
2. the final candidate head passes all protected required checks (`backend`, `frontend`, `containers`);
3. relevant live/reference/energy smoke evidence is current enough for the release claim being made;
4. no known critical defect, fabricated production fallback, unresolved review finding or misleading documentation remains; and
5. release notes state scientific/operational limitations instead of implying municipal-authority or causal guarantees.

Until then, the repository may be functional and useful without being described as a completed v1.0 platform.
