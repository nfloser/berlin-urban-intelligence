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

The current implementation logs to a stream handler. It does not ship a metrics backend, distributed tracing collector, alerting system or dashboard for operational telemetry.

## Error handling

Errors are represented at the boundary where they can be interpreted meaningfully:

- live-source acquisition classifies source/schema/decoder/model failures into explicit error codes;
- independent source failures do not delete unrelated valid state;
- previous accepted source values can remain last-known-good while current availability becomes unavailable;
- typed request validation produces FastAPI/Pydantic validation errors;
- resilience endpoints distinguish missing prerequisites from derivation failures;
- integrated assessment records unavailable dimensions and per-dimension errors instead of failing the entire multi-domain response where possible.

The current source error codes are operational classifications, not a stable public universal exception ontology.

## Security

Current configured upstream providers are public and require no application-managed credentials. Repository CI includes a secret guard, and the backend container runs as a non-root user.

Current limitations:

- the FastAPI application does not implement authentication or authorization;
- no rate limiting is implemented in the application;
- no user/account model exists;
- persisted JSON/RDF files are trusted local deployment inputs and are not a multi-tenant storage boundary;
- public deployment requires external network/access controls appropriate to the environment.

Input validation is provided by typed Pydantic models, explicit scenario bounds and strict source parsing, but this should not be interpreted as a complete security audit.

## Privacy

The configured sources are urban/environmental/infrastructure datasets rather than personal user records. The platform nevertheless avoids logging arbitrary HTTP request bodies/query strings through its structured logging utility. A future source containing personal or sensitive data would require a new privacy/data-governance assessment before integration.

## Performance and scalability

Measured production-scale performance results are not currently available.

Known architectural characteristics:

- persisted runtime/reference/energy snapshots are loaded into process memory at API startup;
- large reference list endpoints are paginated and capped at 1000 items per request;
- resilience builds/uses an in-memory NetworkX `MultiDiGraph`;
- RDF projection is built in memory from loaded canonical state;
- the default deployment is a single backend service with no shared database/cache;
- acquisition is outside request handlers, so external-source latency does not directly determine normal API request latency.

Potential bottlenecks include large reference/network snapshots, graph algorithms, RDF materialization and serialization of large geospatial collections. These are plausible architectural limits, not measured benchmark results.

## Caching

There is no general application cache layer. Persisted snapshots effectively act as acquisition-time materialization, but request-time cache invalidation/TTL behavior is not implemented.

## Concurrency and consistency

The current design assumes a startup snapshot per backend process. If multiple backend processes load different versions of the files at different times, the repository does not provide a synchronization protocol to guarantee identical in-memory state. A future horizontally scaled deployment must define snapshot versioning/rollout consistency.

## Diagnostics

Recommended diagnostic order:

1. `/health` for process state;
2. `/ready` for loaded snapshot state;
3. `/api/v1/agents/health` for domain state;
4. `/api/v1/source-status` for live source availability/freshness;
5. operation ID + structured server logs for an individual request;
6. persisted `errors` fields/refresh command output for acquisition failures.

See [Troubleshooting](../usage/troubleshooting.md) for concrete commands.
