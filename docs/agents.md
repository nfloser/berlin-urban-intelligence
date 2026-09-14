# Domain agents

All domain agents publish an `AgentDescriptor` and `AgentHealth`, making capabilities and source dependencies machine-inspectable.

## Live State Agent

Aggregates domain health and availability. It is intentionally not a master score and never manufactures values to make the city appear complete.

## Mobility Agent

Consumes VBB GTFS-Realtime and static GTFS reference stops. A realtime feed with zero updates is represented as unknown/partial evidence rather than proof of normal operation. Static GTFS reference ingestion is kept separate from realtime operational state.

## Environmental Exposure Agent

Normalizes official Berliner Luftgütemessnetz LQI records into canonical observations. It supports the currently observed station-envelope response as well as the earlier flat record shape. Current automatic readings retain provisional/suspect quality semantics; missing component grades are not converted to zeros.

## Urban Heat Agent

Normalizes DWD 10-minute meteorological observations and official Berlin Climate Analysis 2022 WFS features. DWD values are `observed`; climate-analysis features are `official_modelled`. Provider missing sentinels remain missing.

## Energy Forecasting Agent

Accepts only Berlin forecasts whose evaluation metadata and dataset fingerprint match the registered evaluation boundary. The supporting workflow performs chronological holdout evaluation against persistence and seasonal-naive baselines and also evaluates Ridge and HistGradientBoosting candidates. Metrics are calculated from holdout predictions rather than embedded. The historical UCI household dataset is methodology/reference only and is never exposed as Berlin energy state.

## Resilience Agent

Runs weighted routing, route comparisons, accessibility and disruption analyses on explicit network/facility inputs. The road representation preserves parallel edges with a `MultiDiGraph`. Scenario closures/penalties are overlays on a copied graph, the baseline graph is not mutated, and facility-to-network snapping is performed with metric Berlin coordinates and an explicit maximum distance.

## Cross-domain assessment

`IntegratedAssessmentService` combines available Heat, Energy and Resilience scenario dimensions. Each dimension preserves its own status/provenance; unavailable dimensions are reported explicitly. The service intentionally emits no synthetic composite score.