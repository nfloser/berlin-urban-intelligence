# Implementation Status

## Current phase

Phase 21 — evidence-driven v1.0 completion. Security (#18), structured observability (#19) and reproducible real Berlin energy evidence (#20) are merged and verified. PR #34 / issue #21 verifies two source-backed descriptive cross-domain workflows end to end. After this candidate is merged, the only remaining critical release-level evidence gap is the separately external-blocked real OSM road-network verification (#14).

## Current development work

Issue #21 / PR #34 extends the existing derived-information path without adding a universal score, hidden weighting or unsupported causal inference.

The first workflow, `heat-air-quality-context-v1`, retains the latest persisted DWD 2 m air-temperature observation and Berlin LQI observation as separate values with separate entity identifiers and observation timestamps. The second workflow, `mobility-air-quality-context-v1`, co-reports the VBB GTFS-Realtime delayed trip-update share and latest Berlin LQI observation, again preserving the numerator/denominator, independent timestamps, source semantics and provenance.

The second workflow was developed test-first. RED run `35083736052` passed format, lint and strict mypy, then failed exactly three new Pytest contracts because `mobility-air-quality-context-v1` did not yet exist. The implementation now provides the requested definition/record, quality/freshness propagation, last-known-good source-unavailable semantics and missing-input omission without synthetic replacement values.

The dashboard Derived Information inspector now exposes each derivation definition's scientific interpretation next to producer/algorithm version, inputs, lineage and provenance. Deterministic browser-acceptance fixtures persist both cross-domain records through the normal `DerivedStateStore`; Playwright switches between both results and verifies their input lineage and explicit non-causal/no-score caveats through the composed nginx → FastAPI → persisted-state → React path.

`docs/evaluation/cross-domain-workflows.md` is authoritative for the scientific interpretation boundaries. These products are descriptive context only. They do not establish correlation or causality, estimate passenger/person exposure, spatially co-locate observations that originate from different source footprints, or calculate a combined city/risk score.

## Recently completed work

- Issue #20 / PR #33 completed reproducible real Berlin energy verification and squash-merged as `42dfb85da6f80b46c2786c0ff108ec250bac8811`. Final protected CI run `35083089572` and real-energy run `35083089585` were green. The accepted source is the clean official 2024 Stromnetz Berlin high-voltage annual curve; the five inspected 2025 files remain rejected for chronological forecasting because each contains a 96-row upstream `#BEZUG!` timestamp block.
- Issue #19 / PR #32 completed structured operation observability. Source refreshes, snapshot reloads, derivation refreshes and explicit scenario calculations expose allow-listed correlation IDs, durations and safe error-state classifications without per-record noise or raw-provider exception leakage.
- Issue #18 / PR #31 completed the repository/deployment security baseline with loopback-only default exposure, container hardening, browser security headers, exception-message redaction, vulnerability-reporting documentation and dependency-audit workflows.
- Issue #17 / PR #30 established reproducible performance/scaling evidence with a deterministic 10,000-stop/250-facility/750-node benchmark, bounded map response selection and raw latency/allocation evidence.
- Issue #16 / PR #29 completed the practical dashboard accessibility and keyboard baseline with composed Playwright/Axe acceptance.
- Issue #15 / PR #28 completed populated dashboard-inspector acceptance through the composed application stack.
- Issue #14 / PR #27 merged real-road verification/degradation infrastructure without fabricating provider success. #14 remains open because captured public Overpass attempts timed out before a usable real Berlin network could be produced.
- Issues #12 and #13 completed semantic API parity plus real-agent metadata/composition boundaries; issue #11 established [`verification.md`](verification.md) as the repository-wide evidence gate.

## Current architectural state

- Runtime, reference, energy and derived state are persisted separately and loaded through validated stores.
- API snapshot control hot-reloads validated replacements; invalid replacements retain last-known-good state and expose reload diagnostics.
- Six real agents expose explicit names/domains/capabilities/contracts and executable source/agent dependencies; cross-agent composition remains outside individual agents.
- Registry-driven deterministic workflows resolve unique capabilities and enforce dependency ordering.
- Derived information retains definitions, upstream lineage, provenance, freshness/quality and dependency status with incremental recomputation.
- Source-backed derived products are omitted when required inputs are absent; current source failure is propagated through freshness rather than hidden by fabricated replacement state.
- RDF projection and bounded semantic relationship inspection use validated persisted state.
- FastAPI exposes system/source/agent/domain/reference/scenario/derived/dependency/semantic/map surfaces and resilience routing/scenario operations.
- The React/MapLibre dashboard exposes map/reference inspection, observation provenance, platform/derived inspection, deterministic workflows, explicit derivation interpretation, heat scenarios and baseline-vs-disruption routing.
- Critical resilience routing has an equivalent coordinate-driven keyboard path over the same nearest-node and routing APIs.
- Browser acceptance runs against the composed nginx → FastAPI → persisted-state → React/MapLibre stack and includes pinned Axe accessibility scanning.
- Structured operation logging covers request, source-refresh, reload, derivation-refresh and scenario boundaries with safe low-cardinality fields.
- The security baseline and dependency-audit workflow are separate from application-domain logic.
- The real-energy evidence workflow downloads provider data only during CI and never converts official files into a committed production fallback.
- Optional real road-network acquisition remains separate from deterministic CI and never fabricates provider success.

## Evidence baselines

### Cross-domain products

`docs/evaluation/cross-domain-workflows.md` defines the current Heat + Air Quality and Mobility + Air Quality products, input/freshness/quality behavior, unavailable-input semantics and the scientific claims they explicitly do not support. `tests/test_derived_products.py` provides deterministic contract coverage, while composed Playwright acceptance proves the persisted API/dashboard inspection path.

### Real Berlin energy

`docs/energy-real-evidence.md` is authoritative for the point-in-time official-source validation, 2025 timestamp defect, clean 2024 source contract, chronological evaluation metrics, persisted/API verification and scientific limitations.

### Performance

Protected correctness CI enforces stable structural properties rather than runner-dependent millisecond thresholds. The 10,000-stop evidence run is documented in `docs/performance.md`; complete RDF graph serialization remains a bulk/research scaling boundary rather than a high-QPS dashboard endpoint.

### Accessibility

The automated baseline covers representative principal dashboard states and asserts no configured critical/serious Axe findings for the tested WCAG A/AA tags, visible keyboard focus, keyboard operation of analytical controls, named focusable diagnostic regions and a non-map resilience route-selection path. No formal WCAG conformance claim is made.

### Security and observability

`SECURITY.md` and `docs/security.md` define the current single-host research trust boundary. `docs/observability.md` defines operation event names, safe fields, correlation/failure semantics and the no-per-record-noise policy.

## Repository governance state

The `Protect main` repository ruleset is active on the default branch, has no bypass actors, blocks destructive branch changes, requires pull requests/review-thread resolution and uses strict required-status-check semantics.

The three merge-critical correctness checks remain:

- `backend`
- `frontend`
- `containers`

Security, real-source, performance and other evidence workflows remain additional scoped evidence rather than weakening or replacing those protected correctness checks.

## Current v1.0 evidence gaps

The authoritative detail is in [`verification.md`](verification.md). On the PR #34 candidate, the #21 cross-domain gate is satisfied by two explicit source-backed descriptive products, deterministic normal/missing/unavailable behavior, persisted API/dashboard inspection and composed browser acceptance.

The remaining critical release-level evidence gap is:

1. #14 — **EXTERNAL/BLOCKED**: a successful real Berlin OSM network plus baseline route is still missing because captured public Overpass attempts timed out.

The overall v1.0 gate therefore remains **NOT READY** unless #14 obtains successful real-provider evidence or the dependency is explicitly accepted as an external release exception for the intended v1 research scope.

## Known external and scope constraints

- Provider availability is external to deterministic CI and is checked through separate smoke/evaluation workflows.
- OSM-backed routing remains source-dependent and must degrade explicitly when acquisition is unavailable; deterministic routing fixtures are not proof of current Berlin road-network acquisition.
- Cross-domain contexts are descriptive co-reporting only; different source timestamps and spatial footprints remain visible and are not interpreted as causal, correlated or co-located evidence.
- The currently reproducible energy evidence is historical 2024 high-voltage network load, not current total Berlin demand.
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

Separate scoped evidence workflows additionally cover dependency security audits, live/reference providers, real Berlin energy and performance measurements.

## Next concrete tasks

1. Complete PR #34 only after its final code/documentation head passes protected backend/frontend/container CI and composed browser acceptance, then independently review and merge it to close #21.
2. Re-run #14 against viable real Overpass infrastructure without changing its strict no-synthetic-fallback/readiness contract.
3. If #14 succeeds, verify the produced real Berlin nodes/edges and a real baseline route before changing its evidence gate; if it still fails externally, preserve the blocked status and failure evidence.
4. Reassess v1.0 release readiness only after the final verification matrix contains no unresolved critical gap other than an explicitly accepted external release exception.

## Important migration notes

Do not replace the existing source/agent/domain architecture. Provider acquisition remains outside request handlers. Canonical persisted state stays authoritative; RDF and bounded map GeoJSON are projections only. Cross-agent coordination belongs at composition/orchestration boundaries, while individual agents consume typed inputs and remain independently testable. Cross-domain additions must preserve independent source values/timestamps and explicit provenance rather than hiding them behind composite scores. Performance optimizations must preserve data/provenance semantics. Accessibility changes must preserve semantic native controls and equivalent non-pointer paths. Real-source adapters must reject ambiguous provider semantics rather than inventing timestamps, units or Berlin-wide interpretations.
