# Implementation Status

## Current phase

Phase 16 — evidence-driven v1.0 completion work, with independently scoped quality and real-data verification gates.

## Current development work

Issue #16 / PR #29 establishes the dashboard accessibility and keyboard baseline identified by the v1.0 audit. The implementation adds automated Axe scanning to the isolated Playwright acceptance runner, visible `:focus-visible` treatment, named keyboard-focusable source/agent scroll regions, and a dedicated non-pointer resilience-routing path that resolves typed coordinates through the existing nearest-node API before using the same baseline/disruption route APIs as map-selected routing.

The RED browser run first reproduced two concrete defects while all six existing browser scenarios remained green: Axe reported `scrollable-region-focusable` for the source/agent diagnostic lists, and the visible-focus assertion found `outline: none` on form controls. Implementation head `33f9a6b58c5ec0c87f53a30fe6e7d03456172fba` then passed GitHub Actions run `34993932956`: `backend`, `frontend`, and `containers` were all successful and Playwright reported **8/8 passed**, including Axe checks and keyboard-only routing.

`docs/accessibility.md` records the manual keyboard/focus/zoom/reflow/screen-reader checklist and explicitly states that this baseline is not a formal WCAG conformance certification. The final documentation head still requires the normal protected `backend`, `frontend`, and `containers` checks before PR #29 may merge.

Issue #14 remains separately **EXTERNAL/BLOCKED**. Its repository verification/degradation infrastructure is merged on `main`, but the two captured public Overpass attempts on 2026-09-15 timed out before a real Berlin network could be produced: run `34979600413` hit a 180-second `ConnectTimeout` at `overpass-api.de`; run `34980820676` hit a 180-second `ReadTimeout` at `https://overpass.private.coffee/api`. Both failure artifacts recorded `synthetic_fallback=false`. A real non-empty network plus baseline route is still required before #14 can close.

## Recently completed work

- Issue #15 / PR #28 completed populated dashboard-inspector acceptance. Persisted acceptance-only runtime/reference/derived state now verifies derived lineage/provenance/freshness, source status/error semantics, agent health/capabilities/dependencies and snapshot reload diagnostics through nginx → FastAPI → React/MapLibre. It also fixed installed deployment source-registry resolution through `BUI_SOURCE_REGISTRY`. Pre-merge and post-merge CI passed all protected checks with 6/6 Playwright cases.
- Issue #14 / PR #27 merged the real-road verification/degradation infrastructure without fabricating provider success. A dedicated road-network smoke path, strict canonical OSM readiness validation, opt-in provenance-visible routing imputation, real baseline-route verification contract and last-known-good failure semantics are on `main`; #14 remains open because live Overpass acquisition is externally blocked.
- Issue #13 / PR #26 completed real-agent metadata and composition boundaries. All six real agents expose explicit metadata; `AgentRegistry` owns capability resolution; Live State aggregates typed `AgentHealth` values supplied by the API composition boundary rather than invoking domain agents.
- Issue #12 / PR #23 closed semantic API parity: public graph serialization includes persisted derived lineage and the API exposes bounded typed incoming/outgoing semantic relationship inspection.
- Issue #11 / PR #22 established `docs/verification.md` as the repository-wide completion evidence matrix and corrected orchestration/snapshot documentation drift.
- Issue #5 / PR #10 established the protected repository workflow. `Protect main` is active, has no bypass actors, requires pull requests/review-thread resolution and strictly requires GitHub Actions checks `backend`, `frontend`, and `containers`.

## Current architectural state

- Runtime, reference, energy and derived state are persisted separately and loaded through validated stores.
- API snapshot control hot-reloads validated runtime/reference/energy/derived replacements; invalid replacements retain last-known-good state and expose reload diagnostics.
- Source registry loading supports the explicit `BUI_SOURCE_REGISTRY` deployment path; Compose uses `/app/config/sources.yaml`.
- Six real agents expose explicit names/domains/capabilities/contracts and executable source/agent dependencies. Cross-agent composition remains outside individual agents.
- Registry-driven deterministic workflows resolve unique capabilities and enforce dependency ordering.
- Derived information retains definitions, upstream lineage, provenance, freshness/quality and dependency status with incremental recomputation.
- RDF projection and bounded semantic relationship inspection use the same validated runtime/reference/energy/derived state.
- FastAPI exposes system/source/agent/domain/reference/scenario/derived/dependency/semantic/map surfaces and resilience routing/scenario operations.
- Reference-map rendering uses a bounded viewport projection plus full canonical-detail fetch on selection.
- The React/MapLibre dashboard exposes map/reference inspection, observation provenance, platform/derived inspection, deterministic workflows, heat scenarios and baseline-vs-disruption routing.
- Critical resilience routing no longer requires pointer map selection: an equivalent coordinate-driven keyboard panel resolves nearest persisted network nodes and calls the same routing APIs.
- Browser acceptance runs against the composed nginx → FastAPI → persisted-state → React/MapLibre stack. The acceptance runner now includes pinned Axe accessibility scanning in addition to the existing behavioral tests.
- Optional real road-network acquisition remains separate from deterministic CI and never fabricates a provider success.

## Accessibility baseline

The current automated baseline covers representative principal dashboard states and asserts:

- no Axe `critical`/`serious` violations for the configured WCAG A/AA tags in the tested states;
- visible keyboard focus;
- keyboard operation of workflow execution, layer toggles, scenario controls and derived selection;
- keyboard-focusable named diagnostic scroll regions; and
- a non-map resilience route-selection path.

The MapLibre canvas remains primarily visual for arbitrary feature exploration. `docs/accessibility.md` documents this limitation plus the manual keyboard, focus, zoom/reflow and screen-reader checklist. No formal WCAG conformance claim is made.

## Repository governance state

The `Protect main` repository ruleset is **Active** and targets the default branch. It has no bypass actors, blocks branch deletion and force/non-fast-forward pushes, requires pull requests and review-thread resolution, and uses strict required-status-check semantics.

The three merge-critical GitHub Actions checks are:

- `backend`
- `frontend`
- `containers`

All three are bound to the GitHub Actions integration.

## Current v1.0 evidence gaps

The authoritative detail is in [`verification.md`](verification.md). After the #16 accessibility baseline, the remaining concrete gaps are:

1. #14 — **EXTERNAL/BLOCKED**: a successful real Berlin OSM network plus baseline route is still missing because both captured public Overpass attempts timed out.
2. #17 — establish API/map performance and load evidence.
3. #18 — establish repository/deployment security baseline.
4. #19 — extend structured observability across refresh/derivation/scenario operations.
5. #20 — verify a reproducible real Berlin energy evaluation/forecast artefact.
6. #21 — verify multiple source-backed cross-domain workflows end to end.

The overall v1.0 gate remains **NOT READY** until those critical rows are resolved or explicitly accepted as non-goals for the intended release scope.

## Known external constraints

- Current provider availability remains external to deterministic CI and is checked through separate smoke/evaluation workflows.
- OSM-backed routing remains source-dependent and must degrade explicitly when acquisition is unavailable; deterministic routing fixtures are not proof of current Berlin road-network acquisition.
- Real Berlin energy evidence depends on an accessible, semantically appropriate Stromnetz Berlin publication; external unavailability must remain explicit rather than being replaced with synthetic data.
- Automated accessibility tooling cannot prove full assistive-technology usability or formal standards conformance; manual review remains required for release-level claims.

## Completed reliability milestones

- Persisted snapshots hot-reload into a running API while invalid replacements preserve last-known-good state.
- Browser-level acceptance uses explicit acceptance-only persisted fixtures rather than a production synthetic fallback.
- Populated derived provenance/lineage, source health/error semantics, agent capabilities/dependencies/health and reload diagnostics are verified through the composed browser stack.
- Baseline and hypothetical route results remain distinct and are compared end to end.
- Bounded viewport map loading reports totals/matches/returned/truncation rather than implying completeness.
- Public semantic graph serialization and relationship inspection include persisted derived lineage.
- Real-agent dependency/capability metadata is executable registry data, while composition remains outside individual agents.
- Real OSM verification has a dedicated smoke path with explicit failure evidence and no synthetic production fallback.
- Installed Docker deployments resolve configured resources through explicit deployment paths.
- `main` is protected by required PR/CI rules.
- The dashboard now has an automated high-impact accessibility regression gate, visible keyboard focus and an equivalent non-pointer routing path.

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
Axe critical/serious WCAG A/AA regression scan in principal dashboard states
```

Passing only a subset is not treated as proof that a PR is merge-ready.

## Next concrete tasks

1. Merge PR #29 only after its final documentation head passes all three protected checks; close #16 through that verified merge.
2. Keep #14 open as EXTERNAL/BLOCKED and rerun its live road smoke later when a public provider is responsive.
3. Address #17–#19 as independent performance, security and observability PRs.
4. Verify the real Berlin energy gate #20 independently of deterministic model tests.
5. Complete #21 only after its dependent source/data evidence is sufficient.
6. Reassess v1.0 only when `docs/verification.md` contains no unresolved critical gap.

## Important migration notes

Do not replace the existing source/agent/domain architecture. Provider acquisition remains outside request handlers. Canonical persisted state stays authoritative; RDF and bounded map GeoJSON are projections only. Cross-agent coordination belongs at composition/orchestration boundaries, while individual agents consume typed inputs and remain independently testable. Accessibility changes must preserve semantic native controls and equivalent non-pointer paths rather than hiding interaction in test-specific behavior.
