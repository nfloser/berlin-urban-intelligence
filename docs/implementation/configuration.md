# Configuration

Configuration is intentionally small in version 0.1.0. Source metadata is stored in YAML, persisted-state locations can be overridden by environment variables, and operational acquisition/evaluation choices are explicit CLI arguments.

## Environment variables

The API reads the following variables:

| Variable | Purpose | Required | Default |
|---|---|---:|---|
| `BUI_RUNTIME_STATE` | Runtime snapshot path. | No | `data/runtime/state.json` relative to repository/application root; `/app/data/runtime/state.json` in the container environment. |
| `BUI_REFERENCE_STATE` | Reference snapshot path. | No | `data/runtime/reference.json`. |
| `BUI_ENERGY_STATE` | Energy evaluation/forecast snapshot path. | No | `data/runtime/energy.json`. |

No provider credentials are required by the currently configured public sources. Do not add real secrets to `.env.example`, YAML configuration or source files.

`BUI_LOG_LEVEL` is **not** an implemented environment-variable interface in the current code and therefore should not be documented as active configuration unless the logging implementation is changed to read it.

## Source registry

`config/sources.yaml` records static source metadata including IDs, providers, datasets, domains, URLs, authority, licence/attribution, update cadence, coverage and limitations.

Agent `source_dependencies` refer to these source IDs. When adding or renaming a source, update the registry, agent descriptor, relevant tests and source documentation together.

## Live refresh CLI

```bash
python scripts/refresh_live.py \
  --state data/runtime/state.json \
  --rdf data/generated/latest.ttl
```

Both arguments are optional and the shown paths are defaults. The script performs network I/O and has no synthetic fallback.

## Reference refresh CLI

```bash
python scripts/refresh_reference.py [options]
```

Important options:

| Option | Default / effect |
|---|---|
| `--state` | `data/runtime/reference.json` |
| `--rdf` | `data/generated/reference.ttl` |
| `--skip-gtfs` | Disable static VBB GTFS acquisition. |
| `--with-osm` | Enable optional OSM road acquisition. |
| `--place` | `Berlin, Germany` OSMnx place query. |
| `--network-type` | `drive`. |
| `--allow-osmnx-speed-imputation` | Explicit opt-in to derived/imputed speeds before travel-time calculation. |

OSM acquisition requires installation of the optional `osm` dependency extra.

## Energy evaluation CLI

The energy command deliberately requires source schema configuration rather than guessing columns:

```bash
python scripts/evaluate_energy.py \
  --input <local-csv-or-verified-url> \
  --dataset "<inspected dataset title>" \
  --timestamp-column "<column>" \
  --value-column "<column>" \
  [--source-url <url-for-local-copy>] \
  [--unit MW] \
  [--delimiter ';'] \
  [--source-timezone Europe/Berlin] \
  [--seasonal-lag 96] \
  [--test-fraction 0.2] \
  [--state data/runtime/energy.json]
```

Remote input is accepted only from `https://www.stromnetz.berlin/`. A local copy requires `--source-url` so provenance is not lost.

## Frontend configuration

The development frontend uses Vite. Production nginx configuration in `frontend/nginx.conf` proxies API paths to the backend container. The Docker Compose frontend is exposed on host port `8080`; backend is exposed on `8000`.

## Docker Compose configuration

The committed `docker-compose.yml` sets `BUI_RUNTIME_STATE=/app/data/runtime/state.json` for backend/refresh and mounts `./data:/app/data`. The backend Docker image itself also defaults this variable. Reference and energy paths use application defaults unless explicitly overridden.

## Feature/configuration boundaries

Some behavior is code-level configuration in version 0.1.0 rather than environment configuration: live freshness thresholds, selected Climate Analysis WFS layer names, supported orchestrator workflow mappings and energy candidate-model hyperparameters. Changes to these values are methodological/architectural changes and should be tested and documented, not treated as deployment-only tuning.
