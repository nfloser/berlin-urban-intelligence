# Deployment

## Backend

Python 3.12 or newer is required.

```bash
python -m venv .venv
source .venv/bin/activate
# Windows PowerShell: .venv\Scripts\Activate.ps1
pip install -e '.[dev,live]'
python scripts/refresh_live.py
uvicorn berlin_urban_intelligence.api.app:app --host 0.0.0.0 --port 8000
```

Reference acquisition is separate because official model/facility/transit/network layers change at a different cadence from live observations:

```bash
python scripts/refresh_reference.py
```

Optional OSM road acquisition requires the `osm` extra:

```bash
pip install -e '.[osm]'
python scripts/refresh_reference.py --with-osm
```

Energy evaluation/forecast generation is an explicit operation and persists to `data/runtime/energy.json`; see `scripts/evaluate_energy.py --help`.

## Persisted-state visibility

Provider acquisition is intentionally outside normal API request handlers. The API reads persisted runtime, reference, energy and derived snapshots through validated stores.

A running backend checks snapshot file identity before requests. When a persisted file changes, the corresponding snapshot is reparsed and a valid replacement becomes visible without restarting the process. Runtime/reference/energy changes rebuild the affected in-process agents/orchestrator; derived state is reloaded for derived/API inspection. If a replacement is missing or invalid, the last validated in-process value is retained and `/api/v1/system` exposes reload diagnostics.

This hot-reload mechanism is a single-process deployment boundary. The repository does not provide a coordination protocol that guarantees multiple backend processes switch to the same file version atomically.

## Frontend

The repository commits `frontend/package-lock.json`, so reproducible installation uses `npm ci`:

```bash
cd frontend
npm ci
npm test
npm run build
npm run dev
```

The production frontend container serves the Vite build through nginx and proxies API paths to the backend according to `frontend/nginx.conf`. The running dashboard polls the system snapshot token so validated persisted-state changes become visible without a manual browser reload.

## Docker Compose

The Compose topology contains three services: backend, frontend and the persistent live `refresh` worker.

```bash
docker compose config
docker compose up --build
```

The refresh worker runs `scripts/refresh_live.py --interval-seconds` with a default interval of 300 seconds, configurable through `BUI_REFRESH_INTERVAL_SECONDS`. Reference acquisition and energy evaluation remain separate explicit operations because they have different source/evaluation cadences.

If only the API/UI are desired for inspection of already persisted state:

```bash
docker compose up --build backend frontend
```

Runtime artefacts are written under `data/runtime` / `data/generated` and are not committed as source data.

## CI deployment and browser acceptance

The permanent CI pipeline:

1. validates Compose configuration;
2. builds the backend image;
3. creates an explicit deterministic acceptance-only reference snapshot;
4. builds the frontend image;
5. starts the composed backend/frontend stack;
6. waits for `http://127.0.0.1:8000/health`;
7. verifies the frontend at `http://127.0.0.1:8080/` and the nginx-proxied `/health` route; and
8. runs Playwright through nginx against the real FastAPI/persisted-state stack.

Browser acceptance currently covers dashboard startup/degradation semantics, viewport-backed map loading and canonical object inspection, fail-closed viewport reload behavior, and baseline-vs-disruption routing. Additional populated inspector acceptance is tracked in issue #15.

This verifies more than image buildability, but it does not prove live provider availability, real Berlin road-network completeness, horizontally scaled consistency, production performance or security hardening. Those gates are tracked in [verification.md](verification.md).

Currently registered production sources are public and require no secrets. Future credentials must be supplied through deployment configuration and must never be committed. Public/shared deployments require external access controls unless application-level authentication is intentionally implemented later.
