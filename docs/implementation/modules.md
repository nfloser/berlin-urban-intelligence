# Modules

This page maps implementation modules to architectural responsibilities.

## Adapters

`adapters/` contains provider-specific boundaries:

- `berlin_air_quality.py` — Berlin LQI HTTP payload parsing;
- `dwd.py` — DWD 10-minute meteorology acquisition/parsing;
- `vbb.py` — VBB GTFS-Realtime acquisition/decoding boundary;
- `vbb_static.py` — static GTFS reference processing;
- `berlin_wfs.py` — generic Berlin WFS access;
- `osm_network.py` — optional OSM road-network acquisition/normalization;
- `stromnetz_berlin.py` — explicit energy CSV parsing.

Adapters should not make cross-domain policy decisions. Their responsibility is source access, validation and normalization into the next typed boundary.

## Agents

`agents/` contains `BaseAgent` and Live State, Mobility, Exposure, Heat, Energy and Resilience agents. Agents define `AgentDescriptor` metadata and health behavior. They encapsulate domain semantics rather than network transport.

## Shared

`shared/contracts.py` is the most important interoperability module. Other shared modules cover temporal/spatial utilities, source registry/status, dependency tracking and structured observability.

Changes to shared contracts have cross-domain impact and require coordinated tests/documentation.

## Runtime

`runtime/state.py` and `runtime/reference.py` define persisted snapshot models/stores. `runtime/refresh.py` coordinates current sources. `reference_refresh.py` handles WFS reference layers, while `reference_acquisition.py` coordinates the broader reference process including static GTFS and optional OSM.

## Energy

`energy/pipeline.py` contains leakage-safe feature construction/evaluation/next-step forecasting. `energy/workflow.py` converts evaluated results into artefacts accepted by the Energy Agent; `energy/state.py` persists evaluation/forecast state.

The forecasting pipeline is deterministic for the current candidate configuration, including `random_state=0` for histogram gradient boosting.

## Resilience

Resilience functionality currently lives primarily in `agents/resilience.py`. It provides network construction, shortest paths, route comparison, facility/network snapping and accessibility. NetworkX `MultiDiGraph` preserves parallel edges.

## Scenario engine

`scenario_engine/models.py` defines immutable bounded scenarios. `engine.py` contains deterministic transformations for supported temperature and energy-demand deltas. Network/facility scenario effects are applied by the Resilience Agent.

## Orchestration

`orchestrator/engine.py` defines supported workflow kinds and fixed agent mappings. `assessment.py` coordinates scenario calculations across Heat, Energy and Resilience without aggregating them into a composite score.

## Knowledge

`knowledge/graph.py` projects canonical objects into RDF. The executable graph code references ontology namespaces but the version-controlled ontology/SHACL files live at repository root under `knowledge/ontology/`.

## API

`api/app.py` owns FastAPI lifecycle, state loading, agent assembly, HTTP routes and request-operation logging. Provider clients are not instantiated in request handlers.

## Frontend

The frontend is intentionally outside the Python package. It consumes the HTTP API and should not duplicate provider access or authoritative domain calculations.

## Change impact

When modifying a module, evaluate adjacent contracts:

- adapter change -> source docs, parsing tests, provenance/quality behavior;
- contract change -> all producer/consumer tests, API types, RDF projection and docs;
- agent change -> health semantics, API/domain docs and scenario/orchestration behavior;
- persistence change -> startup/reproducibility/deployment docs;
- API change -> frontend types/tests, OpenAPI and interface docs;
- analytical method change -> evaluation methodology/metrics/reproducibility docs.
