# Deployment

## Local backend

Use Python 3.12.

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e '.[dev,live]'
python scripts/refresh_live.py
uvicorn berlin_urban_intelligence.api.app:app --host 0.0.0.0 --port 8000
```

Reference acquisition is a separate operation because static/reference layers change at a different cadence from live observations.

## Frontend

```bash
cd frontend
npm install
npm test
npm run build
npm run dev
```

The production container serves the Vite build through nginx and proxies API paths to the backend according to `frontend/nginx.conf`.

## Compose

```bash
docker compose config
docker compose run --rm refresh
docker compose up --build backend frontend
```

Runtime artefacts are written under `data/runtime` / `data/generated` and are not committed as source data.

The API serves persisted state loaded by the application process. After replacing state files in a long-running deployment, restart/reload the backend unless the deployment explicitly adds a reload mechanism; do not assume hot reload of persisted snapshots.

Secrets are never required for the currently registered public sources and must not be committed if future sources introduce credentials.
