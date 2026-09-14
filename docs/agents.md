# Domain agents

## Live State Agent
Aggregates domain health and availability. It is intentionally not a master score and never manufactures values to make the city look complete.

## Mobility Agent
Consumes VBB GTFS-Realtime summaries and reference GTFS stops. A feed with zero trip updates is represented as unknown/partial evidence, not as proof of normal operation.

## Environmental Exposure Agent
Normalizes official Berlin Luftgütemessnetz LQI records into canonical observations. Current automatic readings retain provisional/suspect quality semantics.

## Urban Heat Agent
Normalizes DWD 10-minute temperature observations and official Berlin Climate Analysis 2022 WFS features. DWD observations are `observed`; climate-analysis layers are `official_modelled`.

## Energy Forecasting Agent
Accepts only Berlin forecasts whose model/dataset evaluation metadata match the registered evaluation boundary. The historical UCI household dataset is a research reference and is never exposed as Berlin energy state.

## Resilience Agent
Runs routing, accessibility and disruption comparisons on explicit network/facility inputs. Scenario closures and penalties are overlays on a copied graph; the baseline graph is not mutated.

All agents publish an `AgentDescriptor` and `AgentHealth`, making capabilities and source dependencies machine-inspectable.
