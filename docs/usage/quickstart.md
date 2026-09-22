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

The running API validates and hot-reloads atomic replacements of runtime, reference, energy, derived and traffic-disruption snapshots before requests. Invalid replacements do not displace the previous validated in-process state; reload diagnostics are exposed through `/api/v1/system`. A normal refresh therefore does not require a backend restart.

## Verify data presence

Useful endpoints after refresh:

```bash
curl http://localhost:8000/api/v1/source-status
curl http://localhost:8000/api/v1/observations
curl http://localhost:8000/api/v1/facilities
curl http://localhost:8000/api/v1/climate-features
curl 'http://localhost:8000/api/v1/traffic/disruptions?active_only=true&limit=250'
curl 'http://localhost:8000/api/v1/map/search?q=Alexanderplatz&limit=8'
```

Reference endpoints can legitimately be empty when the corresponding acquisition was not run or failed. An empty result is not automatically a software error.

## Use the dashboard map

The first dashboard viewport is map-first. Use the floating route planner to search persisted Berlin critical facilities or VBB stops, or select any origin/destination directly on the map. Search results and map clicks are resolved to the nearest persisted road-network node and the route is calculated automatically. The current text search is intentionally limited to persisted reference places; arbitrary-address geocoding is not yet claimed.

The normal route API keeps its baseline path for auditability and separately returns the effective route after current VIZ disruption constraints:

- **baseline** — no active VIZ disruption changes the route;
- **disrupted** — an official disruption intersects the route, but no supported travel-time penalty is inferred;
- **rerouted** — an explicit active VIZ `Vollsperrung` closes one or more matched route edges and an alternative exists;
- **blocked** — an explicit active full closure removes the route and no alternative exists.

The map renders official VIZ disruptions independently of facilities, VBB stops, climate features and automatically monitored critical routes. Full closures are red; other disruptions are amber. The route planner shows effective ETA/distance and automatically fits the map to the effective path. These features provide a familiar navigation workflow, but they do not claim Google Maps-equivalent geocoding, turn-by-turn instructions or live congestion-speed coverage.

The lower research controls still provide an explicit hypothetical network-disruption comparison. This remains separate from source-backed VIZ observations: scenario closures are labelled hypothetical and never mutate the observed/reference baseline.

## Energy workflow

Energy state is not created by `refresh_live.py`. It requires an explicit inspected input dataset:

```bash
python scripts/evaluate_energy.py --help
```

Supply exact upstream dataset, timestamp/value column names and provenance as described in [configuration](configuration.md) and [evaluation](../evaluation/methodology.md).

## Expected behavior

The system may be partially available. For example, live air-quality/weather state can be available while energy is unavailable because no evaluated Berlin energy artefact has been created. This is expected and preferable to synthetic completion.
