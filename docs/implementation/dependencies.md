# Dependencies

Dependency ranges are defined in `pyproject.toml`; frontend versions are locked through `frontend/package-lock.json`.

## Runtime baseline

Python **3.12 or newer** is required by the package metadata and CI currently verifies Python 3.12.

Core Python dependencies include:

| Dependency | Role |
|---|---|
| FastAPI / Uvicorn | HTTP API and ASGI serving. |
| Pydantic | Canonical contracts, persistence/request validation. |
| httpx | External HTTP acquisition. |
| NetworkX | Resilience routing/accessibility graph calculations. |
| NumPy / pandas | Energy time-series processing and evaluation. |
| scikit-learn | Ridge and histogram gradient-boosting forecasting candidates and metrics. |
| pyproj | CRS validation/transformation. |
| Shapely | Geometry validation/repair/spatial operations. |
| RDFLib | RDF knowledge projection. |
| PyYAML | Source-registry loading. |

The project uses bounded major-version ranges rather than unbounded dependencies; see `pyproject.toml` for the exact current constraints.

## Optional extras

### `live`

Installs `gtfs-realtime-bindings` required to decode the VBB GTFS-Realtime feed.

```bash
pip install -e ".[live]"
```

### `osm`

Installs OSMnx for optional OpenStreetMap network acquisition.

```bash
pip install -e ".[osm]"
```

### `dev`

Installs pytest/coverage, Ruff, strict mypy tooling and type stubs used by CI.

```bash
pip install -e ".[dev,live]"
```

## Frontend

`frontend/package.json` currently declares React, React DOM and MapLibre GL as runtime dependencies, with TypeScript, Vite, Vitest and React/Vite type/plugin packages for development. CI uses **Node 22** and reproducible installation through `npm ci` and the committed lockfile.

Do not substitute `npm install` in reproducibility instructions when the goal is to reproduce the committed dependency graph; `npm ci` is the repository's verified path.

## Container runtime

The backend image is based on `python:3.12-slim` and installs the package with the `live` extra. It runs as non-root user `appuser` (UID 10001). The frontend has its own Dockerfile and production nginx configuration.

## External services

The operational implementation depends on public provider endpoints only when acquisition commands are executed. Normal deterministic tests and normal API requests do not require provider access. This distinction allows upstream outages to be tested/observed separately from repository correctness.

## Version reproducibility

Python dependency ranges permit compatible updates rather than pinning every transitive package. Therefore an exact historical environment is best reproduced from a captured environment/container digest in addition to the repository commit if byte-for-byte dependency identity is required. The repository's CI establishes compatibility with the declared ranges, not a claim that every future compatible release is behaviorally identical.
