# Usage examples

These examples use only currently implemented HTTP contracts. They assume the backend is running on `localhost:8000`.

## Inspect system and source state

```bash
curl http://localhost:8000/api/v1/system
curl http://localhost:8000/api/v1/agents
curl http://localhost:8000/api/v1/agents/health
curl http://localhost:8000/api/v1/source-status
```

Use agent health to understand domain availability and source status to distinguish provider availability from freshness.

## Read current observations

```bash
curl "http://localhost:8000/api/v1/observations?offset=0&limit=100"
```

The maximum page size is 1000. Domain-specific views are also available:

```bash
curl http://localhost:8000/api/v1/environment
curl http://localhost:8000/api/v1/heat
curl http://localhost:8000/api/v1/mobility
curl http://localhost:8000/api/v1/energy
```

Do not assume all domains are simultaneously available.

## Inspect reference layers

```bash
curl "http://localhost:8000/api/v1/facilities?limit=100"
curl "http://localhost:8000/api/v1/climate-features?limit=100"
curl "http://localhost:8000/api/v1/transport-stops?limit=100"
curl "http://localhost:8000/api/v1/network/nodes?limit=100"
```

Collection responses for these reference endpoints include `X-Total-Count`.

## Run a deterministic workflow health check

```bash
curl -X POST http://localhost:8000/api/v1/orchestrate \
  -H "Content-Type: application/json" \
  -d '{"workflow":"mobility_resilience"}'
```

The orchestrator reports which agents belong to the fixed workflow and their health. It does not itself calculate a route or mobility metric.

## Validate a scenario

```bash
curl -X POST http://localhost:8000/api/v1/scenarios/validate \
  -H "Content-Type: application/json" \
  -d '{
    "name":"Two degree heat delta",
    "kinds":["extreme_heat"],
    "temperature_delta_c":2.0,
    "is_hypothetical":true
  }'
```

Scenario inputs are bounded by Pydantic validation and are always hypothetical.

## Run integrated heat assessment

```bash
curl -X POST http://localhost:8000/api/v1/assess \
  -H "Content-Type: application/json" \
  -d '{
    "scenario": {
      "name":"Two degree heat delta",
      "kinds":["extreme_heat"],
      "temperature_delta_c":2.0,
      "is_hypothetical":true
    }
  }'
```

If a measured `air_temperature_2m` baseline is loaded, the response contains a scenario temperature result. Otherwise the response explicitly lists the heat dimension as unavailable. `composite_score` remains `null`.

## Compare a disrupted route

This requires a persisted road network and known node identifiers:

```bash
curl -X POST http://localhost:8000/api/v1/resilience/routes/compare \
  -H "Content-Type: application/json" \
  -d '{
    "origin":"<node-id-a>",
    "destination":"<node-id-b>",
    "scenario": {
      "name":"Road closure",
      "kinds":["network_disruption"],
      "closed_network_edges":["<edge-id>"],
      "is_hypothetical":true
    }
  }'
```

A successful response includes baseline/scenario path IDs and travel-time deltas; route geometry is included when coordinate-bearing nodes are available.

## Export the semantic projection

```bash
curl http://localhost:8000/api/v1/graph > current-state.ttl
```

The exported graph reflects the state loaded by the running backend, not a new provider refresh.
