# Canonical model

The Pydantic contracts in `shared/contracts.py` reject unknown fields, require timezone-aware timestamps and normalize them to UTC. Numeric observations require units; non-finite numerical values are rejected. Spatial geometry declares its CRS and must be valid. EPSG:4326 coordinates are bounded, while distance calculations use projected coordinates.

Observed, official_modelled, project_modelled, forecast, derived, interpolated and scenario values have distinct meanings. Missing data are represented by absent values and availability status, not zero. A persisted observation retains its original epistemic state; consumers must inspect source freshness and domain health before interpreting it as current.

Current snapshots are `state.json`, `reference.json` and `energy.json` under `data/runtime`. They are acquisition products and excluded from git. Contract version is 1.0.0; application release remains 0.1.0 until full acceptance gates are met.
