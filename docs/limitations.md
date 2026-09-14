# Limitations

This repository is a research foundation, not an authoritative municipal operations system.

- **Energy:** no Berlin forecast is exposed unless a Berlin dataset/model evaluation and matching forecast artefact exist. The UCI household prototype is not Berlin data.
- **Air quality:** current automatic readings can be provisional and must not be described as final validated measurements.
- **DWD:** `now` observations have not completed final provider quality control.
- **Climate Analysis 2022:** official model output represents a modelled climate situation, not a live sensor field.
- **Mobility:** GTFS-Realtime coverage is feed-dependent. Missing updates do not prove normal service.
- **Resilience:** routing quality depends on the acquired network and facility source. OpenStreetMap is community-maintained and not complete critical-infrastructure truth.
- **Spatial precision:** the platform does not claim street/building precision where source resolution does not support it.
- **Causality:** cross-domain co-occurrence is not a causal claim.
- **Composite scores:** no universal Berlin health/resilience score is produced.
- **Live services:** provider outages and schema changes can make live smoke tests fail while deterministic software tests remain valid.

Any publication or downstream decision-support product should report these limits together with source dates, provenance and model evaluation details.
