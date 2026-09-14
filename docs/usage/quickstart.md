# Quickstart

This quickstart provides two paths: a deterministic software verification path and a live-data demonstration path.

## A. Verify the repository without external providers

After [installation](installation.md):

```bash
pytest
cd frontend
npm test
npm run build
```

Expected result: backend tests pass, frontend tests pass and Vite produces a production build. CI additionally runs formatting, linting, strict typing, semantic validation, secret/production-data guards and container startup checks.

## B. Run a live snapshot and dashboard

Live acquisition requires network access to the configured public providers.

### Docker Compose

From the repository root:

```bash
docker compose run --rm refresh
docker compose up --build backend frontend
```

The refresh service writes the current runtime snapshot into the host-mounted `data/` directory. The backend is available on:

```text
http://localhost:8000
```

and the dashboard on:

```text
http://localhost:8080
```

Check service state:

```bash
curl http://localhost:8000/health
curl http://localhost:8000/ready
curl http://localhost:8000/api/v1/system
curl http://localhost:8000/api/v1/agents/health
```

A successful `/health` means the process is running. `/ready` additionally reports whether runtime and/or reference snapshots were loaded.

### Local Python

```bash
python scripts/refresh_live.py
uvicorn berlin_urban_intelligence.api.app:app --host 0.0.0.0 --port 8000
```

Then open the API or start the frontend development server separately.

## Add reference layers

The default reference refresh acquires official WFS layers and static VBB GTFS:

```bash
python scripts/refresh_reference.py
```

Optional OSM routing topology requires the OSM extra and explicit opt-in:

```bash
pip install -e ".[osm]"
python scripts/refresh_reference.py --with-osm
```

If you generate or replace reference/runtime/energy state **after** the API process has already started, restart/reload the backend. State is loaded at application startup; the API does not automatically watch the files.

With Docker Compose:

```bash
docker compose restart backend
```

This startup-snapshot behavior is a common reason for `/ready` showing `reference_state: false` even though `data/runtime/reference.json` exists on disk.

## Verify data presence

Useful endpoints after refresh:

```bash
curl http://localhost:8000/api/v1/source-status
curl http://localhost:8000/api/v1/observations
curl http://localhost:8000/api/v1/facilities
curl http://localhost:8000/api/v1/climate-features
```

Reference endpoints can legitimately be empty when the corresponding acquisition was not run or failed. An empty result is not automatically a software error.

## Use the dashboard map

The map shows only persisted, WGS84 reference features returned by the API. Its legend provides independent switches for critical facilities, VBB stops and official climate features; switching a layer changes only its visibility, never the underlying state. The colours identify the layer type rather than a risk level or live condition.

A map can therefore remain visually unchanged after a workflow or heat assessment: workflows expose agent availability, and a heat assessment returns an explicitly hypothetical cross-domain result. Neither action mutates the observed/reference baseline or fabricates a spatial impact layer.

## Energy workflow

Energy state is not created by `refresh_live.py`. It requires an explicit inspected input dataset:

```bash
python scripts/evaluate_energy.py --help
```

Supply exact upstream dataset, timestamp/value column names and provenance as described in [configuration](configuration.md) and [evaluation](../evaluation/methodology.md).

## Expected behavior

The system may be partially available. For example, live air-quality/weather state can be available while energy is unavailable because no evaluated Berlin energy artefact has been created. This is expected and preferable to synthetic completion.
