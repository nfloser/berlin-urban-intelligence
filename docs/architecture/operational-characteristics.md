# Operational characteristics

This page consolidates cross-cutting runtime concerns that are not owned by a single domain agent.

## Logging and observability

`shared/observability.py` provides JSON structured logging. Records include UTC timestamp, level, logger and message plus an allow-listed set of context fields:

- `operation_id`
- `agent`
- `source`
- `error_state`
- `duration_ms`
- `http_method`
- `http_path`
- `http_status`

FastAPI middleware creates a UUID operation ID per request, returns it as `X-Operation-Id` and records request completion/error duration. Unknown context keys are ignored by the formatter, which helps prevent arbitrary payload/query content from entering platform logs.

The current implementation logs to a stream handler. It does not ship a metrics backend, distributed tracing collector, alerting system or operational telemetry dashboard. Structured coverage beyond API requests is incomplete; source refresh, snapshot reload, derivation and scenario-operation observability is tracked in issue #19.

## Error handling

Errors are represented at the boundary where they can be interpreted meaningfully:

- live-source acquisition classifies source/schema/decoder/model failures into explicit error codes;
- independent source failures do not delete unrelated valid state;
- previous accepted source values can remain last-known-good while current availability becomes unavailable;
- invalid replacement snapshot files do not replace the previous validated in-process snapshot;
- typed request validation produces FastAPI/Pydantic validation errors;
- resilience endpoints distinguish missing prerequisites from derivation failures;
- integrated assessment records unavailable dimensions and per-dimension errors instead of failing the entire multi-domain response where possible.

The current source error codes are operational classifications, not a stable public universal exception ontology.

## Security

Current configured upstream providers are public and require no application-managed credentials. Repository CI includes a conservative secret guard, and the backend container runs as a non-root user.

Current limitations:

- the FastAPI application does not implement authentication or authorization;
- no rate limiting is implemented in the application;
- no user/account model exists;
- persisted JSON/RDF files are trusted local deployment inputs and are not a multi-tenant storage boundary;
- no dependency-vulnerability audit or complete security verification baseline is currently a release gate;
- public/shared deployment requires external network/access controls appropriate to the environment.

Input validation is provided by typed Pydantic models, explicit scenario bounds and strict source parsing, but this is not a complete security audit. Issue #18 owns the security-baseline gap.

## Privacy

The configured sources are urban/environmental/infrastructure datasets rather than personal user records. The platform nevertheless avoids logging arbitrary HTTP request bodies/query strings through its structured logging utility. A future source containing personal or sensitive data would require a new privacy/data-governance assessment before integration.

## Snapshot reload and consistency

Runtime, reference, energy and derived states are initially loaded into process memory and then monitored through file identity. Before API requests, the snapshot controller checks for persisted-file changes; only changed files are reparsed. Valid replacements become visible without process restart, while invalid/missing replacements preserve the last validated in-process value and expose diagnostics through `/api/v1/system`.

This does not provide distributed consistency. Multiple backend processes can detect and load persisted-file versions at different instants, and the repository currently has no coordinated snapshot-version rollout protocol for horizontally scaled deployment.

## Performance and scalability

Measured production-scale performance results are not currently available.

Known architectural characteristics:

- runtime/reference/energy/derived snapshots are held in process memory after validation;
- unchanged snapshots are not reparsed on every request;
- ordinary reference list endpoints are paginated and capped at 1000 items per request;
- the analytical map uses bbox-bounded `/api/v1/map/reference` projection with a configurable per-layer cap and explicit truncation metadata rather than requesting whole reference snapshots;
- resilience builds/uses an in-memory NetworkX `MultiDiGraph`;
- RDF projection is built in memory from loaded canonical state;
- the default deployment is a single backend service with no shared database/cache;
- acquisition is outside request handlers, so external-source latency does not directly determine normal API request latency.

Potential bottlenecks include large reference/network snapshots, graph algorithms, RDF materialization and serialization of large geospatial collections. These are plausible architectural limits, not measured benchmark results. Issue #17 tracks reproducible performance/load evidence.

## Caching

There is no general application cache layer. Persisted snapshots act as acquisition-time materialization, and unchanged file-backed state remains in memory. There is no general request-response cache/TTL layer.

## Diagnostics

Recommended diagnostic order:

1. `/health` for process state;
2. `/ready` for loaded snapshot state;
3. `/api/v1/system` for persisted-state timestamps and snapshot-reload diagnostics;
4. `/api/v1/agents/health` for domain state;
5. `/api/v1/source-status` for live source availability/freshness;
6. operation ID + structured server logs for an individual request;
7. persisted `errors` fields/refresh command output for acquisition failures.

See [Troubleshooting](../usage/troubleshooting.md) for concrete commands and [verification.md](../verification.md) for the repository-wide evidence status.
