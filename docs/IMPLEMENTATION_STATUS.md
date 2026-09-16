# Implementation Status

## Current phase

Phase 23 — **v1.0.0 release candidate**.

The repository-wide v1 evidence closure is complete. Security (#18), structured observability (#19), reproducible real Berlin energy evidence (#20), multiple source-backed cross-domain workflows (#21) and real Berlin road-network readiness (#14) are verified against the documented acceptance contracts.

The aggregate v1.0 evidence gate is **PASS**. PR #35 was squash-merged to `main` as `bc3c63521895be019b91e322b679f62e0f34be5f` after final protected backend/frontend/container CI and independent real-energy evidence passed. Issue #14 is closed with the successful live OSM evidence and retained failed-provider attempts.

Issue #36 / PR #37 now prepares the first stable Semantic Versioning release. The release work is intentionally separated from feature/evidence closure: version metadata, public release documentation and the eventual GitHub tag/release are reviewed and verified on a dedicated `release/1.0.0` branch before any tag is created.

## Current release work

PR #37 introduces a permanent stable-release metadata contract and prepares version `1.0.0`.

TDD evidence for the release contract is explicit:

- the initial test-only CI exposed repository-style issues that were corrected without changing release metadata;
- run `35094619615` then passed Ruff and strict mypy and reached the intended RED state in Pytest: **145 existing tests passed and exactly one new release-metadata test failed** because the repository still declared major version `0`;
- implementation then updated `VERSION`, `pyproject.toml`, public README release claims, changelog and versioned release notes;
- the remaining central documentation is being aligned before the final protected release-candidate run.

The release metadata regression test requires the stable version to be consistent across `VERSION`, Python project metadata and README, verifies the MIT licence disclosure, requires a dated changelog entry and requires versioned release notes with explicit limitations.

No release tag is created from the branch head. `v1.0.0` will be published only from the reviewed, CI-verified merged release commit.

## Verified v1 evidence baseline

### Protected application CI

PR #35 final head `342d57c71886ac65686c8dcd35d8553b4507a962` passed protected CI run `35093468008`:

- `backend` — PASS;
- `frontend` — PASS;
- `containers` — PASS, including Docker/Compose and the nginx → FastAPI → persisted state → React/Playwright path.

### Real Berlin energy

Independent run `35093467950` passed the official-source probes and the real 2024 evaluation, persistence, Energy Agent and API exposure path.

`docs/energy-real-evidence.md` remains authoritative for source semantics and measured results. The accepted reproducible source is the clean official 2024 Stromnetz Berlin high-voltage annual curve. The inspected 2025 publications with a 96-row upstream `#BEZUG!` timestamp block remain deliberately rejected rather than silently repaired.

### Real Berlin road network

Live run `35091544852` exercised the strict road-network path for `Mitte, Berlin, Germany`, network type `drive`, with explicit OSMnx speed/travel-time derivation.

Two public Overpass endpoints exceeded the configured attempt budget and their failure evidence was retained. `https://overpass-api.de/api` then returned a real graph that passed the readiness contract:

- 740 canonical nodes;
- 1,800 canonical edges;
- `OpenStreetMap contributors` / ODbL 1.0 provenance;
- provenance-visible speed/travel-time imputation;
- `synthetic_fallback=false`.

The existing `ResilienceAgent` completed the baseline route `osm-node:10087214573` → `osm-node:13043292535` at approximately **2.139 seconds**. Evidence artifact `10445300085` has SHA-256 `8672bb1325b80c76d54a5722d78cbc7135ad3d9626432796e1e1bb8b20e1595c`.

This is point-in-time provider compatibility/readiness evidence, not a guarantee of permanent public Overpass availability.

## Current architectural state

- Runtime, reference, energy and derived state are persisted separately and loaded through validated stores.
- Snapshot control hot-reloads validated replacements; invalid replacements retain last-known-good state and expose diagnostics.
- Six real agents expose explicit domains, capabilities, contracts, dependencies and health.
- Cross-agent coordination remains at registry/orchestration/composition boundaries rather than hidden inside domain agents.
- Registry-driven deterministic workflows resolve capabilities and enforce dependency ordering without requiring an LLM.
- Derived information retains definitions, upstream lineage, provenance, producer/algorithm version, freshness/quality and dependency status with incremental recomputation.
- Source-backed cross-domain products are omitted when required inputs are absent; no synthetic replacement score is generated.
- RDF projection and bounded semantic relationship inspection use validated persisted state.
- FastAPI exposes system/source/agent/domain/reference/scenario/derived/dependency/semantic/map and resilience surfaces.
- The React/MapLibre dashboard exposes reference/provenance inspection, platform/derived inspection, deterministic workflows, explicit cross-domain interpretation, scenarios and baseline-versus-disruption routing.
- Critical resilience routing has an equivalent coordinate-driven keyboard path over the same routing APIs.
- Browser acceptance runs against the composed application stack and includes pinned Axe accessibility scanning for representative states.
- Structured observability covers request, source-refresh, reload, derivation-refresh and scenario boundaries with safe low-cardinality fields.
- Security and dependency-audit workflows remain separate from application-domain logic.
- Real-source evidence workflows download provider data during the run and do not convert those publications into committed production fallbacks.

## Repository governance state

The `Protect main` ruleset is active on the default branch, has no bypass actors, blocks destructive branch changes, requires pull-request/review-thread resolution and uses strict required-status-check semantics.

The three merge-critical correctness checks remain:

- `backend`
- `frontend`
- `containers`

Security, real-source, performance and other evidence workflows are additional scoped evidence; they do not weaken or replace protected correctness checks.

## v1.0.0 release contract

The release candidate must satisfy all of the following before merge/tagging:

- `VERSION`, `pyproject.toml` and README all declare `1.0.0`;
- README states the MIT project-source licence and separates external dataset terms;
- `CHANGELOG.md` contains a dated `1.0.0` entry;
- `docs/releases/v1.0.0.md` records capabilities, verification evidence, operating notes and limitations;
- central docs do not retain stale `0.1.0`, `NOT READY` or pre-merge PR #35 status claims;
- protected backend/frontend/container checks pass on the final release-candidate head;
- review finds no unresolved correctness, documentation, compatibility, security or release-process findings;
- the release PR is squash-merged before the `v1.0.0` tag/GitHub release is created;
- the published release must point to the verified merged commit and use the reviewed versioned release notes.

## Known external and scope constraints

- Public-provider availability is external to deterministic CI and can regress after release.
- OSM-backed routing must degrade explicitly when acquisition is unavailable; no generated production topology substitutes for a provider failure.
- Cross-domain contexts are descriptive co-reporting only and do not establish causality, correlation or exposure.
- Current reproducible energy evidence is historical 2024 high-voltage network load, not current total Berlin demand.
- Automated accessibility tooling does not prove full assistive-technology usability or formal WCAG conformance.
- GitHub-hosted benchmark timings are not production-capacity guarantees.
- Complete RDF serialization is a bulk/research operation in the current in-memory topology, not a high-QPS production endpoint.
- Municipal operational authority, safety-critical use, authenticated multi-tenant deployment and distributed/federated runtime operation are outside the v1.0.0 claim boundary.

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
Axe critical/serious configured WCAG A/AA regression scan in principal dashboard states
```

Separate scoped workflows cover dependency security audits, live/reference providers, real Berlin energy, real Berlin road-network readiness and performance measurements.

## Next concrete tasks

1. Complete the v1.0.0 release-documentation alignment on PR #37.
2. Run the complete protected CI on the final release-candidate head.
3. Perform an independent PR review, correct any findings and re-run affected checks.
4. Mark PR #37 review-ready and squash-merge only when the final head is green and review-clean.
5. Publish GitHub release/tag `v1.0.0` from the verified merged commit using the reviewed `docs/releases/v1.0.0.md` content.
6. Verify the published release target, release notes and issue #36 closure evidence.

## Important migration notes

Do not replace the existing source/agent/domain architecture. Provider acquisition remains outside request handlers. Canonical persisted state stays authoritative; RDF and bounded map GeoJSON are projections only. Cross-agent coordination belongs at composition/orchestration boundaries, while individual agents consume typed inputs and remain independently testable. Cross-domain additions must preserve independent source values/timestamps and explicit provenance rather than hiding them behind composite scores. Performance optimizations must preserve data/provenance semantics. Accessibility changes must preserve semantic native controls and equivalent non-pointer paths. Real-source adapters must reject ambiguous provider semantics rather than inventing timestamps, units or Berlin-wide interpretations.