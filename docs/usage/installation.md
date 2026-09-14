# Installation

## Requirements

Minimum backend requirement:

- Python 3.12 or newer.
- Git for repository checkout.

Additional tools depend on the workflow:

- Node.js 22 is the version used by CI for frontend development/builds.
- Docker with Compose is required for the composed deployment path.
- Internet access is required only for live/reference acquisition or remote energy input, not for deterministic unit tests.

## Clone

```bash
git clone https://github.com/nfloser/berlin-urban-intelligence.git
cd berlin-urban-intelligence
```

## Backend development environment

### Linux/macOS

```bash
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -e ".[dev,live]"
```

### Windows PowerShell

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -e ".[dev,live]"
```

The `live` extra supplies GTFS-Realtime decoding. Install the optional OSM extra only when road-network acquisition is required:

```bash
pip install -e ".[osm]"
```

or combine extras for development:

```bash
pip install -e ".[dev,live,osm]"
```

## Validate the backend installation

The deterministic repository verification commands are:

```bash
ruff format --check src tests scripts
ruff check src tests scripts
mypy src/berlin_urban_intelligence
pytest --cov=berlin_urban_intelligence --cov-report=term-missing
python scripts/validate_knowledge.py
python scripts/check_production_data.py
python scripts/check_secrets.py
```

These checks are the backend portion of CI and do not require live provider availability.

## Frontend installation

```bash
cd frontend
npm ci --no-audit --no-fund
npm test
npm run build
```

`npm ci` is the reproducible installation path verified in CI because the repository commits `package-lock.json`.

Start the development frontend with:

```bash
npm run dev
```

## Docker installation path

No local Python or Node environment is required to run the composed images if Docker is available:

```bash
docker compose config
docker compose build backend frontend
```

The backend image uses Python 3.12 and runs as a non-root user. The frontend production image serves the built Vite application through nginx.

## Generated directories

Refresh/evaluation commands create or update files under:

```text
data/runtime/
data/generated/
```

These are generated operational artefacts. Do not treat them as hand-maintained source files or silently commit provider datasets without checking repository policy/licensing.

## External-source access

The current configured public sources do not require credentials. Provider access can still fail because of network, maintenance or upstream schema changes; such failures are not resolved by adding fabricated local values.

Continue with [Quickstart](quickstart.md).
