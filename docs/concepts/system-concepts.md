# System concepts

## Canonical state as the interoperability boundary

Provider schemas and domain-specific records are not passed directly between agents. The platform converts accepted information into shared canonical contracts that carry state, quality, time, units, spatial reference and provenance where applicable.

This design limits accidental semantic coupling. An agent can depend on `Observation`, `Forecast`, `NetworkEdge` or another canonical type without depending on the original provider response format.

## Epistemic separation

The platform treats epistemic state as part of correctness. The following distinctions are intentionally preserved:

- measured/current values are `observed`;
- official external model output is `official_modelled`;
- project predictions are `forecast`;
- reproducible transformations may be `derived`, `interpolated` or `project_modelled`;
- hypothetical changes are `scenario`.

A scenario result therefore cannot silently replace an observation, and Berlin Climate Analysis 2022 features cannot be displayed as live sensor measurements.

## Quality, availability and freshness

These concepts are orthogonal:

- **quality** describes confidence or validation status of accepted data;
- **availability** describes current source/agent accessibility or usable state;
- **freshness** describes age relative to a configured domain threshold.

A source can be unavailable while a last-known-good value remains known, or available while the newest accepted observation is stale.

## Snapshot persistence

The implementation uses three persisted JSON boundaries:

1. runtime state for current observations, mobility and source status;
2. reference state for facilities, static transit, official-model features and network topology;
3. energy state for evaluated model metadata and validated forecast artefacts.

Writes are performed by explicit acquisition/evaluation workflows. API handlers do not contact upstream providers. The application loads persisted state when the FastAPI lifespan starts, so replacing files requires an application reload/restart before the new snapshot is served.

## Agent model

Agents are conventional software components with typed descriptors and health methods. They encapsulate domain behavior; they are not anthropomorphic actors and do not require a language model.

The deterministic orchestrator maps five supported workflow kinds to fixed agent sets and reports agent health. It does not dynamically infer new workflows from agent descriptions and does not compute domain-specific numerical results.

## Scenario model

A `Scenario` is immutable and always hypothetical. Supported scenario dimensions are:

- network disruption: closed edges and multiplicative travel-time penalties;
- extreme heat: temperature delta bounded to -20 to +20 °C;
- energy demand: percentage delta bounded to -100% to +500%;
- infrastructure degradation: explicit unavailable facility identifiers.

Scenario calculations operate on a selected baseline and produce separate scenario result types. The Resilience Agent copies the baseline graph before applying edge overlays.

## Semantic projection

The RDF layer is a projection of canonical objects rather than a separate execution model. It represents entities, observations, forecasts, official-model features and network topology and uses PROV-O relations for lineage. SOSA is used for observations and QUDT is available in the namespace configuration, while project-specific predicates cover concepts not directly mapped to reused vocabularies.

The current repository serializes RDF and includes ontology/SHACL artefacts and a SPARQL query. It does not operate a persistent SPARQL server as part of the default deployment.

## Explainability boundary

The platform prioritizes traceable inputs and transformations over a synthetic cross-domain score. `IntegratedAssessmentService` reports Heat, Energy and Resilience dimensions independently, records unavailable dimensions and returns `composite_score: null` by contract.

This is a design constraint, not a missing UI feature. A future aggregate score would require an explicit validated weighting methodology and corresponding documentation/evaluation.
