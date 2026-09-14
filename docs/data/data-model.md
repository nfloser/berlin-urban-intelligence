# Data model

The canonical data model is implemented in `src/berlin_urban_intelligence/shared/contracts.py` and currently uses contract version `1.0.0`.

## Model principles

- Cross-domain models are frozen Pydantic models with `extra="forbid"`.
- Numeric observations and derived values require explicit units.
- Canonical datetimes are timezone-aware and normalized to UTC.
- Spatial references validate CRS identifiers and GeoJSON geometry.
- Epistemic state is constrained by contract type rather than being a free-form display label.
- Provenance is part of analytical state, not metadata added only at presentation time.

## Value classes

### Observation

Represents an observed/measured value associated with an entity and observation time. `Observation` rejects `forecast`, `scenario` and `unavailable` states. A numeric observation without a unit is invalid.

### DerivedValue

Represents project derivation/interpolation/modelling and records dependency identifiers plus `DerivationStatus`. Its state is restricted to `derived`, `interpolated` or `project_modelled`.

### Forecast

Represents a model prediction with issue and valid times. Bounds are optional, but if one uncertainty bound is supplied the other is required and the point forecast must lie inside the pair. The current energy workflow does not generate calibrated bounds, so its persisted forecast normally has none.

### Scenario result

`ScenarioValue` and domain-specific scenario result models represent hypothetical outputs. They remain distinct from baseline observations/forecasts and carry an explicit scenario/baseline relationship where the model supports it.

### OfficialModelFeature

Represents external official model output with geometry, source properties, provenance and `official_modelled` state. The Climate Analysis workflow uses this type rather than converting model polygons into observations.

## Entity and network classes

`UrbanEntity` provides stable identity, optional name/spatial reference and source identifier. `CriticalFacility` specializes it for facility categories.

`NetworkNode` and `NetworkEdge` represent topology. Edges require positive travel time and length and can be marked bidirectional. The Resilience Agent converts them into a `MultiDiGraph`, preserving parallel edges.

## Health and source state

`AgentHealth` combines availability, freshness, quality, check time and detail. `SourceRuntimeStatus` separately records source availability/freshness, latest retrieval attempt, last successful retrieval, latest observation time and error code.

This distinction lets the system say, for example: transport acquisition is currently unavailable, the last successful retrieval happened earlier, and the retained observation has now become stale.

## Epistemic state

Canonical `DataState` values are:

- `observed`
- `official_modelled`
- `project_modelled`
- `forecast`
- `derived`
- `interpolated`
- `scenario`
- `unknown`
- `unavailable`
- `stale`

These states do not replace quality or availability. They answer a different question: *what kind of claim does this value represent?*

## Spatial conventions

EPSG:4326 is the default interchange CRS. Geometry bounds are validated for WGS84. Metric Berlin calculations in resilience use EPSG:25833 by default.

A facility may be represented by non-point geometry. Facility/network linkage transforms geometry into the metric CRS and uses the point itself or a representative point before finding the nearest network node.

## Persistence schemas

Runtime, reference and energy store models are defined near their corresponding workflows and serialize canonical models into JSON. They should be treated as version-sensitive internal persistence contracts; external consumers should prefer the HTTP API/canonical model documentation unless they intentionally operate on generated snapshots.

For a conceptual view of relationships, see [Domain model](../concepts/domain-model.md).
