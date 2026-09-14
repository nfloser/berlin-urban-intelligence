# Data quality

Data quality is represented explicitly and separately from source availability and epistemic state.

## Quality dimensions

The canonical `QualityFlag` values are `valid`, `suspect`, `partial`, `stale`, `invalid` and `unknown`. A quality flag describes confidence/validation status; it does not answer whether the value is observed, modelled or forecast, and it does not indicate whether the upstream service is currently reachable.

## Source-specific quality constraints

### Berlin air quality

Current automatically measured LQI values are treated as provisional and emitted with `suspect` quality. Missing component grades are omitted. They are not interpreted as zero concentration or a healthy condition.

### DWD

The configured `now` product has not completed final quality control. Provider quality level is retained by parsing logic; current canonical observations can therefore be `suspect` even though they are genuine observations.

### VBB

Realtime coverage depends on feed/operator availability. A valid transport feed with zero updates is insufficient evidence for normal operation, so an empty snapshot receives unknown quality semantics.

### Climate Analysis 2022

These features are official model output rather than observations. If source geometry is invalid but repairable, the geometry is normalized and the feature is marked `suspect`; the repair is recorded in provenance.

### Facilities

The official datasets are authoritative for the documented identity/location scope, not for live opening, staffing, capacity or emergency availability.

### OpenStreetMap

Road-network completeness and attributes vary. OSM is explicitly non-authoritative in the registry. Speed imputation, if enabled, is a derived modelling operation and not evidence that the source provided the speed.

### Energy

The source publication's scope is preserved. A distribution-grid/high-voltage load curve is not generalized into total Berlin electricity demand. Forecast acceptance additionally requires matching model and dataset fingerprints.

## Freshness thresholds

The current live coordinator classifies freshness using:

| Source | Threshold |
|---|---:|
| Berlin air quality | 2 hours |
| DWD | 1 hour |
| VBB GTFS-Realtime | 15 minutes |

These are application thresholds, not guarantees from the providers. They should be revisited if acquisition cadence or intended use changes.

## Missing data

Missingness is preserved when the source does not support a defensible replacement. The platform generally prefers omission/unavailable state over imputation. The notable optional modelling path is OSM speed imputation, which is opt-in and provenance-visible.

## Last-known-good behavior

Retaining previous values during an upstream outage does not make them current. Source runtime status records the failed retrieval attempt and availability, while the retained observation's time drives freshness. Consumers must inspect both.

## Spatial quality

The system validates coordinate reference systems and geometry validity but cannot increase source spatial accuracy. Metric snapping to a road node is an approximation; even a short geometric distance does not prove that the selected node is the legal or operational entrance to a facility.

## Temporal quality

All canonical boundary timestamps are timezone-aware. This prevents naive-time comparisons but does not guarantee that an upstream source timestamp reflects collection latency or final publication time. Provider semantics remain part of provenance/source documentation.

## Quality gaps

The platform does not currently implement a generalized quantitative uncertainty model across domains, automated source-to-source conflict reconciliation, statistical imputation for live missing measurements, or calibrated uncertainty intervals for energy forecasts. These are research/extension opportunities rather than undocumented features.
