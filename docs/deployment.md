# Deployment

From the repository root, install Python 3.11+ dependencies with `pip install -e ".[dev,live]"`. Run `python scripts/refresh_live.py`, then `uvicorn berlin_urban_intelligence.api.app:app --host 0.0.0.0 --port 8000`. In frontend, run `npm ci` and `npm run dev`. Vite proxies /api to the backend.

For containers: `docker compose run --rm refresh`, then `docker compose up --build backend frontend`. The dashboard is on port 8080, the API on 8000. The host data directory must be writable by container UID 10001; provision directory ownership for that service account on Linux. Do not make directories globally writable.

BUI_DATA_DIR selects the snapshot directory; BUI_RUNTIME_STATE overrides the live-state file; BUI_SOURCE_REGISTRY selects source metadata. The live, reference and energy files should be refreshed by a single writer per file. The current filesystem store is intended for a single-host research deployment.

/health is process liveness. /ready returns 503 unless at least one domain has available data; it is not an all-domain certification. The API has no authentication or tenant isolation. Put authenticated infrastructure in front of it before exposing it as a shared service. Docker execution was not available in the implementation workspace; image builds are a CI gate.
