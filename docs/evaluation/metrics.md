# Evaluation metrics

Metrics are interpreted only within the experiment that generates them. The repository does not define one project-wide performance score.

## Energy MAE

Mean absolute error:

\[
\mathrm{MAE} = \frac{1}{n}\sum_{i=1}^{n} |y_i - \hat{y}_i|
\]

MAE is the primary model-selection metric in the current energy pipeline because it expresses average absolute error in the target's original unit and is less dominated by individual large errors than squared-error metrics.

Limitations: MAE does not show error direction, temporal clustering, tail behavior or calibration. Values are not comparable across differently scaled targets without normalization.

## Energy RMSE

Root mean squared error:

\[
\mathrm{RMSE} = \sqrt{\frac{1}{n}\sum_{i=1}^{n} (y_i - \hat{y}_i)^2}
\]

RMSE is reported as a secondary metric and tie-breaker. It penalizes larger errors more strongly than MAE.

Limitations: RMSE can be disproportionately influenced by outliers and remains scale-dependent.

## Baseline comparison

Every `ModelMetric` records a persistence baseline ID and baseline MAE. Candidate metrics should be interpreted relative to this simple baseline rather than in isolation. The pipeline also evaluates a seasonal-naive baseline on the same holdout.

The current selection algorithm does not require a complex model to beat persistence by a predefined statistical/significance margin; it simply selects the lowest holdout MAE under deterministic tie-breaking. A future research evaluation should add uncertainty/significance analysis if claims are made about model superiority.

## Resilience outputs

Route comparison exposes:

- baseline travel time;
- scenario travel time;
- absolute delta in seconds; and
- relative delta percentage.

These are deterministic network-analysis outputs for the loaded graph/scenario, not accuracy metrics against observed journey times.

Accessibility reports reachable, unreachable and unsnapped facility identifiers for a configured time budget and snapping threshold. Counts may be derived by a consumer, but the repository does not define a validated policy threshold or universal resilience score from them.

## Availability and freshness

Agent/source availability and freshness are operational-state indicators, not evaluation metrics. A high availability fraction from a short smoke period would not establish long-term reliability without a defined observation period and monitoring design.

## Software verification metrics

Pytest coverage is reported but no minimum percentage threshold is currently enforced. Test count and coverage should not be used as substitutes for behavior/risk coverage.

CI pass/fail is evidence that the defined verification gates succeeded for a commit; it is not a scientific performance measure.

## Metrics not currently implemented

The repository does not currently report:

- MAPE/sMAPE or probabilistic forecast scores;
- calibrated interval coverage/width;
- routing accuracy against ground truth;
- end-to-end latency/throughput percentiles;
- memory/CPU scaling curves;
- source uptime SLA statistics;
- semantic interoperability benchmarks; or
- user/decision-quality metrics.

Such metrics should be added only together with a defined methodology and reproducible experiment.
