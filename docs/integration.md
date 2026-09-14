# Integration model

The repository integrates capabilities through canonical contracts, not through runtime imports from the historical prototype repositories.

## Ingestion paths

Live/current state:

`provider → adapter → canonical object → domain agent → runtime store → API / RDF projection`

Reference state:

`official WFS / VBB GTFS / optional OSM → source adapter → canonical reference objects → reference store → API / RDF / resilience`

Energy:

`explicit Berlin grid-load input → schema-bound adapter → chronological evaluation → candidate selection → one-step forecast → energy store → Energy Agent / API / assessment`

Scenario analysis:

`persisted baseline + explicit Scenario → domain calculation(s) → independent result dimensions → API/dashboard`

## Store separation

- **Runtime store**: changing observations, source statuses and realtime mobility snapshot.
- **Reference store**: facilities, transit stops, official-model features and road-network nodes/edges.
- **Energy store**: evaluation metadata and forecasts whose model/dataset fingerprints have been validated.

This separation prevents an unevaluated forecast, a slow-changing official model or a static transit schedule from masquerading as live sensor state.

## Failure isolation

A failure in one live source does not destroy unrelated valid observations. Last-success/freshness metadata remain separate from current availability. Reference acquisition similarly retains last-known-good data by source/category rather than writing a partially mixed snapshot after an independent source failure.

## API and UI

The API exposes canonical state, reference layers, provenance, deterministic orchestration, resilience analyses and integrated assessment. Resource-heavy map endpoints are paginated and capped. The React/MapLibre dashboard consumes these API contracts only; it does not fabricate client-side measurements when an API domain is unavailable.