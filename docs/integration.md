# Integration model

The repository integrates capabilities through contracts, not through imports from the historical prototype repositories.

A normal ingestion path is:

`provider → adapter → canonical object → domain agent → persisted state → API / RDF projection`.

A cross-domain scenario path is:

`persisted baseline + explicit Scenario → domain calculation(s) → independent result dimensions → API/dashboard`.

The runtime store contains changing observations and realtime mobility state. The reference store contains slower-moving facilities, transit stops, official model features and network objects. The energy store carries evaluated model metadata and forecasts separately so that an unevaluated model cannot silently become production state.

Failure in one source must not destroy unrelated valid state. Source statuses preserve last-success/freshness information separately from current availability.
