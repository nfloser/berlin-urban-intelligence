# Limitations

Berlin Urban Intelligence is a research platform, not an authoritative municipal operations or control system.

- **Energy scope:** the implemented workflow can evaluate and forecast explicitly supplied Stromnetz Berlin grid-load publications, but a published network-level load curve is not the same as total Berlin electricity demand. A forecast is exposed only when dataset/model evaluation metadata and fingerprints match. The UCI household prototype is not Berlin data.
- **Forecast horizon:** the current energy workflow produces a one-step point forecast. No calibrated uncertainty interval is claimed because no interval-calibration method is implemented.
- **Air quality:** current automatic Berlin LQI readings can be provisional and must not be described as final validated measurements. Missing component values are not zeros.
- **DWD:** configured `now` observations have not completed final provider quality control.
- **Climate Analysis 2022:** the ingested official WFS is model output representing an official modelled climate situation, not a live sensor field.
- **Mobility:** GTFS-Realtime coverage is feed/operator dependent. Missing updates do not prove normal service.
- **Facility data:** official hospital/fire-station identity and location do not imply real-time opening, capacity or operational availability.
- **Resilience:** route/accessibility quality depends on the acquired road graph, travel-time attributes and facility locations. OpenStreetMap is community-maintained and cannot be treated as complete authoritative critical-infrastructure truth. Deterministic CI routing fixtures do not prove that a current real Berlin road graph was successfully acquired; live network verification is tracked in issue #14.
- **OSM speed imputation:** optional OSMnx imputation is a derived modelling choice and must remain provenance-visible.
- **Snapping:** facility-to-network assignment is a geometric approximation with an explicit maximum distance; a snapped facility is not evidence that the chosen road node is its legal/operational access point.
- **Spatial precision:** the platform does not claim street/building precision where the source resolution does not support it.
- **Causality:** cross-domain co-occurrence or scenario comparison is not a causal claim.
- **Composite scores:** no universal Berlin health/resilience score is produced.
- **Persisted snapshots:** a running API checks runtime, reference, energy and derived snapshot file identities before requests and hot-reloads validated replacements. Invalid replacements retain the previous validated in-process state and expose reload diagnostics. This is a single-process consistency mechanism, not a distributed synchronization protocol: multiple backend processes can still observe different file versions at different instants.
- **Semantic state:** RDF is a projection of canonical state rather than an independent source of truth. The public graph endpoint does not yet expose the full persisted derived projection/typed semantic relationship surface; issue #12 tracks that gap.
- **Security:** the current research API has no application authentication/authorization or application rate limiting. Public/shared deployment requires an appropriate external access-control boundary; the broader security baseline is tracked in issue #18.
- **Performance:** no production-scale load/soak benchmark or release SLO is currently claimed; issue #17 tracks reproducible performance evidence.
- **Accessibility:** the dashboard has semantic labels/roles in important interactions, but broad WCAG-oriented and keyboard-only acceptance is not yet claimed; issue #16 tracks that verification.
- **Live services:** provider outages and future schema changes can make live smoke checks fail while deterministic software tests remain valid.

Any publication or decision-support use should report these limitations together with source dates, provenance, freshness, model evaluation details and scenario assumptions. The repository-wide completion evidence and open gates are maintained in [verification.md](verification.md).
