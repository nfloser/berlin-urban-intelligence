# Reproducibility

This document defines what must be captured to reproduce the current software behavior and the energy experiment.

## Software environment

Verified CI baseline:

- Python 3.12;
- Node 22 for frontend;
- dependencies declared in `pyproject.toml`;
- frontend dependency graph installed with `npm ci` from `frontend/package-lock.json`;
- Docker Compose configuration committed in the repository.

For an exact historical reproduction, record the repository commit plus the resolved Python environment/container image digest because Python dependencies are constrained by compatible ranges rather than a fully pinned transitive lock.

## Deterministic software reproduction

From a clean clone:

```bash
python3.12 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev,live]"
ruff format --check src tests scripts
ruff check src tests scripts
mypy src/berlin_urban_intelligence
pytest --cov=berlin_urban_intelligence --cov-report=term-missing
python scripts/validate_knowledge.py
python scripts/check_production_data.py
python scripts/check_secrets.py
```

Frontend:

```bash
cd frontend
npm ci --no-audit --no-fund
npm test
npm run build
```

Container verification:

```bash
docker compose config
docker compose build backend frontend
docker compose up -d backend frontend
```

Then verify `/health`, the frontend root and proxied `/health` as CI does.

## Live acquisition reproduction

Live source results are time-dependent and cannot be reproduced exactly from provider calls alone after the fact. To reproduce a specific observed snapshot, retain the generated runtime state and source metadata or the exact upstream source responses where licensing permits.

Command:

```bash
python scripts/refresh_live.py \
  --state data/runtime/state.json \
  --rdf data/generated/latest.ttl
```

Record:

- repository commit;
- execution timestamp/timezone;
- generated `state.json` and RDF;
- source status/error output;
- resolved dependency environment.

## Reference acquisition reproduction

```bash
python scripts/refresh_reference.py
```

For OSM:

```bash
pip install -e ".[osm]"
python scripts/refresh_reference.py --with-osm
```

Record whether `--skip-gtfs`, `--with-osm`, `--place`, `--network-type` or `--allow-osmnx-speed-imputation` were used. These choices materially change the reference state.

Upstream WFS/GTFS/OSM data can evolve, so exact historical reproduction also requires archived source artefacts/snapshots where possible.

## Energy experiment reproduction

Required inputs:

- exact source file/URL and dataset title;
- file checksum or archived immutable copy where permitted;
- timestamp/value column names;
- unit, delimiter and source timezone;
- seasonal lag and test fraction;
- repository commit and resolved environment.

Execute:

```bash
python scripts/evaluate_energy.py \
  --input <input> \
  --source-url <url-if-local> \
  --dataset "<dataset-title>" \
  --timestamp-column "<timestamp-column>" \
  --value-column "<value-column>" \
  --unit MW \
  --delimiter ';' \
  --source-timezone Europe/Berlin \
  --seasonal-lag 96 \
  --test-fraction 0.2 \
  --state data/runtime/energy.json
```

The emitted dataset fingerprint is part of the reproduction record. The gradient-boosting candidate uses `random_state=0`; other current candidates are deterministic under the supplied data/configuration.

Expected artefact: `energy.json` containing selected `ModelMetric` plus a matching one-step forecast artefact. Exact metric/forecast values depend on the supplied dataset and therefore are not hard-coded in documentation.

## API reproduction

Set state paths if non-default:

```bash
export BUI_RUNTIME_STATE=/path/to/state.json
export BUI_REFERENCE_STATE=/path/to/reference.json
export BUI_ENERGY_STATE=/path/to/energy.json
uvicorn berlin_urban_intelligence.api.app:app --host 0.0.0.0 --port 8000
```

The state is loaded at startup. Record the exact files supplied to reproduce API responses.

## Hardware

No special accelerator/GPU is required by the current implementation. Hardware is not presently part of correctness evaluation. If performance benchmarks are introduced, CPU/memory/storage/platform details must be recorded.

## Randomness

The energy histogram gradient boosting model fixes `random_state=0`. Current routing, scenario transformations and deterministic orchestrator do not require random seeds. Future stochastic models must document and expose seeds.

## What cannot be reconstructed from repository commit alone

- historical values from mutable public endpoints;
- provider outages/latency at an earlier time;
- an energy experiment when the exact input publication/file is not retained;
- exact Python transitive package versions unless the resolved environment/image was captured.

These limitations should be reported in any publication that depends on a historical run.
