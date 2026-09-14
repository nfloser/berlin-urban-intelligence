# Components

This page describes architectural responsibilities rather than mirroring directory names.

## Component map

| Component | Responsibility | Main inputs | Main outputs | Primary implementation |
|---|---|---|---|---|
| Source adapters | Isolate provider access, payload parsing and provider-specific schema rules. | HTTP/file responses or explicit input files. | Typed provider records or canonical reference objects. | `src/berlin_urban_intelligence/adapters/` |
| Canonical contracts | Enforce cross-domain state, quality, time, unit, geometry and provenance constraints. | Domain values. | Frozen validated Pydantic models. | `shared/contracts.py` |
| Refresh coordinator | Best-effort independent live-source acquisition with last-known-good retention. | Air-quality, DWD and VBB clients; previous runtime state. | `RuntimeState`. | `runtime/refresh.py` |
| Reference refresh | Acquire slow-changing facilities and official climate layers; preserve prior data per failed source. | Berlin WFS clients; previous reference state. | `ReferenceState`. | `runtime/reference_refresh.py` |
| Energy workflow | Parse explicit grid-load input, evaluate candidates chronologically, select a candidate and produce one next-step artefact. | Explicitly configured tabular dataset. | Evaluation metadata and forecast artefact persisted as energy state. | `energy/`, `scripts/evaluate_energy.py` |
| Domain agents | Encapsulate domain state, calculations and health semantics. | Canonical/provider-domain records. | Domain snapshots, observations, forecasts or analysis results. | `agents/` |
| Resilience engine | Routing, route comparison, facility snapping and accessibility under scenario overlays. | Network nodes/edges, facilities, scenarios. | Route/accessibility results. | `agents/resilience.py` |
| Scenario engine | Apply bounded hypothetical deltas while retaining baseline identity. | Baseline observation/forecast plus `Scenario`. | Scenario result types. | `scenario_engine/` |
| Deterministic orchestrator | Select fixed supported agent combinations and report workflow health. | `OrchestrationRequest`, agent registry. | `ExecutionPlan`, `ExecutionResult`. | `orchestrator/engine.py` |
| Integrated assessment | Coordinate independent Heat, Energy and Resilience scenario calculations. | `AssessmentRequest`, agents and reference data. | `IntegratedAssessment` with per-dimension errors and no composite score. | `orchestrator/assessment.py` |
| Knowledge projection | Convert canonical state/lineage into RDF. | Canonical entities, values, network objects. | Turtle/RDF graph. | `knowledge/graph.py` |
| HTTP API | Serve persisted state and analytical operations with operation IDs. | Persisted stores + typed requests. | Versioned JSON/text responses. | `api/app.py` |
| Dashboard | Visualize API state and initiate supported requests. | Backend HTTP API. | Browser research UI and map views. | `frontend/` |

## Agents

All agents derive from `BaseAgent`, which provides an injectable timezone-aware clock and requires a `health()` implementation. `AgentDescriptor` exposes identity, version, capabilities, input/output contract names and source dependencies.

### Live State Agent

**Purpose:** aggregate health from registered domain agents.

**Behavior:** reports overall availability only. It does not combine measurements or calculate a city score. All available -> available; a mixture containing available/degraded -> degraded; otherwise unavailable/unknown according to the actual health set.

### Mobility Agent

**Purpose:** summarize VBB GTFS-Realtime updates.

**Input:** decoded trip records and feed timestamp.

**Output:** `MobilitySnapshot` with update counts, delayed-trip count, maximum absolute reported delay, source time, retrieval time, quality and note.

**Failure/quality behavior:** zero trip updates are represented as unknown evidence rather than normal service. A 15-minute freshness threshold is used by current health logic.

### Environmental Exposure Agent

**Purpose:** normalize official Berlin LQI data.

**Output:** canonical observations for station LQI grade and available component grades.

**Quality behavior:** current automatic LQI values are marked `suspect` because they remain subject to provider quality control. Missing components are omitted rather than converted to zero.

### Urban Heat Agent

**Purpose:** represent measured DWD meteorology and normalize official Berlin climate-model features without conflating them.

**Measured output:** DWD temperature, near-ground temperature, humidity, pressure and dew point observations where values are present.

**Reference/model output:** `OfficialModelFeature` objects. Invalid-but-repairable source geometries are repaired with `shapely.make_valid` and marked suspect with the transformation recorded in provenance.

### Energy Agent

**Purpose:** enforce the boundary between evaluated Berlin-scoped forecasting artefacts and API-visible forecasts.

A forecast can be registered only after a Berlin evaluation is present and only when `model_id` and `dataset_fingerprint` match that evaluation. The agent does not reinterpret the UCI household reference dataset as Berlin demand.

### Resilience Agent

**Purpose:** weighted network routing, disruption comparison and facility accessibility.

It uses a NetworkX `MultiDiGraph` so parallel edges are preserved. Scenario edge closures/penalties are applied to a copied graph. Facility snapping uses metric projected coordinates and an explicit maximum distance; unsnapped facilities remain explicit.

## Orchestrator behavior

The orchestrator currently supports five hard-coded workflow families: `urban_snapshot`, `heat_energy`, `mobility_exposure`, `mobility_resilience`, and `heat_mobility_resilience`.

The mapping is defined in `Orchestrator._PLANS`. It is not dynamically inferred from descriptors. `plan()` returns the expected agent identifiers; `execute()` queries the corresponding agents' health and returns overall availability/missing agents. Domain numerical analysis remains the responsibility of domain components.

## Failure boundaries

Provider transport/schema failures are converted into explicit source error codes where acquisition coordinators can classify them. Domain absence propagates as unavailable/degraded health or typed API errors. The architecture does not use generic fabricated fallback values to make workflows succeed.
