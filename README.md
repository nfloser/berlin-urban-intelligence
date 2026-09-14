# Berlin Urban Intelligence

**Version 0.1.0 — verified integrated research platform**

Berlin Urban Intelligence is an agent-extensible urban intelligence and digital-twin research platform for Berlin. It connects independently testable domain agents through versioned canonical contracts, explicit provenance, quality and freshness semantics, semantic relationships, deterministic orchestration and explicit scenario modelling.

The project is inspired by broad architectural principles demonstrated by **The World Avatar**—specialised agents, semantic interoperability, provenance and composable derivations—but is independently implemented for Berlin. It is not affiliated with The World Avatar, Cambridge CARES or the University of Cambridge.

## Design goals

The platform is designed around a few non-negotiable rules:

- real production inputs are never replaced with fabricated urban data;
- observed, official-modelled, forecast, derived and scenario states remain distinguishable;
- source attribution, units, UTC timestamps and spatial reference are explicit;
- source availability is separate from freshness and last-known-good state;
- scenarios never overwrite the baseline state;
- cross-domain analysis remains explainable and does not collapse uncertainty into a synthetic city score;
- deterministic agent execution is the core; an LLM is not required for execution.

## Architecture

```text
verified urban sources
        |
        v
 source adapters
        |
        v
 canonical state + provenance + quality
        |
  +-----+---------+---------+---------+---------+
  |               |         |         |         |
Live State     Mobility   Exposure   Heat     Energy
  |               |         |         |         |
  +---------------+---------+----+----+---------+
                               |
                         Resilience
                               |
                     Scenario Engine
                               |
              Deterministic Orchestrator
                               |
                  FastAPI + MapLibre UI

               + semantic RDF projection
               + dependency/freshness model
               + atomic runtime/reference stores
```

The standalone portfolio repositories remain historical/reference prototypes. This repository is the maintained integration layer; reusable ideas are reimplemented behind common contracts rather than imported as runtime dependencies.

## Implemented capabilities

| Area | Status |
|---|---|
| Shared contracts | Versioned observations, forecasts, derived/scenario values, official-model features, facilities, transit stops and network contracts |
| Provenance / quality | First-class provider, dataset, source URL, timestamps, agent/model identity, licence, quality notes and RDF PROV-O lineage |
| Time / units / CRS | UTC enforcement, explicit numeric units, validated CRS/GeoJSON and EPSG:25833 metric calculations |
| Live State Agent | Cross-domain health aggregation with graceful degradation and no master score |
| Mobility Agent | VBB GTFS-Realtime decoding plus static GTFS stop/reference ingestion |
| Exposure Agent | Official Berlin LQI ingestion, including the current station-envelope API schema and provisional-quality handling |
| Heat Agent | DWD 10-minute observations plus Berlin Climate Analysis 2022 official-modelled reference features |
| Energy Agent | Berlin grid-load evaluation/forecast boundary with dataset fingerprints, chronological holdout evaluation and persisted forecasts |
| Energy models | Persistence, seasonal-naive, Ridge and HistGradientBoosting candidates; reported metrics come from real holdout predictions |
| Resilience Agent | Multi-edge NetworkX routing, accessibility, facility-to-network snapping and immutable disruption overlays |
| Reference acquisition | Berlin WFS facilities/climate, VBB static GTFS and optional OSM road-network acquisition with last-known-good retention |
| Scenario Engine | Explicit hypothetical heat, network, energy and infrastructure parameters |
| Integrated assessment | Heat, energy and resilience dimensions combined without a fabricated composite score |
| Orchestrator | Deterministic typed workflow planning **and execution**; no LLM required |
| Knowledge layer | RDF/SOSA/PROV-O/QUDT projection, ontology/SHACL artefacts and semantic export |
| Runtime state | Atomic runtime, reference and energy JSON stores plus generated RDF artefacts |
| API | Versioned FastAPI surface, OpenAPI, pagination/resource limits and operation IDs |
| Dashboard | React/TypeScript/MapLibre research UI with map layers, observations, provenance inspection, orchestration and explicit hypothetical assessment controls |
| CI | Ruff, strict mypy, pytest, ontology/knowledge validation, data/secret guards, OpenAPI, `npm ci`, frontend tests/build, Docker builds and a running Compose HTTP smoke test |

A missing source remains missing. There is no production fallback to generated temperatures, delays, pollution, energy demand, infrastructure state or model metrics.

## Data sources

The maintained source registry is [`config/sources.yaml`](config/sources.yaml). Current source boundaries include:

- **Berliner Luftgütemessnetz** — official LQI/air-quality REST data; current automatic values remain provisional. Licence: DL-DE-BY-2.0.
- **VBB** — official GTFS static data and GTFS-Realtime. Licence: CC BY 4.0.
- **DWD Open Data / CDC** — 10-minute meteorological observations; the default live path uses Berlin-Tempelhof station `00433` and preserves DWD missing-value semantics.
- **Berlin Climate Analysis 2022** — official WFS features ingested as `official_modelled`, never as live observations. Licence: DL-DE-Zero-2.0.
- **Berlin hospitals and fire stations** — official WFS facility identity/location references. Published location does not imply live operational availability.
- **OpenStreetMap** — optional Berlin road-network reference under ODbL; explicitly qualified as community-maintained rather than authoritative infrastructure truth.
- **Stromnetz Berlin** — Berlin grid-load source boundary used by the explicit energy evaluation/forecast workflow. The published network-level curve is not relabelled as total Berlin electricity demand.
- **UCI household electricity dataset** — methodology/reference only; it is one household in Sceaux, France and is never presented as Berlin state.

A live verification on **2026-09-14** successfully reached the three realtime/current sources used by `refresh_live.py`: Berlin air quality, DWD and VBB GTFS-Realtime. All three were reported `available`, and their accepted data were `valid` for freshness at that run; the smoke test produced 70 canonical observations. This is a point-in-time operational verification, not a guarantee of future provider availability.

See [`docs/data-sources.md`](docs/data-sources.md) for source semantics and limitations.

## Epistemic states

Canonical objects can explicitly communicate what kind of knowledge they represent:

```text
observed
official_modelled
project_modelled
forecast
derived
interpolated
scenario
unknown
unavailable
stale
```

For example, a DWD temperature is `observed`; a Berlin Climate Analysis feature is `official_modelled`; an evaluated energy prediction is `forecast`; an accessibility result is `derived`; and a manually imposed temperature perturbation is `scenario`.

## Requirements and deterministic tests

Python **3.12+** is required by `pyproject.toml`.

```bash
python -m venv .venv
source .venv/bin/activate
# Windows PowerShell: .venv\Scripts\Activate.ps1
pip install -e ".[dev,live]"
ruff format --check src tests scripts
ruff check src tests scripts
mypy src/berlin_urban_intelligence
pytest --cov=berlin_urban_intelligence --cov-report=term-missing
python scripts/validate_knowledge.py
python scripts/check_production_data.py
python scripts/check_secrets.py
```

Deterministic tests do not depend on external providers.

## Acquire live/current state

```bash
python scripts/refresh_live.py
```

This independently refreshes Berlin air quality, DWD meteorology and VBB GTFS-Realtime, persists canonical state to `data/runtime/state.json`, writes RDF to `data/generated/latest.ttl`, and records availability/freshness per source. A failed source does not erase unrelated valid state or trigger synthetic replacement data.

## Acquire reference layers

```bash
python scripts/refresh_reference.py
```

By default this acquires the official Berlin WFS reference layers and VBB static GTFS. OSM road-network acquisition is opt-in:

```bash
pip install -e ".[osm]"
python scripts/refresh_reference.py --with-osm
```

OSMnx speed imputation is also opt-in via `--allow-osmnx-speed-imputation` and is recorded in provenance.

## Evaluate and forecast Berlin grid-load data

The energy workflow requires explicitly inspected input columns rather than guessing an upstream schema:

```bash
python scripts/evaluate_energy.py \
  --input <stromnetz-berlin.csv-or-verified-url> \
  --dataset "<inspected dataset title>" \
  --timestamp-column "<timestamp column>" \
  --value-column "<value column>" \
  --unit MW
```

Evaluation is chronological and leakage-safe. Persistence and seasonal-naive baselines are always calculated; Ridge and HistGradientBoosting are evaluated on the same holdout. The selected candidate, metrics, dataset fingerprint and one-step forecast are persisted in `data/runtime/energy.json`.

## API

```bash
uvicorn berlin_urban_intelligence.api.app:app --host 0.0.0.0 --port 8000
```

Important endpoints include:

```text
GET  /health
GET  /ready
GET  /api/v1/system
GET  /api/v1/agents
GET  /api/v1/agents/health
GET  /api/v1/sources
GET  /api/v1/source-status
GET  /api/v1/state
GET  /api/v1/observations
GET  /api/v1/environment
GET  /api/v1/heat
GET  /api/v1/mobility
GET  /api/v1/energy
GET  /api/v1/facilities
GET  /api/v1/climate-features
GET  /api/v1/transport-stops
GET  /api/v1/network/nodes
GET  /api/v1/graph
POST /api/v1/scenarios/validate
POST /api/v1/orchestrate
POST /api/v1/resilience/routes/compare
POST /api/v1/resilience/accessibility
POST /api/v1/assess
```

OpenAPI is served at `http://localhost:8000/docs`. API responses receive a server-generated `X-Operation-Id` for request correlation.

## Dashboard

The frontend has a committed lockfile and uses reproducible installation:

```bash
cd frontend
npm ci
npm test
npm run build
npm run dev
```

The dashboard displays agent health, canonical observations, epistemic state, quality and provenance; maps official facilities, VBB stops and official climate-model features; runs deterministic orchestration workflows; and exposes explicitly hypothetical heat assessment controls. Missing API data are shown as unavailable rather than replaced with demo values.

## Docker / Compose

```bash
docker compose config
docker compose run --rm refresh
docker compose up --build backend frontend
```

Then open:

- Dashboard: `http://localhost:8080`
- API/OpenAPI: `http://localhost:8000/docs`

CI builds both images, starts the composed backend/frontend stack, verifies the backend health endpoint, verifies the frontend, and verifies the proxied `/health` route.

Generated runtime data remain under the local `./data` mount and are not committed as source data.

## Verification status

As of the 2026-09-14 release verification:

- Ruff format: pass
- Ruff lint: pass
- strict mypy: pass
- pytest + coverage execution: pass
- ontology/knowledge validation: pass
- production synthetic-data guard: pass
- secret guard: pass
- OpenAPI generation: pass
- frontend `npm ci`: pass
- frontend tests: pass
- frontend production build: pass
- Docker Compose configuration: pass
- backend image build: pass
- frontend image build: pass
- running Compose HTTP smoke: pass
- separate real live-source smoke for Berlin Air + DWD + VBB: pass

Live-provider status is intentionally kept outside deterministic CI because external outages and schema changes are valid operational conditions rather than deterministic repository failures.

## Repository structure

```text
src/berlin_urban_intelligence/
  adapters/           external-source boundaries
  agents/             domain agents
  api/                FastAPI v1 surface
  energy/             leakage-safe energy evaluation/forecast workflow
  knowledge/          RDF projection code
  orchestrator/       deterministic planning/execution + integrated assessment
  runtime/            live/reference acquisition and persisted state
  scenario_engine/    explicit hypothetical overlays
  shared/             contracts, time, CRS, provenance, quality, dependencies
knowledge/
  ontology/           project vocabulary + SHACL shapes
  queries/            SPARQL artefacts
config/
  sources.yaml        machine-readable source registry
frontend/             React / TypeScript / MapLibre research UI
docs/                 architecture, methods, limitations, ADRs, migrations
scripts/              acquisition, evaluation and validation commands
tests/                deterministic unit/integration tests
.github/workflows/     deterministic CI + separate live-source smoke
```

## Prototype migration

Migration assessments are under [`docs/prototype-migrations/`](docs/prototype-migrations/).

- Live Twin contributed patterns for semantic state, provenance, freshness and VBB/Berlin source boundaries.
- Resilience Twin contributed topology/scenario separation and accessibility-analysis patterns.
- Energy Twin contributed leakage-safe evaluation and baseline methodology, while its UCI data remains non-Berlin reference material.
- Mobility, Environmental Exposure and Urban Heat standalone repositories were bootstrap/empty at assessment time and therefore did not provide substantive code to import.

## Scientific boundaries

This project does **not** claim a universal Berlin health/resilience score, causal effects from cross-domain co-occurrence, precision unsupported by source resolution, authoritative completeness from OSM, live operational status from facility location datasets, or forecast performance that has not been calculated from held-out data.

See [`docs/limitations.md`](docs/limitations.md).

## Documentation

- [`docs/architecture.md`](docs/architecture.md)
- [`docs/agents.md`](docs/agents.md)
- [`docs/data-sources.md`](docs/data-sources.md)
- [`docs/data-model.md`](docs/data-model.md)
- [`docs/knowledge-graph.md`](docs/knowledge-graph.md)
- [`docs/provenance.md`](docs/provenance.md)
- [`docs/orchestration.md`](docs/orchestration.md)
- [`docs/scenarios.md`](docs/scenarios.md)
- [`docs/testing.md`](docs/testing.md)
- [`docs/deployment.md`](docs/deployment.md)
- [`docs/integration.md`](docs/integration.md)
- [`docs/limitations.md`](docs/limitations.md)
- [`docs/world-avatar-comparison.md`](docs/world-avatar-comparison.md)
- [`docs/adr/`](docs/adr/)
- [`docs/prototype-migrations/`](docs/prototype-migrations/)

## Licence note

No project-source licence has been added automatically. External datasets retain their own licences and attribution requirements as recorded in the source registry and documentation.