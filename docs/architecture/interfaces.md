# Interfaces

Berlin Urban Intelligence exposes interfaces at four levels: external source adapters, canonical Python contracts, persisted files and HTTP endpoints.

## Canonical Python interface

The canonical contracts in `shared/contracts.py` are the primary in-process interoperability API. Models are frozen and reject unknown fields. Contract version is currently `1.0.0`.

New domain components should exchange canonical models rather than untyped dictionaries whenever data crosses a domain boundary.

## Persistence interfaces

| Store | Default path | Contents |
|---|---|---|
| Runtime | `data/runtime/state.json` | Current observations, realtime mobility snapshot, source runtime statuses, refresh errors. |
| Reference | `data/runtime/reference.json` | Critical facilities, official-model features, transport stops, network nodes and edges, reference-refresh errors. |
| Energy | `data/runtime/energy.json` | Selected Berlin evaluation metadata and validated forecast artefacts. |
| Derived | `data/runtime/derived.json` | Derivation definitions, derived records, freshness/status and explicit upstream lineage. |

The store implementations validate data through Pydantic models and use explicit serialization rather than treating files as arbitrary JSON blobs.

## HTTP API

The FastAPI application is implemented in `src/berlin_urban_intelligence/api/app.py`. OpenAPI generation is validated in CI.

### Service and metadata

| Method | Endpoint | Purpose |
|---|---|---|
| GET | `/health` | Process liveness and version. |
| GET | `/ready` | Snapshot readiness; returns HTTP 503 when neither runtime nor reference state is loaded. |
| GET | `/api/v1/system` | System/version/contract and snapshot generation timestamps. |
| GET | `/api/v1/agents` | Agent descriptors. |
| GET | `/api/v1/agents/health` | Current domain health as seen by the loaded snapshot. |
| GET | `/api/v1/sources` | Static configured source registry. |
| GET | `/api/v1/source-status` | Runtime source availability/freshness status when runtime state exists. |

### State and domain views

| Method | Endpoint | Notes |
|---|---|---|
| GET | `/api/v1/state` | Runtime state plus reference summary, not full reference payload. |
| GET | `/api/v1/observations` | Paginated runtime observations; default 250, maximum 1000. |
| GET | `/api/v1/environment` | Exposure-agent health and LQI observations. |
| GET | `/api/v1/heat` | Heat-agent health and measured meteorological observations. |
| GET | `/api/v1/mobility` | Mobility health and current loaded summary snapshot. |
| GET | `/api/v1/energy` | Energy health, registered evaluation and forecasts. |
| GET | `/api/v1/facilities` | Paginated critical facilities with `X-Total-Count`. |
| GET | `/api/v1/climate-features` | Paginated official model features with `X-Total-Count`. |
| GET | `/api/v1/transport-stops` | Paginated transport stops with `X-Total-Count`. |
| GET | `/api/v1/network/nodes` | Paginated network nodes with `X-Total-Count`. |
| GET | `/api/v1/derived` | Persisted derivation definitions and derived records. |
| GET | `/api/v1/derived/{record_id}` | One derived record plus its derivation definition. |
| GET | `/api/v1/provenance/{record_id}` | Provenance for one persisted derived record. |
| GET | `/api/v1/dependencies/{resource_id}` | Derived dependency-DAG upstream/downstream inspection. |
| GET | `/api/v1/graph` | Current RDF/Turtle projection of validated runtime, reference, energy and derived snapshots. |
| GET | `/api/v1/knowledge/relations/{resource_id}` | Bounded incoming/outgoing RDF relationships for one canonical resource; default limit 100, maximum 500, 404 when absent. |

The semantic relation response reports `total`, `returned` and `truncated` so callers can distinguish a complete relation set from a bounded result. Each relation records direction, predicate URI, related node kind/value and literal datatype/language where applicable. This is a constrained inspection interface, not an unrestricted SPARQL endpoint.

Reference network edges are part of persisted/reference and RDF state but do not currently have a dedicated list endpoint.

### Analysis endpoints

| Method | Endpoint | Request/behavior |
|---|---|---|
| POST | `/api/v1/scenarios/validate` | Validates a typed `Scenario`; valid objects are always hypothetical. |
| POST | `/api/v1/orchestrate` | Accepts a supported workflow kind and returns deterministic plan + health execution result. |
| POST | `/api/v1/resilience/routes/compare` | Requires origin, destination and scenario; derivation failures return 422. |
| POST | `/api/v1/resilience/accessibility` | Requires persisted network/facilities; missing prerequisites return 409, derivation failures 422. |
| POST | `/api/v1/assess` | Runs supported scenario dimensions independently and reports unavailable dimensions/errors. |

## Example orchestration request

```json
{
  "workflow": "mobility_resilience"
}
```

The response contains a `plan` and `execution`. `requires_llm` is `false` in both contracts.

## Example heat scenario request

```json
{
  "scenario": {
    "name": "Heat delta +2 Cel",
    "kinds": ["extreme_heat"],
    "temperature_delta_c": 2.0,
    "is_hypothetical": true
  }
}
```

This does not change the stored temperature observation. If no measured `air_temperature_2m` baseline is loaded, the assessment reports the heat dimension as unavailable.

## Error semantics

FastAPI/Pydantic returns validation errors for malformed typed requests. Analysis endpoints additionally expose explicit error classes in response detail or assessment dimension errors, including `INSUFFICIENT_DATA`, `MODEL_UNAVAILABLE` and `DERIVATION_FAILED` in the implemented paths.

Unknown semantic resource identifiers return 404. A missing optional snapshot simply contributes no triples to the semantic projection; it is not replaced with fabricated graph data.

Provider acquisition errors are represented separately in persisted source/reference status rather than converted into HTTP provider calls during request handling.

## External source interfaces

Provider-specific HTTP/file contracts are isolated under `adapters/`. The machine-readable source boundaries, URLs, licences and limitations are listed in `config/sources.yaml` and described in [data sources](../data/data-sources.md).

## Dashboard interface

The browser client uses the HTTP API only. `frontend/src/api.ts` contains client-side TypeScript response/request shapes and helpers. The backend OpenAPI schema remains the authoritative HTTP contract; TypeScript declarations must be kept synchronized when API shapes change.
