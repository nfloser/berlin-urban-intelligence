# Implementation Status

## Current phase

Phase 17 — evidence-driven v1.0 completion work, with performance/scaling verification now implemented and the remaining security, observability and real-data/cross-domain gates tracked independently.

## Current development work

Issue #17 / PR #30 establishes the repository performance and scaling baseline. The work began with RED performance-contract tests, then added a reusable latency/allocation measurement harness, deterministic benchmark-only persisted state, a separate scheduled/manual GitHub Actions workflow and explicit scaling documentation.

The map viewport projector was also tightened so it no longer materializes every spatial match before applying `limit_per_layer`; it scans the canonical sequences for accurate match counts while retaining only the bounded response selection. Existing total/matched/returned/truncated semantics are preserved.

The first successful benchmark evidence is GitHub Actions run `35004770633`. On its Ubuntu 24.04 Azure runner with Python 3.12.14 and 4 reported logical CPUs, a temporary 4,695,269-byte fixture containing 10,000 transport stops, 250 facilities, 750 nodes and 749 edges recorded p95 observations of 0.018 ms for unchanged snapshot checks, 3.552 ms for `/api/v1/system`, 8.266 ms for agent health, 193.779 ms for the bounded two-layer map viewport, 3.709 ms for canonical detail, 13.712 ms for nearest-node lookup, 40.503 ms for baseline routing and 14,947.922 ms for complete semantic graph serialization. These are point-in-time engineering observations, not production SLOs; the graph result explicitly documents the bulk-export scaling boundary.

`docs/performance.md` records methodology, fixture/environment metadata, raw-operation measurements, stable regression invariants and deployment assumptions. The benchmark uses only temporary deterministic state and explicitly records `synthetic_production_fallback=false`.

Issue #14 remains separately **EXTERNAL/BLOCKED**. Its repository verification/degradation infrastructure is merged on `main`, but the captured public Overpass attempts on 2026-09-15 timed out before a real Berlin network could be produced. A real non-empty network plus baseline route is still required before #14 can close.

## Recently completed work

- Issue #16 / PR #29 completed the dashboard accessibility and keyboard baseline. Final implementation head `419e8a90c5c1c59d32a42cc8670cafa5bfcee0b4` passed GitHub Actions run `34994941517`: `backend`, `frontend` and `containers` were successful and the composed Playwright/Axe suite passed 8/8 cases. The PR was independently reviewed and squash-merged as `e47bdbcc5d51f596e1b20bb209df04e32c038f04`.
- Issue #15 / PR #28 completed populated dashboard-inspector acceptance. Persisted acceptance-only runtime/reference/derived state verifies derived lineage/provenance/freshness, source status/error semantics, agent health/capabilities/dependencies and snapshot reload diagnostics through nginx → FastAPI → React/MapLibre. It also fixed installed deployment source-registry resolution through `BUI_SOURCE_REGISTRY`.
- Issue #14 / PR #27 merged real-road verification/degradation infrastructure without fabricating provider success. A dedicated road-network smoke path, strict canonical OSM readiness validation, opt-in provenance-visible routing imputation, real baseline-route verification contract and last-known-good failure semantics are on `main`; #14 remains open because live Overpass acquisition is externally blocked.
- Issue #13 / PR #26 completed real-agent metadata and composition boundaries. All six real agents expose explicit metadata; `AgentRegistry` owns capability resolution; Live State aggregates typed `AgentHealth` values supplied by the API composition boundary rather than invoking domain agents.
- Issue #12 / PR #23 closed semantic API parity: public graph serialization includes persisted derived lineage and the API exposes bounded typed incoming/outgoing semantic relationship inspection.
- Issue #11 / PR #22 established `docs/verification.md` as the repository-wide completion evidence matrix and corrected orchestration/snapshot documentation drift.
- Issue #5 / PR #10 established the protected repository workflow. `Protect main` is active, has no bypass actors, requires pull requests/review-thread resolution and strictly requires GitHub Actions checks `backend`, `frontend` and `containers`.

## Current architectural state

- Runtime, reference, energy and derived state are persisted separately and loaded through validated stores.
- API snapshot control hot-reloads validated runtime/reference/energy/derived replacements; invalid replacements retain last-known-good state and expose reload diagnostics.
- Unchanged snapshot request checks use file identity and do not reparse persisted JSON.
- Source registry loading supports the explicit `BUI_SOURCE_REGISTRY` deployment path used by Compose.
- Six real agents expose explicit names/domains/capabilities/contracts and executable source/agent dependencies. Cross-agent composition remains outside individual agents.
- Registry-driven deterministic workflows resolve unique capabilities and enforce dependency ordering.
- Derived information retains definitions, upstream lineage, provenance, freshness/quality and dependency status with incremental recomputation.
- RDF projection and bounded semantic relationship inspection use validated persisted state.
- FastAPI exposes system/source/agent/domain/reference/scenario/derived/dependency/semantic/map surfaces and resilience routing/scenario operations.
- Reference-map rendering uses a bounded viewport projection plus full canonical-detail fetch on selection; temporary selected-object retention is also bounded by `limit_per_layer`.
- The React/MapLibre dashboard exposes map/reference inspection, observation provenance, platform/derived inspection, deterministic workflows, heat scenarios and baseline-vs-disruption routing.
- Critical resilience routing has an equivalent coordinate-driven keyboard path over the same nearest-node and routing APIs.
- Browser acceptance runs against the composed nginx → FastAPI → persisted-state → React/MapLibre stack and includes pinned Axe accessibility scanning.
- A separate deterministic performance workflow records point-in-time latency/allocation evidence without turning noisy hosted-runner timings into protected SLO thresholds.
- Optional real road-network acquisition remains separate from deterministic CI and never fabricates provider success.

## Performance/scaling baseline

The protected correctness CI enforces stable structural properties rather than runner-dependent millisecond thresholds. In particular:

- unchanged snapshots are not reparsed;
- API pagination and map limits are explicit;
- map response selection is bounded per layer while accurate match counts are retained; and
- benchmark fixtures never become a production fallback.

The first 10,000-stop benchmark shows that normal dashboard-oriented API paths remain far lighter than complete RDF graph export. `docs/performance.md` is authoritative for methodology, exact values and interpretation limits. Current architecture remains a single-host research topology; persistent spatial indexes, semantic stores/caches and coordinated multi-process snapshot invalidation are future scaling mechanisms if actual deployment demand requires them.

## Accessibility baseline

The current automated baseline covers representative principal dashboard states and asserts no configured critical/serious Axe findings for the tested WCAG A/AA tags, visible keyboard focus, keyboard operation of analytical controls, named focusable diagnostic regions and a non-map resilience route-selection path.

The MapLibre canvas remains primarily visual for arbitrary feature exploration. `docs/accessibility.md` documents this limitation plus the manual keyboard, focus, zoom/reflow and screen-reader checklist. No formal WCAG conformance claim is made.

## Repository governance state

The `Protect main` repository ruleset is active on the default branch, has no bypass actors, blocks destructive branch changes, requires pull requests and review-thread resolution and uses strict required-status-check semantics.

The three merge-critical GitHub Actions checks remain:

- `backend`
- `frontend`
- `containers`

The performance workflow is deliberately additional evidence, not a fourth brittle timing gate.

## Current v1.0 evidence gaps

The authoritative detail is in [`verification.md`](verification.md). After the accessibility and performance work, the remaining concrete gaps are:

1. #14 — **EXTERNAL/BLOCKED**: a successful real Berlin OSM network plus baseline route is still missing because captured public Overpass attempts timed out.
2. #18 — establish the repository/deployment security baseline.
3. #19 — extend structured observability across refresh, reload, derivation and scenario operations.
4. #20 — verify a reproducible real Berlin energy evaluation/forecast artefact.
5. #21 — verify multiple source-backed cross-domain workflows end to end.

The overall v1.0 gate remains **NOT READY** until those critical rows are resolved or explicitly accepted as non-goals for the intended release scope.

## Known external and scope constraints

- Provider availability is external to deterministic CI and is checked through separate smoke/evaluation workflows.
- OSM-backed routing remains source-dependent and must degrade explicitly when acquisition is unavailable; deterministic routing fixtures are not proof of current Berlin road-network acquisition.
- Real Berlin energy evidence depends on an accessible, semantically appropriate source publication; external unavailability must remain explicit rather than being replaced with synthetic data.
- Automated accessibility tooling cannot prove full assistive-technology usability or formal standards conformance.
- GitHub-hosted runner benchmark timings are not production capacity guarantees.
- Complete RDF serialization is a bulk/research operation in the current in-memory topology, not a high-QPS dashboard endpoint.

## Verification commands enforced by protected CI

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
Axe critical/serious WCAG A/AA regression scan in principal dashboard states
```

Separate performance evidence runs `scripts/benchmark_performance.py` through `.github/workflows/performance.yml` and uploads the raw JSON report.

## Next concrete tasks

1. Complete PR #30 only after its final head passes protected CI and the performance workflow; close #17 through that verified merge.
2. Keep #14 open as EXTERNAL/BLOCKED until a real provider run can honestly satisfy the road-readiness acceptance contract.
3. Address #18 and #19 as independent security and observability PRs.
4. Verify #20 using a real Berlin energy artifact without substituting unrelated data.
5. Complete #21 only with a second defensible populated cross-domain workflow and end-to-end evidence.
6. Reassess v1.0 only when `docs/verification.md` contains no unresolved critical gap other than any explicitly accepted external release exception.

## Important migration notes

Do not replace the existing source/agent/domain architecture. Provider acquisition remains outside request handlers. Canonical persisted state stays authoritative; RDF and bounded map GeoJSON are projections only. Cross-agent coordination belongs at composition/orchestration boundaries, while individual agents consume typed inputs and remain independently testable. Performance optimizations must preserve data/provenance semantics rather than bypass validation or introduce silent caches with stale state. Accessibility changes must preserve semantic native controls and equivalent non-pointer paths rather than hiding interaction in test-specific behavior.
