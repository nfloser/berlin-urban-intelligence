# Structured observability

Berlin Urban Intelligence uses low-cardinality JSON operation events to make principal runtime boundaries auditable without logging provider payloads, request bodies, query strings or per-record data. This is an application logging baseline, not a metrics/tracing backend or an SLA-monitoring product.

## Safe context contract

`shared/observability.py` is the authoritative formatter/operation primitive. The structured context allow-list is intentionally small:

| Field | Meaning |
|---|---|
| `operation_id` | Correlation identifier for one request or background operation group. |
| `agent` | Stable agent/component identifier, not user input. |
| `source` | Stable source/snapshot/calculation identifier, not a URL or payload. |
| `error_state` | Safe failure classification; operation observation uses the exception class name only. |
| `duration_ms` | Wall-clock duration measured at the operation boundary. |
| `http_method` | Optional HTTP method when explicitly supplied by an HTTP boundary. |
| `http_path` | Optional route path when explicitly supplied by an HTTP boundary. |
| `http_status` | Optional response status when explicitly supplied by an HTTP boundary. |

Unknown context keys are discarded. Raw exception messages and tracebacks are not serialized by the JSON formatter because third-party/provider exceptions can contain URLs or secret-like remote context.

## Stable operation events

### `api_request`

Emitted once by the FastAPI request middleware. The API operation ID is returned to the caller as `X-Operation-Id`. HTTP failures are represented by a normalized `HTTP_<status>` state; unhandled failures use `UNHANDLED_EXCEPTION`.

Resilience route/accessibility calls already execute synchronously inside this HTTP operation boundary, so the API request event is the route-operation timing boundary rather than adding a duplicate per-edge/per-node route log. Route/scenario result payloads are never copied into the log.

### `source_refresh`

Emitted once for each authoritative live-source acquisition attempt (Berlin air quality, DWD and VBB) rather than once per observation/vehicle/station. All source attempts in the same `RefreshCoordinator.refresh()` cycle share one generated `operation_id`, allowing a refresh cycle to be reconstructed while preserving per-source success/failure and duration.

The structured `error_state` is a safe exception class. Domain-normalized provider states such as `SCHEMA_CHANGED` or `SOURCE_UNAVAILABLE` remain authoritative in persisted `SourceRuntimeStatus`; the log deliberately does not copy arbitrary exception text.

### `snapshot_reload`

Emitted only when a persisted snapshot is initially loaded, changes, or transitions to a missing state. An unchanged file-identity check emits no event, preventing one log line per HTTP request when nothing changed.

The `source` field uses a stable `snapshot:<name>` identifier. The operation can inherit a caller-provided ID; otherwise it receives an independent UUID. Invalid replacement files still preserve last-known-good state exactly as before.

### `derivation_refresh`

Emitted once around a complete `DerivedRefreshCoordinator.refresh()` call. It covers topology replacement, no-change decisions and dependency-aware incremental execution as one derivation operation rather than logging every derived record.

### `scenario_calculation`

Emitted once around each explicit temperature or energy-demand scenario transformation. `source` identifies the calculation kind (`temperature_delta` or `energy_demand_delta`) and `agent` identifies the responsible domain. Callers that already own an operation ID can pass it through; standalone/background calculations receive an independent UUID.

## Correlation semantics

There is no hidden global request context.

- API requests own the UUID returned as `X-Operation-Id`.
- A background live refresh owns one UUID shared by the source attempts in that refresh cycle.
- Derivation refreshes and standalone scenario calculations generate their own UUIDs unless an explicit caller ID is provided.
- Snapshot reloads can inherit an explicit caller ID but otherwise use their own operation ID.

This makes correlation explicit and testable and avoids accidental cross-request context leakage in worker threads/processes. A future tracing backend may propagate IDs more broadly, but it must preserve these security and cardinality constraints.

## Failure semantics

Operation observation re-raises exceptions unchanged after logging a safe event; observability must not alter control flow or turn failures into success. Components that already implement partial-failure semantics continue to catch errors at their normal boundary after the event has been emitted.

For example, `RefreshCoordinator` still records source-specific availability/error status and preserves last-known-good observations. `ReloadingSnapshot` still rejects an invalid replacement and retains its previous validated state.

## Noise and cardinality policy

Do not add structured logs inside loops over observations, features, stops, graph edges or predictions. Prefer one event per externally meaningful operation. Do not use raw URLs, entity IDs with unbounded cardinality, request parameters, payload fragments or exception messages as structured fields.

## Verification

`tests/test_operation_observability.py` verifies:

- success and failure events contain operation IDs and durations;
- raw exception messages do not enter structured operation context;
- changed snapshot reloads emit an event;
- unchanged snapshots do not emit repeated events; and
- invalid reload attempts record a safe error type while retaining existing reload semantics.

Existing refresh, derivation and scenario suites continue to verify domain behavior after instrumentation. Protected CI additionally runs the security logging-redaction contract from #18, ensuring broader operation logging cannot bypass the formatter allow-list.
