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

## Frontend

The repository commits `frontend/package-lock.json`, so reproducible installation uses `npm ci`:

```bash
cd frontend
npm ci
npm test
npm run build
npm run dev
```

The production frontend container serves the Vite build through nginx and proxies API paths to the backend according to `frontend/nginx.conf`.

## Docker Compose

```bash
docker compose config
docker compose run --rm refresh
docker compose up --build backend frontend
```

Runtime artefacts are written under `data/runtime` / `data/generated` and are not committed as source data.

The API loads persisted runtime/reference/energy state at process startup. After replacing persisted state files in a long-running deployment, restart/reload the backend process so requests see the new snapshot; provider acquisition is intentionally not hidden inside request handlers.

## CI deployment smoke

The permanent CI pipeline:

1. validates Compose configuration;
2. builds the backend image;
3. builds the frontend image;
4. starts the composed backend/frontend stack;
5. waits for `http://127.0.0.1:8000/health`;
6. verifies the frontend at `http://127.0.0.1:8080/`;
7. verifies the nginx-proxied `http://127.0.0.1:8080/health` route.

This verifies more than image buildability: the composed services must actually start and answer HTTP requests.

Currently registered production sources are public and require no secrets. Future credentials must be supplied through deployment configuration and must never be committed.