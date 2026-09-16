# Evaluation methodology

Berlin Urban Intelligence currently has two different evidence classes that must not be conflated:

1. **software verification** — tests, static analysis, semantic validation, container startup and provider compatibility checks; and
2. **quantitative model evaluation** — currently implemented formally for the energy forecasting workflow.

The repository does not yet contain a comparative system-level experiment demonstrating superiority of the overall architecture over alternative urban digital-twin platforms.

## Research-evaluation boundary

Software tests establish that implemented invariants behave as expected under tested conditions. Live-source smoke runs establish point-in-time provider compatibility. Neither is a scientific measure of urban-model accuracy, decision quality or architectural superiority.

## Cross-domain descriptive workflows

The platform implements source-backed descriptive cross-domain products, currently Heat + Air Quality and Mobility + Air Quality. These are verified as software/data-integration workflows, not evaluated as causal or predictive models. Their outputs keep source values and timestamps separate, propagate provenance, quality and freshness, and disappear rather than fabricate values when required inputs are absent.

The allowed interpretations and explicit scientific non-claims for each product are defined in [Cross-domain workflow semantics](cross-domain-workflows.md). In particular, these workflows do not calculate correlations, causal effects, passenger exposure, a universal city score or hidden weighted composites.

## Energy forecasting experiment

The implemented formal model experiment operates on an explicitly supplied, timestamp-ordered energy series.

### Research question

For the supplied Berlin-scoped grid-load series, which of the implemented one-step candidates has the lowest holdout error under the current feature construction and chronological split?

This question is intentionally dataset/run specific. The system does not claim the selected model generalizes to all Berlin energy data.

### Data preparation

The pipeline requires:

- unique strictly increasing timestamps;
- finite numeric target values;
- explicit source unit and provenance;
- enough history to construct lag/rolling features and train/test partitions.

Features are constructed using only information available before each target time:

- lag 1;
- seasonal lag (`96` by default);
- rolling mean of previous 4 values;
- rolling mean of previous 16 values;
- sine/cosine time-of-day encoding; and
- weekday.

### Split

After dropping rows with incomplete lag features, data are split chronologically. The default test fraction is 0.2 and the implementation accepts values from 0.1 to 0.5. No random train/test shuffling is used.

### Baselines and candidates

All models are evaluated on the same holdout:

- persistence baseline (`lag_1`);
- seasonal-naive baseline (`lag_seasonal`);
- Ridge regression after standardization; and
- histogram gradient boosting (`learning_rate=0.05`, `max_depth=4`, `max_iter=200`, `random_state=0`).

### Selection

The candidate with lowest MAE is selected; RMSE breaks MAE ties. Exact metric ties prefer the deterministic simplicity order persistence -> seasonal naive -> Ridge -> histogram gradient boosting.

### Artefact binding

The entire input frame is fingerprinted with SHA-256 over canonical timestamp/value content and column names. The selected evaluation and forecast artefact carry this fingerprint. The Energy Agent rejects forecast registration if model ID or dataset fingerprint does not match the registered evaluation.

### Forecast horizon

The workflow retrains the selected model on usable history and produces exactly one next-cadence point forecast. The timestamp cadence must be regular. No calibrated prediction interval is implemented.

## Resilience evaluation status

Routing/accessibility algorithms are behaviorally tested, including scenario overlays and snapping constraints. The repository does not currently include a benchmark against a reference routing engine, measured travel-time ground truth, scalability benchmark or validated accessibility outcome dataset. Route deltas are therefore analytical outputs, not validated predictive-accuracy results.

## Scenario assessment status

Scenario transformations are deterministic sensitivity calculations over explicit baselines. They are not causal forecasts of city response. No empirical calibration currently validates a temperature delta, energy-demand percentage delta or network penalty as a realistic future scenario distribution.

## Architecture evaluation status

The architecture is verified for reproducibility, failure semantics, typed boundaries and integration behavior through tests/CI. Comparative measures such as extension effort, throughput, fault recovery time, semantic interoperability score or developer/user study are not yet implemented.

## Reproducibility

See [Experiments](experiments.md) for executable experiment procedure and [Research reproducibility](../research/reproducibility.md) for environment/data capture requirements.
