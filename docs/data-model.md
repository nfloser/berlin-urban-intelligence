# Canonical data model

The shared contracts are the interoperability boundary between agents.

## Core entities

- `UrbanEntity`: identified city object with optional spatial reference.
- `Observation`: measured/declared observation with UTC time, state, quality and provenance.
- `DerivedValue`: reproducible calculation with dependency identifiers and derivation status.
- `Forecast`: time-targeted prediction, explicit unit, model provenance and optional uncertainty bounds.
- `ScenarioValue`: explicitly hypothetical parameter/value tied to a scenario identifier.
- `OfficialModelFeature`: geometry/properties from an official modelled dataset.
- `NetworkNode` / `NetworkEdge`: transport/network topology; edge lengths and travel times are explicit.
- `CriticalFacility`: facility identity/location with source confidence, never an implied live operating status.

## Epistemic states

`observed`, `official_modelled`, `project_modelled`, `forecast`, `derived`, `interpolated`, `scenario`, `unknown`, `unavailable`, `stale`.

These states are semantic constraints. For example, `Observation` rejects `forecast`, `scenario` and `unavailable` states; scenario results use dedicated contracts rather than masquerading as observations.

## Units, time and space

Numeric observations and derived values require an explicit unit. Cross-agent datetimes must be timezone-aware and are normalized to UTC. `SpatialReference` validates CRS identifiers and GeoJSON geometry; WGS84 coordinates are bounded. Distance/snapping calculations project into a metric CRS explicitly.
