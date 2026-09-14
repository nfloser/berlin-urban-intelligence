# Troubleshooting

## `/ready` reports `reference_state: false` although `reference.json` exists

The API loads runtime/reference/energy snapshots at application startup and does not watch files for changes. If `reference.json` was generated after the backend started, restart/reload the backend.

Docker Compose:

```bash
docker compose restart backend
```

Then verify:

```bash
curl http://localhost:8000/ready
```

Also confirm the file exists inside the container volume:

```bash
docker compose exec backend sh -lc 'ls -lh /app/data/runtime/'
```

`BUI_REFERENCE_STATE` may be unset; that is valid because the application has a default `/app/data/runtime/reference.json` path in the container layout.

## `/ready` returns HTTP 503

The current readiness rule requires at least runtime **or** reference state. Run a refresh command and restart the backend if it was already running:

```bash
docker compose run --rm refresh
docker compose restart backend
```

Reference-only readiness can be established by generating reference state before backend startup.

## An agent is unavailable while the API is healthy

`/health` only indicates that the API process is running. Domain health is separate. Inspect:

```bash
curl http://localhost:8000/api/v1/agents/health
curl http://localhost:8000/api/v1/source-status
```

Energy is expected to be unavailable until a validated Berlin-scoped evaluation/forecast state exists. Resilience is expected to be unavailable without a network snapshot.

## Live refresh returns exit code 2

`refresh_live.py` returns 0 when at least one tracked live source is available and 2 when none are available. Inspect the printed per-source availability/freshness/error values. External outage or schema change is not automatically a repository defect.

## Reference refresh returns exit code 2

`refresh_reference.py` returns 2 when `ReferenceState.errors` is non-empty. It can still persist valid data from successful sources and retain previous valid data for an independently failed source. Inspect the printed `source=<id> error=<code>` lines.

## OSM acquisition cannot start

Install the optional dependency:

```bash
pip install -e ".[osm]"
```

Then run `refresh_reference.py --with-osm`. Speed imputation remains disabled unless explicitly enabled.

## Energy evaluation refuses the CSV

The energy parser is intentionally strict. Check:

- exact timestamp and value column names;
- delimiter and source timezone;
- duplicate/non-monotonic timestamps;
- missing/non-finite values;
- local-file `--source-url` provenance;
- remote URL uses the verified `www.stromnetz.berlin` domain.

Do not work around schema errors by renaming unknown columns without first inspecting their semantics and units.

## Route/accessibility requests fail

Common causes:

- no OSM/reference network was acquired;
- supplied node/edge IDs are not present in the loaded snapshot;
- scenario closure disconnects the route;
- facilities cannot be snapped within the configured maximum distance.

`/api/v1/resilience/accessibility` returns 409 when network/facility prerequisites are absent. Calculation errors are returned as 422 derivation failures.

## Frontend loads but API calls fail

For Docker Compose, confirm backend health and nginx proxy behavior:

```bash
curl http://localhost:8000/health
curl http://localhost:8080/health
```

For Vite development mode, inspect the configured proxy in `frontend/vite.config.ts` and ensure the backend is running on the expected port.

## Frontend data looks stale after refresh

Restart the backend after replacing persisted state. Refreshing the browser does not make the backend reload its startup snapshots.

## Tests pass but a live-source workflow fails

This is possible by design. Deterministic tests avoid relying on third-party provider uptime. Live-source smoke workflows separately detect provider outages and schema incompatibilities. Investigate whether the provider contract changed before modifying deterministic fixtures.

## Logs and correlation

API responses include `X-Operation-Id`. Structured backend logs use JSON records containing the operation ID and duration/error state. Use this ID to correlate a reported HTTP operation with server logs.
