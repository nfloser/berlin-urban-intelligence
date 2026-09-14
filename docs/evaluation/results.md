# Evaluation results

## Quantitative model results

The repository does **not** commit a fixed benchmark table for the energy model because the production/research input dataset is supplied explicitly and can change between evaluated publications. Consequently, there is no repository-wide MAE/RMSE number that can be stated honestly without identifying the exact source snapshot and generated `data/runtime/energy.json` artefact.

A completed `scripts/evaluate_energy.py` run prints and persists the selected model, MAE, RMSE, persistence baseline MAE, forecast value/time and dataset fingerprint. Those generated values are the result record for that specific experiment.

This documentation intentionally does not invent example performance numbers.

## Software verification results

The permanent CI pipeline is designed to pass only when formatting/linting, strict typing, backend tests, semantic validation, production-data/secret guards, OpenAPI generation, frontend tests/build and container startup/HTTP smoke checks succeed.

A green CI run establishes that these defined checks passed for the tested commit. It does not establish domain-model accuracy, long-term provider uptime or production scalability.

## Live-source evidence

Repository documentation records successful point-in-time live compatibility verification for the current live adapters in September 2026. Such runs show that the adapter/source combination worked at that time. They are not a guarantee of future availability and should not be converted into uptime or reliability percentages without longitudinal monitoring.

The separate reference smoke workflow likewise provides compatibility evidence for current official reference endpoints when run; it is not a benchmark of data completeness or geographic truth.

## Scenario and resilience results

The repository contains deterministic tests demonstrating expected behavior on controlled fixtures (for example, scenario overlays and accessibility/routing mechanics). It does not currently contain a validated Berlin historical-event benchmark from which predictive resilience accuracy or policy effectiveness can be concluded.

## What can currently be concluded

Supported conclusions are limited to:

- the implemented software contracts/invariants are covered by the repository's verification strategy;
- the energy workflow can produce reproducible holdout metrics and a model/fingerprint-bound one-step forecast for a valid explicitly supplied dataset;
- source adapters can be checked independently against current providers;
- network/scenario calculations are deterministic for the loaded inputs and explicit scenario.

Claims about architecture superiority, causal urban impacts, forecast generalization, municipal decision quality or large-scale performance require additional experiments.

## Adding future results

Future result documentation should include:

- research question/hypothesis;
- source snapshot and licence/provenance;
- repository commit and environment;
- baseline(s);
- metric definitions;
- raw/generated result artefact location;
- uncertainty/statistical analysis where appropriate; and
- limitations/failed cases.

Raw results and interpretation should remain distinguishable.
