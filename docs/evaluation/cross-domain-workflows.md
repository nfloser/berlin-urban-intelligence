# Cross-domain workflow semantics

Berlin Urban Intelligence exposes cross-domain information only when the required persisted source-backed inputs exist. These products are descriptive context, not causal models, universal city scores or decision recommendations. Each record retains its individual source values, timestamps, quality/freshness state, upstream identifiers and derivation metadata.

## Heat + Air Quality context

`heat-air-quality-context-v1` pairs the latest persisted DWD 2 m air-temperature observation with the latest persisted Berlin LQI grade.

The output keeps both measurements separate and exposes the temperature and LQI entity identifiers and observation timestamps. Its quality is the least favourable quality of the two observations. Its freshness is the least favourable source freshness across `dwd_open_data` and `berlin_air_quality`.

The workflow can support inspection of simultaneously available heat and air-quality conditions. It cannot establish that heat caused an air-quality state, estimate a person's exposure, represent every location in Berlin, or produce a combined health/risk score. DWD and air-quality observations can refer to different stations, spatial footprints and observation times.

If either required observation is absent, no Heat + Air Quality record is emitted. A missing input is never replaced by a synthetic value.

## Mobility + Air Quality context

`mobility-air-quality-context-v1` co-reports the delayed trip-update share from the persisted VBB GTFS-Realtime snapshot with the latest persisted Berlin LQI grade.

The mobility value is calculated as `delayed_trip_updates / trip_updates` for trip updates present in the realtime feed. The output additionally exposes the numerator, denominator, mobility timestamp, LQI grade, LQI station/entity identifier and LQI observation timestamp. Its quality is the least favourable quality of the mobility snapshot and LQI observation. Its freshness is the least favourable source freshness across `vbb_gtfs_rt` and `berlin_air_quality`.

This workflow can support descriptive inspection of public-transport feed conditions alongside the available air-quality observation. It cannot be interpreted as a network-wide punctuality rate, a causal effect of mobility on air quality, a passenger exposure estimate or evidence that service delays and LQI conditions are spatially co-located. No correlation, regression, weighting or combined score is calculated.

If the mobility snapshot is absent, contains zero trip updates, or the LQI observation is absent, no Mobility + Air Quality record is emitted. If persisted last-known-good inputs still exist while a current source acquisition is unavailable, the record may remain inspectable but its freshness becomes `unavailable`; consumers therefore see the source failure rather than a falsely current result.

## Provenance and implementation contract

Both workflows are produced by the deterministic `DerivedProductBuilder` during the normal dependency-aware derived refresh. They are persisted through `DerivedStateStore` and exposed by `/api/v1/derived`, `/api/v1/dependencies/{resource_id}` and `/api/v1/provenance/{resource_id}`. The dashboard Derived Information inspector exposes the value, status, freshness, quality, definition, scientific interpretation, producer/algorithm version, inputs, dependency lineage and provenance.

The implementation contract intentionally forbids hidden aggregation across domains. Adding future cross-domain products requires an explicit definition, source-backed inputs, documented interpretation limits, missing-input behavior and deterministic tests before the result can be presented as verified functionality.

## Verification

Repository tests cover populated products, quality/freshness propagation, last-known-good behavior during source failure and missing-domain omission. The composed browser acceptance path seeds validated persisted-state fixtures only for UI verification, then exercises the actual nginx → FastAPI → persisted state → React path and inspects both cross-domain definitions. These fixtures do not constitute current live Berlin measurements; live-source acquisition remains independently monitored by the source smoke workflows.
