# Development setup

Use the same major runtime versions as CI when possible: Python 3.12 and Node 22.

## Backend

```bash
python3.12 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev,live]"
```

Windows PowerShell:

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -e ".[dev,live]"
```

Add `osm` only when working on optional road-network acquisition:

```bash
pip install -e ".[dev,live,osm]"
```

## Frontend

```bash
cd frontend
npm ci --no-audit --no-fund
```

## Recommended local verification

Before committing a backend change:

```bash
ruff format --check src tests scripts
ruff check src tests scripts
mypy src/berlin_urban_intelligence
pytest --cov=berlin_urban_intelligence --cov-report=term-missing
python scripts/validate_knowledge.py
python scripts/check_production_data.py
python scripts/check_secrets.py
```

Before committing a frontend change:

```bash
cd frontend
npm test
npm run build
```

Changes affecting deployment should additionally run:

```bash
docker compose config
docker compose build backend frontend
```

## External-provider development

Do not make ordinary tests depend on public provider uptime. Add deterministic fixtures that reproduce the relevant provider shape, then use the separate live/reference smoke paths to check current provider compatibility.

Synthetic fixtures belong under `tests/` and are test data only. Production code must not read those fixtures as operational Berlin state.

## Generated artefacts

Running acquisition/evaluation writes generated data under `data/runtime/` and `data/generated/`. Review ignore rules and source licensing before committing any generated data.

## Documentation during development

For every change, check whether it affects:

- architecture/component responsibility;
- a canonical contract or API shape;
- configuration or CLI behavior;
- source semantics, provenance or quality;
- persistence/data flow;
- test/evaluation methodology;
- reproducibility commands; or
- a documented limitation/roadmap item.

Update the corresponding documentation in the same logical change when practical.
