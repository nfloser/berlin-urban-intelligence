# Future research

This page records research directions that are **not** claims about current implementation performance.

## Architecture evaluation

A future publication should move beyond descriptive architecture by evaluating concrete hypotheses, for example:

- whether explicit canonical/epistemic contracts reduce integration defects compared with ad-hoc domain exchange;
- whether adding a new source/agent requires less cross-module change under the current modular boundary than under a coupled baseline;
- whether failure isolation preserves more usable state during controlled source outages;
- whether provenance completeness remains stable across JSON, API and RDF projections.

These questions require predefined baselines and measurable outcomes.

## Cross-domain scenario validation

Current scenarios are deterministic sensitivity calculations. Future work could reproduce documented historical disruptions/heat events using archived source snapshots and compare modelled accessibility/state changes with independent observations.

A valid experiment would need to distinguish scenario plausibility, input-data uncertainty and algorithm error.

## Resilience methodology

Potential research extensions include:

- observed/live traffic-aware edge costs;
- mode-specific or multimodal networks;
- explicit facility entrance/access relations rather than nearest-node approximation;
- capacity/redundancy measures from verified sources;
- benchmark comparison against established routing/accessibility methods;
- sensitivity analysis for snapping thresholds and imputed speeds.

## Energy forecasting

Potential extensions include rolling-origin evaluation, additional transparent baselines, calibrated prediction intervals, probabilistic metrics, weather/calendar exogenous features, drift monitoring and multi-horizon forecasts.

Any added model should retain chronological leakage prevention, dataset fingerprinting and a simple baseline comparison.

## Semantic interoperability

The ontology/provenance layer could be evaluated with competency questions, SHACL coverage, SPARQL query suites and mappings to additional established urban/energy/mobility vocabularies. A persistent triplestore/federated query layer may be studied after synchronization semantics are defined.

## Distributed/federated agents

The current in-process agent model could evolve into remotely deployed domain services. Research questions include contract version negotiation, transport/event semantics, distributed provenance, idempotency, partial failure and reproducibility across independently deployed modules.

Distribution should be evaluated as a trade-off rather than assumed to improve the system.

## Orchestration

Current orchestration is a fixed deterministic mapping. Future research can compare:

- static typed workflows;
- capability-based deterministic planning;
- rule/policy engines; and
- optional language-model interpretation that produces typed requests.

An LLM, if evaluated, should be kept outside the numerical truth boundary and measured on request-translation correctness rather than permitted to invent domain outputs.

## Human and decision-support evaluation

The dashboard has not been evaluated through a user study. Future work could measure whether explicit freshness, provenance, scenario and unavailable-state presentation improves analyst understanding or reduces misinterpretation.

## Scalability and operations

Before production-scale claims, benchmark state-load time, API latency, memory use, RDF generation, network algorithms and large collection pagination at realistic Berlin-scale volumes. Controlled fault and restart/reload experiments would complement throughput benchmarks.

## Publication path

A future paper should select a limited research thesis rather than documenting every feature. A strong architectural study would combine:

1. a precise interoperability/federation research question;
2. formal architecture and invariants;
3. Berlin multi-domain implementation as an artefact;
4. controlled extension/failure experiments;
5. at least one quantitative domain case study;
6. reproducibility package; and
7. explicit threats to validity/limitations.

Until such experiments are completed, the repository should describe these items as future research rather than completed contributions.
