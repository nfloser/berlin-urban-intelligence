# Documentation

Berlin Urban Intelligence is a research-oriented urban intelligence and digital-twin integration platform for Berlin. This documentation describes the system as implemented in version **1.0.0** and separates verified operational facts from research ambitions, external-provider conditions and future extensions.

## Start here

- [Project overview](overview.md) — purpose, users, boundaries and high-level workflow.
- [Motivation](motivation.md) — the engineering and research problem addressed by the platform.
- [Objectives and scope](objectives-and-scope.md) — primary objectives, non-goals and scope boundaries.
- [Architecture](architecture/overview.md) — system layers, runtime topology and architectural invariants.
- [Data architecture](data/overview.md) — source acquisition, canonicalization, persistence and provenance.
- [Installation](usage/installation.md) and [quickstart](usage/quickstart.md) — reproducible local execution.
- [Testing](development/testing.md) — deterministic CI, browser acceptance and scoped external evidence workflows.
- [Security baseline](security.md) — deployment trust boundary, container/HTTP controls, logging redaction and dependency auditing.
- [Structured observability](observability.md) — operation event names, safe fields, correlation semantics and noise policy.
- [Real Berlin energy evidence](energy-real-evidence.md) — official source validation, chronological evaluation, measured metrics and claim boundaries.
- [Real Berlin road-network evidence](road-network-verification.md) — strict live OSM readiness/routing evidence and provider-failure semantics.
- [Dynamic critical-route monitoring](critical-route-monitoring.md) — automatic critical-facility routing, map refresh, provenance and the explicit no-live-traffic boundary.
- [Cross-domain workflows](evaluation/cross-domain-workflows.md) — verified descriptive multi-domain products, provenance/freshness semantics and scientific claim boundaries.
- [Performance baseline](performance.md) — reproducible latency/memory evidence, bounded map behavior and scaling limits.
- [Accessibility baseline](accessibility.md) — automated keyboard/Axe acceptance, non-pointer routing and the manual release checklist.
- [v1.0 verification matrix](verification.md) — authoritative evidence-backed completion gate for the declared v1 scope.
- [v1.0.0 release notes](releases/v1.0.0.md) — reviewed release scope, evidence and limitations.
- [Changelog](../CHANGELOG.md) — versioned notable project changes.
- [Evaluation](evaluation/methodology.md) — what is evaluated scientifically and what is not yet evaluated.
- [Reproducibility](research/reproducibility.md) — software, data and commands required to reproduce implemented workflows.
- [Roadmap](roadmap.md) — implemented capabilities and planned development, clearly separated.

## Documentation map

### Concepts

The [domain model](concepts/domain-model.md), [terminology](concepts/terminology.md) and [system concepts](concepts/system-concepts.md) define the vocabulary used throughout the repository. Observed, official-modelled, forecast, derived and scenario state are intentionally not interchangeable.

### Architecture

Architecture documentation is split into [overview](architecture/overview.md), [components](architecture/components.md), [data flow](architecture/data-flow.md), [interfaces](architecture/interfaces.md), [deployment](architecture/deployment.md), [operational characteristics](architecture/operational-characteristics.md) and [design decisions](architecture/design-decisions.md). Accepted ADRs remain under [`docs/adr/`](adr/).

### Data

The data section covers [source boundaries](data/data-sources.md), the [canonical data model](data/data-model.md), [processing](data/data-processing.md), [quality](data/data-quality.md) and [provenance](data/provenance.md). The machine-readable source registry remains `config/sources.yaml` and is authoritative for configured provider boundaries. Point-in-time energy and road-network evidence is documented separately so live-provider success is never confused with a permanent implementation constant.

### Implementation and operation

Implementation documentation covers [project structure](implementation/project-structure.md), [modules](implementation/modules.md), [configuration](implementation/configuration.md), [dependencies](implementation/dependencies.md) and [extension points](implementation/extension-points.md). Operational instructions are under [`usage/`](usage/). The concise current development state is maintained in [IMPLEMENTATION_STATUS.md](IMPLEMENTATION_STATUS.md), while [verification.md](verification.md) is the authoritative completion-evidence matrix. Repository-level vulnerability reporting instructions are in [`../SECURITY.md`](../SECURITY.md).

### Development, releases and research

Development guidance covers environment setup, tests, code-quality gates, repository governance and contribution workflow. Stable release metadata is mechanically checked by `tests/test_release_metadata.py`; published release scope is recorded in versioned files under [`docs/releases/`](releases/) and in the repository [changelog](../CHANGELOG.md).

Research documentation records assumptions, reproducibility boundaries, current evaluation methodology and future research directions without treating planned functionality as implemented. The [cross-domain workflow semantics](evaluation/cross-domain-workflows.md) document defines how multi-domain results may be interpreted and which causal or scoring claims are explicitly unsupported.

## Current implementation status

The stable v1.0.0 baseline includes canonical Pydantic contracts, configured source adapters, six domain/aggregation agents, live/reference acquisition, persisted runtime/reference/energy/derived state, leakage-safe energy evaluation and forecasting, resilience calculations, explicit scenarios, registry/capability-driven deterministic orchestration, first-class derivations/dependencies, RDF/semantic relationship projection, a FastAPI API, a React/MapLibre dashboard, structured observability and protected CI/container/browser acceptance. Current post-v1 development additionally includes automatic snapshot-bound critical-route monitoring and persistent MapLibre route visualization; see [dynamic critical-route monitoring](critical-route-monitoring.md).

Some capabilities remain conditional on source data. Energy forecasts require an evaluated matching Berlin-scoped dataset artefact; the reproducible v1 evidence uses the clean official 2024 Stromnetz Berlin high-voltage curve and correctly treats the result as historical. Cross-domain derived products are emitted only when their required persisted source-backed inputs exist and retain source-specific timestamps/freshness. Resilience routing requires a persisted network snapshot; optional OSM acquisition has successful point-in-time real Berlin readiness evidence but remains provider-dependent.

The aggregate v1.0 verification status is **PASS** for the declared scope. This means the documented v1 acceptance/evidence criteria are satisfied. It does **not** claim permanent public-provider availability, municipal operational authority, safety-critical suitability, formal WCAG conformance, causal cross-domain inference, authenticated multi-tenant deployment or production-scale capacity guarantees. See [verification.md](verification.md) and the [v1.0.0 release notes](releases/v1.0.0.md).

## Documentation authority

Documentation is subordinate to executable contracts, configuration, tests and source code when a discrepancy is discovered. Such discrepancies are documentation defects and should be corrected with the relevant implementation change. Point-in-time provider smoke-test results are operational evidence only; they are not guarantees of future source availability or scientific performance beyond their documented scope.