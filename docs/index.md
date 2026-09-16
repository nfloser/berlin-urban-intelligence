# Documentation

Berlin Urban Intelligence is a research-oriented urban intelligence and digital-twin integration platform for Berlin. This documentation describes the system as implemented in version 0.1.0 and separates operational facts from research ambitions and future extensions.

## Start here

- [Project overview](overview.md) — purpose, users, boundaries and high-level workflow.
- [Motivation](motivation.md) — the engineering and research problem addressed by the platform.
- [Objectives and scope](objectives-and-scope.md) — primary objectives, non-goals and scope boundaries.
- [Architecture](architecture/overview.md) — system layers, runtime topology and architectural invariants.
- [Data architecture](data/overview.md) — source acquisition, canonicalization, persistence and provenance.
- [Installation](usage/installation.md) and [quickstart](usage/quickstart.md) — reproducible local execution.
- [Testing](development/testing.md) — deterministic CI, live-source checks and current testing gaps.
- [Security baseline](security.md) — deployment trust boundary, container/HTTP controls, logging redaction and dependency auditing.
- [Structured observability](observability.md) — operation event names, safe fields, correlation semantics and noise policy.
- [Performance baseline](performance.md) — reproducible latency/memory evidence, bounded map behavior and scaling limits.
- [Accessibility baseline](accessibility.md) — automated keyboard/Axe acceptance, non-pointer routing and the manual release checklist.
- [v1.0 verification matrix](verification.md) — evidence-backed PASS/PARTIAL/NOT VERIFIED status for completion gates and linked follow-up issues.
- [Evaluation](evaluation/methodology.md) — what is evaluated scientifically and what is not yet evaluated.
- [Reproducibility](research/reproducibility.md) — software, data and commands required to reproduce the implemented workflows.
- [Roadmap](roadmap.md) — implemented capabilities and planned development, clearly separated.

## Documentation map

### Concepts

The [domain model](concepts/domain-model.md), [terminology](concepts/terminology.md) and [system concepts](concepts/system-concepts.md) define the vocabulary used throughout the repository. In particular, observed, official-modelled, forecast, derived and scenario state are intentionally not interchangeable.

### Architecture

Architecture documentation is split into [overview](architecture/overview.md), [components](architecture/components.md), [data flow](architecture/data-flow.md), [interfaces](architecture/interfaces.md), [deployment](architecture/deployment.md), [operational characteristics](architecture/operational-characteristics.md) and [design decisions](architecture/design-decisions.md). Accepted ADRs remain under [`docs/adr/`](adr/).

### Data

The data section covers [source boundaries](data/data-sources.md), the [canonical data model](data/data-model.md), [processing](data/data-processing.md), [quality](data/data-quality.md) and [provenance](data/provenance.md). The machine-readable source registry remains `config/sources.yaml` and is authoritative for configured provider boundaries.

### Implementation and operation

Implementation documentation covers [project structure](implementation/project-structure.md), [modules](implementation/modules.md), [configuration](implementation/configuration.md), [dependencies](implementation/dependencies.md) and [extension points](implementation/extension-points.md). Operational instructions are under [`usage/`](usage/). The concise current development state is maintained in [IMPLEMENTATION_STATUS.md](IMPLEMENTATION_STATUS.md), while [verification.md](verification.md) is the authoritative completion-evidence matrix. Repository-level vulnerability reporting instructions are in [`../SECURITY.md`](../SECURITY.md).

### Development and research

Development guidance covers environment setup, tests, code-quality gates, repository governance and contribution workflow. Research documentation records assumptions, reproducibility boundaries, current evaluation methodology and future research directions without treating planned functionality as implemented.

## Current implementation status

The repository currently implements canonical Pydantic contracts, source adapters, six domain/aggregation agents, live and reference acquisition workflows, a leakage-safe energy evaluation and one-step forecasting workflow, network resilience calculations, explicit hypothetical scenarios, registry/capability-driven deterministic orchestration, first-class derived information/dependencies, RDF projection, a FastAPI API, a React/MapLibre dashboard and protected deterministic CI/container/browser acceptance.

Some capabilities are conditional on data availability. In particular, the Energy Agent requires a successfully evaluated Berlin-scoped input dataset before it exposes forecasts, and Resilience routing requires a persisted network snapshot. Optional OpenStreetMap acquisition is not part of the default reference refresh.

The current aggregate v1.0 verification status is **NOT READY**. This does not mean the implemented application is unusable; it means critical evidence gaps remain and are explicitly tracked rather than being converted into completion claims. See [verification.md](verification.md) for the exact gates and issues.

The repository does not implement a municipal control system, a universal Berlin score, causal inference across domains, calibrated forecast intervals, an authoritative real-time facility-capacity system, an authenticated multi-tenant service, or an LLM-dependent execution core.

## Documentation authority

Documentation is subordinate to executable contracts, configuration, tests and source code when a discrepancy is discovered. Such discrepancies are documentation defects and should be corrected together with the relevant implementation change. Point-in-time provider smoke-test results are operational evidence only; they are not guarantees of future source availability and are not scientific performance results.
