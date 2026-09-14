# Evaluation limitations

The following limitations constrain interpretation of current software and experimental outputs.

## Data limitations

- Current Berlin LQI automatic measurements can be provisional.
- DWD `now` observations are not final quality-controlled data.
- VBB GTFS-Realtime coverage depends on feed/operator publication and missing updates do not imply normal service.
- Climate Analysis 2022 is official model output, not a live measured temperature field.
- Hospital/fire-station datasets establish identity/location, not live operational availability or capacity.
- OpenStreetMap is community-maintained and may have missing/inconsistent network attributes.
- A configured Stromnetz Berlin network-level curve must not be generalized into total-city demand.

## Forecasting limitations

The energy experiment uses one chronological holdout, a limited candidate set and hand-defined lag/time features. The current workflow produces one-step point forecasts only. It does not provide calibrated intervals, probabilistic scores, nested model-selection validation, distribution-shift analysis or long-horizon evaluation.

A lower holdout MAE does not by itself establish statistically significant superiority or future generalization.

## Resilience limitations

Travel time is calculated from the acquired network edge attributes and optional documented imputation. It is not dynamically calibrated from live road traffic. Facility snapping is geometric and does not prove a legal/operational access point.

The current repository does not validate route outputs against an external routing ground truth or observed emergency-accessibility outcomes.

## Scenario limitations

Temperature/energy deltas, edge penalties/closures and facility unavailability are user-specified hypothetical inputs. The system calculates consequences under its implemented transformation rules but does not estimate the probability that the scenario will occur or establish causal city response.

## Architecture evaluation limitations

The repository does not yet contain controlled comparisons with alternative integration architectures, quantitative extension-effort studies, semantic interoperability benchmarks, fault-recovery experiments, throughput/load benchmarks or user studies.

The architecture may therefore be described and verified, but not empirically claimed to be more scalable, more maintainable or more accurate than competing systems without further evidence.

## Deployment limitations

- API state is loaded at startup rather than streamed/watched.
- The default backend loads JSON snapshots into process memory.
- No repository-level authentication/authorization is implemented for the API.
- No production scheduler is included for refresh/evaluation.
- No multi-node consistency or horizontal-scaling mechanism has been evaluated.

## Geographic and temporal limitations

The analytical claim is Berlin-focused and inherits each source's actual coverage/resolution. The project does not increase spatial precision beyond source support. Provider snapshots and dated model layers can become outdated; persistence alone does not make data current.

## Operational evidence limitations

Live/reference smoke tests are point-in-time compatibility checks. They should not be summarized as an SLA or long-term availability percentage unless repeated measurements and a defined monitoring period are collected.

## Generalization and policy limitations

Cross-domain co-occurrence and scenario outputs do not establish causality. The platform intentionally avoids a composite city score because no validated weighting model exists. Results should be reported with source dates, freshness, quality, provenance, scenario assumptions and model-evaluation context.
