# Canonical data model

Shared contracts are the interoperability boundary between agents and prevent domain-specific assumptions from leaking through ad-hoc dictionaries.

## Core entities

- `UrbanEntity`: identified city object with optional validated spatial reference.
- `Observation`: measured/declared observation with UTC time, epistemic state, quality and provenance.
- `DerivedValue`: reproducible calculation with dependency identifiers and derivation status.
- `Forecast`: time-targeted prediction with explicit unit, model provenance, baseline/fingerprint context and optional uncertainty bounds.
- `ScenarioValue`: explicitly hypothetical value tied to a scenario and baseline identifier.
- `OfficialModelFeature`: geometry/properties from an official modelled dataset.
- `TransportStop`: canonical reference entity derived from static transit data.
- `NetworkNode` / `NetworkEdge`: transport/network topology with explicit identifiers, lengths and travel times.
- `CriticalFacility`: facility identity/location with source confidence; never an implied live operating status.
- `AgentDescriptor` / `AgentHealth`: machine-inspectable capabilities and current health semantics.
- source runtime status models: availability, freshness, last successful retrieval, latest observation time and error code remain separate.

## Epistemic states

`observed`, `official_modelled`, `project_modelled`, `forecast`, `derived`, `interpolated`, `scenario`, `unknown`, `unavailable`, `stale`.

These are semantic constraints rather than labels for display only. For example, `Observation` rejects forecast/scenario/unavailable states, while scenario results use dedicated contracts instead of masquerading as observations.

## Units, time and space

Numeric observations/derived values require an explicit unit. Cross-agent datetimes must be timezone-aware and are normalized to UTC. `SpatialReference` validates CRS identifiers and GeoJSON geometry; WGS84 coordinates are bounded.

Metric distance/snapping calculations project into EPSG:25833 for Berlin by default. This avoids treating angular longitude/latitude differences as metres.

## Persistence boundaries

Runtime observations/realtime mobility, reference layers/network objects, and energy evaluation/forecasts are stored separately. This prevents slow reference data, forecasts and live observations from being conflated while still allowing the API and knowledge projection to combine them explicitly.