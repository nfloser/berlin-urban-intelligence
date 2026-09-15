# Performance and scaling baseline

Berlin Urban Intelligence is currently a research-oriented single-host application, not a horizontally scaled municipal production service. Performance evidence is therefore recorded as reproducible engineering observations with explicit fixture and hardware context rather than as unsupported production service-level objectives.

## What is measured

`scripts/benchmark_performance.py` builds an isolated deterministic persisted `ReferenceState` in a temporary directory and exercises the same FastAPI application and domain code used by normal execution. The default evidence fixture contains:

- 10,000 transport stops;
- 250 critical facilities;
- 750 network nodes and 749 bidirectional road edges; and
- no synthetic runtime, energy or derived production fallback.

The benchmark records p50, p95 and maximum wall-clock latency plus peak Python allocation observed by `tracemalloc` for:

- unchanged persisted-snapshot reload checks;
- `/api/v1/system`;
- `/api/v1/agents/health`;
- bounded `/api/v1/map/reference` viewport projection;
- canonical reference-detail lookup;
- nearest-network-node lookup;
- resilience baseline routing; and
- complete semantic graph serialization.

The benchmark is intentionally source-independent. Live provider acquisition belongs to the separate source smoke workflows and would make latency results non-repeatable.

## Reproduce the benchmark

From an installed development environment:

```bash
python scripts/benchmark_performance.py --output performance-baseline.json
```

A smaller exploratory run can override fixture sizes and iteration counts. The repository's point-in-time evidence workflow is `.github/workflows/performance.yml`; it also runs weekly and can be triggered manually. It uploads the JSON report as a short-lived GitHub Actions artifact.

The report records Python version, operating-system/platform information, machine architecture, logical CPU count, fixture cardinalities, persisted reference size, configured map output bound and every measured result. This makes comparisons meaningful only when fixture and environment differences are considered.

## CI regression guarantees

Ordinary protected PR CI does **not** fail on narrow millisecond thresholds from shared GitHub-hosted runners. Such timings vary with runner placement, CPU contention and image changes and would create false regressions.

Instead, deterministic tests protect stable algorithmic and data-contract properties:

- `ReloadingSnapshot` does not parse an unchanged persisted file again after its validated value is active;
- map responses remain bounded by `limit_per_layer` and preserve explicit total/matched/returned/truncated metadata;
- the map projector retains at most `limit_per_layer` selected canonical objects per requested layer while scanning the current snapshot; and
- API pagination and map query parameters have explicit maximums.

The separate performance workflow supplies comparative latency/memory evidence without weakening protected correctness CI.

## Map scaling characteristics

`/api/v1/map/reference` is a viewport projection, not a transport for the complete canonical reference snapshot. The public API currently allows at most 5,000 returned features per requested layer. With the three supported layers requested together, the theoretical response-selection ceiling is therefore 15,000 features; the dashboard normally requests much smaller viewport results.

The current projector scans the selected canonical layer sequences to determine spatial matches, so CPU work remains **O(n)** in the number of objects in each requested layer. The retained temporary selection is bounded, but geometry-bound checks are still computed during each viewport request. If reference volumes or request concurrency grow substantially, a persistent spatial index or database-backed viewport query is the appropriate next architecture step rather than increasing response limits.

Canonical detail lookup is also currently linear within the selected in-memory layer. It is appropriate for the current single-host research scale and should be indexed if large-layer detail traffic becomes material.

## Snapshot reload characteristics

Every HTTP request performs cheap file-identity checks for runtime, reference, energy and derived persisted states. `ReloadingSnapshot` compares file modification time, size and inode and does not re-read/re-validate JSON while the identity is unchanged. When a validated snapshot changes, the API rebuilds the dependent in-process agent/orchestrator state. Invalid replacement files retain last-known-good state instead of becoming a fast but incorrect fallback.

This design prioritizes deterministic correctness and simple deployment. A multi-process or horizontally scaled deployment would require coordinated snapshot publication/cache invalidation and is outside the current guarantee.

## Graph and routing characteristics

The semantic graph endpoint builds an RDF projection from validated in-memory canonical state for each request and serializes the complete graph. Its cost therefore scales with the amount of semantic state and it is not intended as a high-QPS bulk export endpoint. Production-scale semantic workloads should use a persisted graph store or cached projection.

Resilience routing keeps a NetworkX graph in the Resilience Agent and uses weighted shortest-path operations. Snapshot replacement rebuilds that graph. The benchmark chain network is deterministic and verifies software scaling behavior only; it does not claim that a synthetic topology represents real Berlin routing complexity. Real-road correctness remains the separate issue #14 gate.

Nearest-node lookup currently transforms and scans the persisted node sequence for each request. This is deliberately measured because it is used by dashboard routing. A spatial node index is the expected optimization if real network size makes this operation material.

## Interpretation limits

The benchmark uses FastAPI `TestClient`, so API results include application middleware, validation, serialization and domain computation but exclude reverse-proxy and external network latency. `tracemalloc` reports Python allocations, not resident-set size or container memory. GitHub-hosted runner results are point-in-time observations and must not be presented as production capacity guarantees.

No benchmark result changes the project's scientific semantics: faster execution does not prove data quality, model validity, provider completeness or scenario correctness. Those remain separate verification gates in [`verification.md`](verification.md).

## Current point-in-time evidence

The first successful repository-managed baseline was GitHub Actions run `35004770633` from PR #30. It ran on an Ubuntu 24.04 Azure-hosted x86_64 runner with Python 3.12.14, 4 reported logical CPUs and a 4,695,269-byte persisted benchmark reference. The artifact used 10,000 stops, 250 facilities, 750 nodes and 749 edges and explicitly recorded `temporary_fixture_only=true` and `synthetic_production_fallback=false`.

| Operation | Iterations | p50 ms | p95 ms | max ms | peak traced KiB |
|---|---:|---:|---:|---:|---:|
| unchanged snapshot reload | 35 | 0.012 | 0.018 | 0.079 | 1.950 |
| system API | 7 | 3.358 | 3.552 | 3.595 | 120.237 |
| agent-health API | 7 | 8.039 | 8.266 | 8.352 | 120.746 |
| bounded map viewport | 7 | 186.963 | 193.779 | 196.011 | 419.941 |
| canonical detail | 7 | 3.643 | 3.709 | 3.711 | 103.057 |
| nearest network node | 7 | 13.427 | 13.712 | 13.758 | 123.919 |
| resilience route | 7 | 39.533 | 40.503 | 40.691 | 1,118.346 |
| complete semantic graph serialization | 3 | 14,907.606 | 14,947.922 | 14,952.402 | 77,738.416 |

These numbers are observations, not pass/fail latency targets. They make one important scaling boundary concrete: complete RDF graph export is orders of magnitude heavier than the dashboard-oriented API paths at this fixture size and should be treated as a bulk/research operation. The viewport path remained explicitly capped at 250 features per requested layer (500 maximum for the two benchmarked layers), while still scanning the complete selected layer sequences to compute match metadata.

The raw JSON artifact is the authoritative record for that run. Later scheduled/manual results should be compared only after checking fixture and runner metadata; meaningful regressions should first be reproduced before changing code or introducing a CI threshold.
