# Implementation Status

## Current phase

Phase 20 — evidence-driven v1.0 completion. Security (#18) and structured observability (#19) are merged and verified. PR #33 / issue #20 now establishes reproducible real Berlin energy evidence. The remaining critical completion work is the cross-domain end-to-end gate (#21) plus the separately external-blocked real OSM road-network verification (#14).

## Current development work

Issue #20 / PR #33 verifies the existing leakage-safe energy pipeline against an official Berlin-scoped source rather than deterministic fixtures or an unrelated research dataset.

The source investigation inspected all five official Stromnetz Berlin 2025 annual network-level load curves. Every 2025 file contains a contiguous 96-row timestamp block whose date and time fields are literally `#BEZUG!`. The numeric values still reproduce the respective published annual maximum and rounded annual work, so the repository does not discard the publication as fabricated; however, it also does not invent chronological timestamps for those rows.

The clean official 2024 high-voltage load curve is therefore used as the reproducible chronological evidence source. It contains 35,136 quarter-hour values for the leap year, valid daylight-saving endpoint behavior, a published/observed maximum of 2,034,416 kW and published/reproduced annual work of 11,834,389,631 kWh. The strict annual parser validates source identity, publication metadata, exact annual point count, DST timing, maximum and energy integral before forecasting.

Point-in-time GitHub Actions run `35082301338` completed source acquisition, strict parsing, chronological evaluation, persisted `EnergyState`, matching dataset-fingerprint validation in `EnergyAgent` and `/api/v1/energy` exposure. It selected the ridge candidate with MAE 6,832.567799 kW and RMSE 9,488.502204 kW against a persistence baseline MAE of 19,347.097888 kW, then produced a one-step 15-minute forecast tied to dataset fingerprint `feb97ff824a8231156cf11c923e4c628988e0e865b3a74e7a79401297825bf00`.

The evidence is intentionally scoped as **historical high-voltage network load**, not total Berlin electricity consumption and not a live grid-control forecast. The current API correctly reports the resulting historical forecast as stale.

## Recently completed work

- Issue #19 / PR #32 completed structured operation observability. Source refreshes, snapshot reloads, derivation refreshes and explicit scenario calculations now expose allow-listed correlation IDs, durations and safe error-state classifications without per-record noise or raw provider exception leakage. Final protected run `35079338962` passed backend, frontend and composed browser acceptance before merge.
- Issue #18 / PR #31 completed the repository/deployment security baseline. It adds loopback-only default exposure, unprivileged/no-new-privileges containers, bounded writable paths, browser security headers, exception-message redaction, `SECURITY.md`, detailed security documentation and separate Python/frontend/browser dependency auditing. Final protected run `35078122965` and security audit run `35078123100` passed before merge.
- Issue #17 / PR #30 established reproducible performance/scaling evidence with a deterministic 10,000-stop/250-facility/750-node benchmark, bounded map response selection and raw latency/allocation evidence. The benchmark explicitly records `temporary_fixture_only=true` and `synthetic_production_fallback=false`.
- Issue #16 / PR #29 completed the dashboard accessibility and keyboard baseline. Protected CI and composed Playwright/Axe acceptance passed 8/8 cases.
- Issue #15 / PR #28 completed populated dashboard-inspector acceptance through the composed nginx → FastAPI → persisted-state → React/MapLibre path.
- Issue #14 / PR #27 merged real-road verification/degradation infrastructure without fabricating provider success. #14 remains open because captured public Overpass attempts timed out before a usable real Berlin network could be produced.
- Issues #12 and #13 completed semantic API parity plus real-agent metadata/composition boundaries.
- Issue #11 established [`verification.md`](verification.md) as the repository-wide evidence gate.

## Current architectural state

- Runtime, reference, energy and derived state are persisted separately and loaded through validated stores.
- API snapshot control hot-reloads validated replacements; invalid replacements retain last-known-good state and expose reload diagnostics.
- Six real agents expose explicit names/domains/capabilities/contracts and executable source/agent dependencies; cross-agent composition remains outside individual agents.
- Registry-driven deterministic workflows resolve unique capabilities and enforce dependency ordering.
- Derived information retains definitions, upstream lineage, provenance, freshness/quality and dependency status with incremental recomputation.
- RDF projection and bounded semantic relationship inspection use validated persisted state.
- FastAPI exposes system/source/agent/domain/reference/scenario/derived/dependency/semantic/map surfaces and resilience routing/scenario operations.
- The React/MapLibre dashboard exposes map/reference inspection, observation provenance, platform/derived inspection, deterministic workflows, heat scenarios and baseline-vs-disruption routing.
- Critical resilience routing has an equivalent coordinate-driven keyboard path over the same nearest-node and routing APIs.
- Browser acceptance runs against the composed nginx → FastAPI → persisted-state → React/MapLibre stack and includes pinned Axe accessibility scanning.
- Structured operation logging covers request, source-refresh, reload, derivation-refresh and scenario boundaries with safe low-cardinality fields.
- The security baseline and dependency-audit workflow are separate from application-domain logic.
- The real-energy evidence workflow downloads provider data only during CI and never converts the official files into a committed production fallback.
- Optional real road-network acquisition remains separate from deterministic CI and never fabricates provider success.

## Evidence baselines

### Performance

The protected correctness CI enforces stable structural properties rather than runner-dependent millisecond thresholds. The first 10,000-stop evidence run is documented in `docs/performance.md`; complete RDF graph serialization is explicitly treated as a bulk/research scaling boundary rather than a high-QPS dashboard endpoint.

### Accessibility

The automated baseline covers representative principal dashboard states and asserts no configured critical/serious Axe findings for the tested WCAG A/AA tags, visible keyboard focus, keyboard operation of analytical controls, named focusable diagnostic regions and a non-map resilience route-selection path. `docs/accessibility.md` records the manual checks and claim limitations; no formal WCAG conformance claim is made.

### Security

`SECURITY.md` and `docs/security.md` define the reporting process, single-host unauthenticated research trust boundary, container/HTTP hardening, public-deployment requirements and limitations. `.github/workflows/security.yml` audits the resolved third-party Python runtime plus frontend and isolated browser-runner dependencies.

### Observability

`docs/observability.md` defines operation event names, safe fields, correlation semantics, failure semantics and the no-per-record-noise policy. Raw provider/request payloads and raw exception messages are excluded from structured operation logs.

### Real Berlin energy

`docs/energy-real-evidence.md` is authoritative for the point-in-time official-source hash, 2025 timestamp defect, clean 2024 source contract, chronological evaluation metrics, persisted/API verification and scientific limitations.

## Repository governance state

The `Protect main` repository ruleset is active on the default branch, has no bypass actors, blocks destructive branch changes, requires pull requests/review-thread resolution and uses strict required-status-check semantics.

The three merge-critical correctness checks remain:

- `backend`
- `frontend`
- `containers`

Security, real-source, performance and other evidence workflows remain additional scoped evidence rather than weakening or replacing those protected correctness checks.

## Current v1.0 evidence gaps

The authoritative detail is in [`verification.md`](verification.md). The remaining critical gaps are:

1. #14 — **EXTERNAL/BLOCKED**: a successful real Berlin OSM network plus baseline route is still missing because the captured public Overpass attempts timed out.
2. #21 — a second defensible source-backed cross-domain workflow, including API/dashboard inspection, partial-failure behavior and browser acceptance, still needs end-to-end verification.

Issues #18, #19 and #20 are no longer completion gaps: security, structured observability and the reproducible real Berlin energy path now have explicit implementation, tests, documentation and CI/point-in-time evidence.

The overall v1.0 gate remains **NOT READY** until #21 is completed and #14 either gains successful real-provider evidence or is explicitly accepted as an external release exception for the intended scope.

## Known external and scope constraints

- Provider availability is external to deterministic CI and is checked through separate smoke/evaluation workflows.
- OSM-backed routing remains source-dependent and must degrade explicitly when acquisition is unavailable; deterministic routing fixtures are not proof of current Berlin road-network acquisition.
- The currently reproducible energy evidence is historical 2024 high-voltage network load. It is not current total Berlin demand, and the newer inspected 2025 files are not chronologically accepted while their upstream `#BEZUG!` timestamp block remains unresolved.
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

1. Complete PR #33 / #20 only after the final documentation/code head passes protected CI and the real-energy evidence workflow; independently review before merge.
2. Implement #21 as a separate branch/PR with a second scientifically defensible source-backed cross-domain workflow, deterministic missing/stale/partial-failure tests and composed browser acceptance.
3. Re-run #14 against viable real Overpass infrastructure without changing its no-synthetic-fallback contract; keep it EXTERNAL/BLOCKED if public acquisition still cannot complete.
4. Reassess the aggregate v1.0 gate only after the updated verification matrix contains no unresolved critical gap other than an explicitly accepted external release exception.

## Important migration notes

Do not replace the existing source/agent/domain architecture. Provider acquisition remains outside request handlers. Canonical persisted state stays authoritative; RDF and bounded map GeoJSON are projections only. Cross-agent coordination belongs at composition/orchestration boundaries, while individual agents consume typed inputs and remain independently testable. Performance optimizations must preserve data/provenance semantics rather than bypass validation or introduce silent caches with stale state. Accessibility changes must preserve semantic native controls and equivalent non-pointer paths rather than hiding interaction in test-specific behavior. Real-source adapters must reject ambiguous provider semantics rather than inventing timestamps, units or Berlin-wide interpretations.
