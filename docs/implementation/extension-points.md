# Extension points

Berlin Urban Intelligence is designed to be extended through explicit interfaces rather than by bypassing canonical contracts.

## Add a data source

A new external source normally requires:

1. add source metadata and limitations to `config/sources.yaml`;
2. implement a provider-specific adapter under `adapters/`;
3. define/choose the canonical output contract and epistemic state;
4. preserve provider timestamps, identifiers, units, licence and quality notes in provenance;
5. add deterministic parsing/schema tests using fixtures;
6. add acquisition integration into the appropriate live/reference workflow;
7. define failure/freshness behavior rather than a synthetic fallback;
8. update data-source, processing, quality and reproducibility documentation; and
9. add a live smoke check only if external compatibility needs operational verification.

A source ID referenced by an agent should match the registry.

## Add a domain agent

A new agent should derive from `BaseAgent`, publish an `AgentDescriptor`, implement `health()` and consume/produce explicit typed contracts.

Document:

- responsibility and non-responsibilities;
- input/output contracts;
- source dependencies;
- freshness/quality semantics;
- deterministic calculations and failure modes;
- persistence requirements, if any.

Do not use an agent as a wrapper around untyped provider responses.

If the agent participates in orchestration, update `Orchestrator._PLANS` or introduce a separately documented planning mechanism. Current orchestration is not capability-discovery based despite descriptors containing capabilities.

## Add a canonical contract

Cross-domain contract changes are high-impact. New/changed models should:

- use explicit units/time/state/quality where relevant;
- reject ambiguous/invalid combinations;
- define provenance expectations;
- remain serializable through required persistence/API paths;
- receive contract tests and RDF mapping if semantically exposed;
- consider `CONTRACT_VERSION` compatibility.

A breaking semantic change should not be hidden behind an unchanged contract version.

## Add an analytical model

Analytical components should define:

- input data and assumptions;
- feature construction/transformation;
- evaluation split/validation design;
- meaningful baselines;
- metrics and selection criteria;
- random seeds or deterministic controls;
- model artefact identity and dataset binding;
- failure behavior and uncertainty limitations.

Model performance must not be added to documentation without reproducible evidence.

## Add a scenario dimension

Extend `ScenarioKind` and validation so parameters are bounded and semantically tied to the new kind. Implement the transformation in the owning domain or scenario engine without mutating baseline state. Add typed result models and integrated-assessment behavior only when prerequisites and failure semantics are explicit.

If a new scenario introduces cross-domain weighting or causality, that is a research-methodology change rather than a simple field addition.

## Add an API endpoint

Prefer domain/canonical models for request and response shapes. Define validation bounds and explicit error conditions. Update frontend client types if consumed by the dashboard, interface documentation, API tests and OpenAPI validation.

Large collection endpoints should consider the existing pagination pattern and response-size constraints.

## Add a visualization

Visualizations must reflect API state rather than generate domain values client-side. Preserve unavailable/suspect/stale distinctions where relevant. Geometry should be displayed only with a compatible CRS or explicit transformation.

## Add a persistent semantic store

The current knowledge graph is generated in memory/RDF files. A future SPARQL/triplestore integration should preserve canonical identifiers and provenance and must define synchronization/consistency behavior relative to JSON state. The semantic store should not silently become an independent conflicting source of truth.

## Distributed agents

The current contracts intentionally precede transport. A future message bus or remote-agent protocol should serialize/version the same canonical semantics and define idempotency, retries, authentication, observability and compatibility. Distribution is not required to extend the current in-process system.

## Extension checklist

An extension is complete only when implementation, tests, source/architecture documentation, configuration and reproducibility instructions agree. If new functionality is only conceptual, mark it planned rather than adding an API or capability claim to the README.
