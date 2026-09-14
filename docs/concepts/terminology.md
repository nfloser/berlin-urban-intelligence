# Terminology

This glossary defines terms used consistently across Berlin Urban Intelligence.

| Term | Meaning in this repository |
|---|---|
| **Agent** | A deterministic software component with an `AgentDescriptor`, domain responsibilities and a health interface. It is not assumed to be an autonomous LLM. |
| **Canonical contract** | A versioned Pydantic model used as the interoperability boundary between domains. |
| **Observation** | A canonical value tied to an observation time and source provenance. It cannot carry `forecast`, `scenario` or `unavailable` data state. |
| **Official modelled** | Output of an external official model, such as Berlin Climate Analysis 2022. It is not a measurement. |
| **Project modelled** | A value modelled by this project rather than directly observed or externally official-modelled. |
| **Forecast** | A time-targeted project prediction with issue/valid times, explicit unit and model provenance. |
| **Derived value** | A reproducible calculation from one or more upstream values, with dependency identifiers. |
| **Scenario** | An explicitly hypothetical input describing bounded changes such as temperature delta, energy-demand delta, edge closures/penalties or unavailable facilities. Scenario objects are always hypothetical. |
| **Epistemic state / data state** | A machine-readable indication of what kind of knowledge a value represents: observed, modelled, forecast, derived, scenario and related states. |
| **Quality flag** | A separate judgement about a value's quality (`valid`, `suspect`, `partial`, `stale`, `invalid`, `unknown`). Quality is not the same as data state. |
| **Availability** | Whether a source/agent can currently provide usable access or state. Availability is separate from freshness. |
| **Freshness** | Whether the newest known observation is within a source/domain-specific age threshold. |
| **Last-known-good** | Previously accepted canonical state retained when a later independent source refresh fails. It does not make the failed source currently available. |
| **Reference state** | Slower-changing facilities, static transit stops, official-model features and optional road-network topology. |
| **Runtime state** | Current observations, realtime mobility snapshot, per-source runtime status and refresh errors. |
| **Energy state** | Persisted energy evaluation metadata plus forecast artefacts validated against the selected model and dataset fingerprint. |
| **Provenance** | Provider, dataset, source URL, identifiers, timestamps, processing method, producing agent/model, licence, quality notes and upstream lineage. |
| **Source registry** | `config/sources.yaml`, the machine-readable description of configured external source boundaries and limitations. |
| **Source adapter** | Code that isolates provider-specific access/parsing and converts external structures into typed input records or canonical objects. |
| **Orchestrator** | A deterministic workflow selector/executor that maps a supported workflow kind to a fixed list of domain agents and reports their health. It does not calculate domain results. |
| **Integrated assessment** | A scenario coordination service that can produce independent Heat, Energy and Resilience results and explicit per-dimension failures. It deliberately has no composite score. |
| **Knowledge projection** | RDF representation of canonical entities, observations, forecasts, network objects and provenance. Canonical application state remains the primary execution representation. |
| **Authoritative source** | A source marked authoritative in the project registry for its documented scope. This does not imply that every derived interpretation is authoritative. |
| **Operational state** | State intended to describe current conditions. Static reference data such as facility locations do not imply operational availability. |

## Data-state vocabulary

The canonical `DataState` enumeration contains:

`observed`, `official_modelled`, `project_modelled`, `forecast`, `derived`, `interpolated`, `scenario`, `unknown`, `unavailable`, `stale`.

Not every contract accepts every state. Contract-level validation is part of the semantic boundary.

## Coordinate terminology

**EPSG:4326 / WGS84** is the primary interchange coordinate reference used for longitude/latitude geometries. **EPSG:25833** is the default projected metric CRS used by Berlin resilience distance/snapping calculations.

## “Live” terminology

“Live” in this repository means current/realtime acquisition paths and health state; it does not imply zero latency, continuous streaming or guaranteed provider availability. Persisted snapshots are updated by explicit refresh commands and the API loads them at process startup.
