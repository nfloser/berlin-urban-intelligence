# Implementation Status

## Current phase

Phase 22 — final evidence closure for the v1.0 candidate. Security (#18), structured observability (#19), reproducible real Berlin energy evidence (#20) and multiple source-backed cross-domain workflows (#21) are merged and verified. Issue #14's previously external-blocked real OSM road-network gate now has successful point-in-time live evidence on PR #35.

The only remaining completion step is procedural rather than a missing domain capability: the final PR #35 documentation head must pass the protected `backend`, `frontend` and `containers` checks, followed by the final independent review and merge.

## Current development work

PR #35 hardens only the optional road-network smoke verification infrastructure. It does not change the production road-data semantics or weaken the readiness contract.

The workflow now tries multiple real public Overpass delivery endpoints with a hard 300-second budget per endpoint. Every failed attempt is retained as JSON evidence, and the job can succeed only when the existing OSM adapter, canonical normalizer, strict road-readiness verifier and `ResilienceAgent` baseline route all succeed. No generated, cached or synthetic road topology is accepted as replacement data.

Live run `35091544852` exercised this path for `Mitte, Berlin, Germany`, network type `drive`, with explicit OSMnx speed/travel-time derivation. The first endpoint (`maps.mail.ru`) exceeded its 300-second budget and the second endpoint (`overpass.private.coffee`) also exceeded its budget. The third endpoint (`overpass-api.de`) returned a real OSM network that passed the full contract.

The accepted snapshot contained **740 canonical nodes** and **1,800 canonical edges**, retained `OpenStreetMap contributors` / ODbL 1.0 provenance, exposed OSMnx speed/travel-time imputation in provenance and recorded `synthetic_fallback=false`.

The readiness verifier then routed through the existing resilience implementation from `osm-node:10087214573` to `osm-node:13043292535` using edge `osm:10087214573:13043292535:1:1419417017` with an observed route travel time of approximately **2.139 seconds**. Artifact `10445300085` contains all endpoint attempts plus the successful readiness payload.

Protected PR run `35091630767` already passed backend, frontend and containers/Compose/Playwright on implementation head `51a6f28954ee16bb238fc33c8ad349e1cec8663c`. The current documentation commits deliberately trigger one final protected run before merge.

## Recently completed work

- Issue #21 / PR #34 completed the second source-backed cross-domain workflow and squash-merged as `e562835a1cb60b7c9cbc7b38ad9c801fef66e814`. Final protected run `35090333735` and real-energy run `35090333758` were green.
- Issue #20 / PR #33 completed reproducible real Berlin energy verification and squash-merged as `42dfb85da6f80b46c2786c0ff108ec250bac8811`. Final protected CI run `35083089572` and real-energy run `35083089585` were green. The accepted source is the clean official 2024 Stromnetz Berlin high-voltage annual curve; the five inspected 2025 files remain rejected for chronological forecasting because each contains a 96-row upstream `#BEZUG!` timestamp block.
- Issue #19 / PR #32 completed structured operation observability. Source refreshes, snapshot reloads, derivation refreshes and explicit scenario calculations expose allow-listed correlation IDs, durations and safe error-state classifications without per-record noise or raw-provider exception leakage.
- Issue #18 / PR #31 completed the repository/deployment security baseline with loopback-only default exposure, container hardening, browser security headers, exception-message redaction, vulnerability-reporting documentation and dependency-audit workflows.
- Issue #17 / PR #30 established reproducible performance/scaling evidence with a deterministic 10,000-stop/250-facility/750-node benchmark, bounded map response selection and raw latency/allocation evidence.
- Issue #16 / PR #29 completed the practical dashboard accessibility and keyboard baseline with composed Playwright/Axe acceptance.
- Issue #15 / PR #28 completed populated dashboard-inspector acceptance through the composed application stack.
- Issue #14 / PR #27 originally merged strict real-road verification/degradation infrastructure without fabricating provider success; PR #35 now supplies the missing successful live-provider evidence needed to complete that gate.
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
- Optional real road-network acquisition remains separate from deterministic CI, preserves explicit provider failure semantics and now has successful point-in-time live readiness/routing evidence.

## Evidence baselines

### Cross-domain products

`docs/evaluation/cross-domain-workflows.md` defines the current Heat + Air Quality and Mobility + Air Quality products, input/freshness/quality behavior, unavailable-input semantics and the scientific claims they explicitly do not support. `tests/test_derived_products.py` provides deterministic contract coverage, while composed Playwright acceptance proves the persisted API/dashboard inspection path.

### Real Berlin energy

`docs/energy-real-evidence.md` is authoritative for the point-in-time official-source validation, 2025 timestamp defect, clean 2024 source contract, chronological evaluation metrics, persisted/API verification and scientific limitations.

### Real Berlin road network

`docs/road-network-verification.md` is authoritative for the road-network live contract, earlier failed provider attempts and the successful 2026-09-16 run `35091544852`. The accepted graph contains 740 nodes and 1,800 edges and completed a baseline route through the real resilience implementation. This is point-in-time provider evidence, not a permanent Overpass availability guarantee.

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

The authoritative detail is in [`verification.md`](verification.md).

There is now **no unresolved critical domain/evidence gap** in the current v1.0 matrix. The previously external-blocked #14 road-network requirement is satisfied by real run `35091544852` and artifact `10445300085`, while retaining explicit failure evidence for the endpoints that timed out.

The aggregate v1.0 gate remains **NOT READY** only until the final PR #35 documentation head passes the protected required checks and the final review confirms that no critical defect, misleading evidence statement or unresolved review thread remains.

## Known external and scope constraints

- Provider availability is external to deterministic CI and is checked through separate smoke/evaluation workflows.
- OSM-backed routing remains source-dependent and must degrade explicitly when acquisition is unavailable; the successful run proves compatibility at one timestamp rather than permanent service availability.
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

Separate scoped evidence workflows additionally cover dependency security audits, live/reference providers, real Berlin energy, real Berlin road-network readiness and performance measurements.

## Next concrete tasks

1. Wait for the protected backend/frontend/container checks on the final PR #35 evidence-documentation head.
2. Perform the final independent review of PR #35, including workflow failover safety, evidence accuracy, failure visibility and documentation consistency.
3. If the final head is green and review-clean, update the aggregate verification gate to PASS, run the resulting final checks, merge PR #35 and close issue #14.
4. Only then consider a semantic v1.0 release/tag and release notes; do not create a release merely because an issue was closed.

## Important migration notes

Do not replace the existing source/agent/domain architecture. Provider acquisition remains outside request handlers. Canonical persisted state stays authoritative; RDF and bounded map GeoJSON are projections only. Cross-agent coordination belongs at composition/orchestration boundaries, while individual agents consume typed inputs and remain independently testable. Cross-domain additions must preserve independent source values/timestamps and explicit provenance rather than hiding them behind composite scores. Performance optimizations must preserve data/provenance semantics. Accessibility changes must preserve semantic native controls and equivalent non-pointer paths. Real-source adapters must reject ambiguous provider semantics rather than inventing timestamps, units or Berlin-wide interpretations.