# Berlin Urban Intelligence

**Version 0.1.0 — integrated research foundation**

Implementation and remaining v1.0 acceptance gates are recorded in [docs/integration.md](docs/integration.md). This release provides a working API/dashboard integration; it is not a claim that every masterprompt requirement or live source has passed acceptance.

Berlin Urban Intelligence is an agent-extensible urban intelligence and digital-twin research platform for Berlin. It connects independently testable domain agents through shared contracts, explicit provenance, semantic relationships, deterministic orchestration and scenario semantics so that cross-domain urban analysis can be built without hiding uncertainty or fabricating missing data.

The project is inspired by architectural principles demonstrated by **The World Avatar**—specialised agents, semantic interoperability, provenance and composable derivations—but is an independent, deliberately smaller implementation for one city. It is not affiliated with The World Avatar or the University of Cambridge.

## Why this repository exists

The standalone repositories in this portfolio remain useful historical/reference prototypes. This repository is the maintained integration layer: reusable ideas are assessed and reimplemented behind one common model rather than copied wholesale or loaded as runtime dependencies.

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
                       Orchestrator
                               |
                    FastAPI + Dashboard

               + semantic RDF projection
               + dependency/freshness model
```

## Current capabilities

| Area | v0.1 status |
|---|---|
| Shared contracts | Implemented: versioned observations, forecasts, derived/scenario values, network and facility contracts |
| Provenance / quality | Implemented as first-class fields and RDF PROV-O lineage |
| Time / units / CRS | UTC enforcement, explicit numeric units and EPSG:25833 metric-distance helper |
| Live State Agent | Implemented health aggregation with graceful degradation |
| Mobility Agent | VBB GTFS-Realtime decoding and delay snapshot semantics |
| Exposure Agent | Official Berlin LQI ingestion with provisional-quality handling |
| Heat Agent | DWD 10-minute Berlin meteorology ingestion |
| Energy Agent | Contract/evaluation boundary implemented; **Berlin forecast unavailable by design** until valid Berlin data/model exists |
| Resilience Agent | NetworkX routing/accessibility plus immutable disruption overlays |
| Scenario Engine | Explicit hypothetical heat/network/energy/infrastructure parameters |
| Orchestrator | Deterministic typed workflow planning; no LLM required |
| Knowledge layer | RDF/SOSA/PROV-O project vocabulary, SHACL artefacts and semantic export |
| Runtime state | Atomic canonical JSON + RDF artefacts; per-source availability/freshness |
| API | Versioned FastAPI surface and OpenAPI |
| Dashboard | React/TypeScript status, observations, provenance, sources and orchestration view |
| CI | Deterministic backend/frontend/container gates plus separate live-source smoke workflow |

A missing source remains missing. There is no production fallback to generated sensor values, temperatures, delays, pollution, demand, model metrics or infrastructure state.

## Verified source boundaries

The initial live path uses authoritative providers where available:

- **Berliner Luftgütemessnetz** — official LQI/air-quality REST data. Current automatic values remain explicitly provisional. Licence: DL-DE-BY-2.0.
- **VBB** — official GTFS static data and GTFS-Realtime feed. VBB publishes its open datasets under CC BY 4.0. Absence of realtime updates is not interpreted as normal service.
- **DWD Open Data / CDC** — 10-minute meteorological observations; v0.1 defaults to Berlin-Tempelhof station `00433`. UTC timestamps and `-999` missing values are handled explicitly.
- **Berlin Climate Analysis 2022** — official Berlin WFS is registered as `official_modelled` source material, not as live observation. GeoJSON normalization and explicit reference acquisition are implemented; provider completeness must be checked on acquisition.
- **OpenStreetMap** — available through an optional, explicit OSMnx acquisition path under ODbL.

The UCI household energy dataset used in the standalone Energy Twin is in Sceaux, France. This platform records it only as a methodological research reference and never presents it as Berlin energy state.

See [`docs/data-sources.md`](docs/data-sources.md) and [`config/sources.yaml`](config/sources.yaml).

## Epistemic state is part of the data

Every important value can communicate what it *is*, not only its numeric value:

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

For example, DWD temperature is `observed`; Berlin Climate Analysis is `official_modelled`; a future evaluated energy prediction is `forecast`; a calculated accessibility change is `derived`; and a manually imposed +3 °C perturbation is `scenario`.

## Run deterministic tests

Python 3.11+ is required.

```bash
python -m venv .venv
source .venv/bin/activate
# Windows PowerShell: .venv\Scripts\Activate.ps1
pip install -e ".[dev,live]"
pytest
python scripts/validate_knowledge.py
python scripts/check_production_data.py
python scripts/check_secrets.py
```

Normal tests do not depend on external services.

## Acquire real current data

Network acquisition is explicit:

```bash
python scripts/refresh_live.py
```

The command independently attempts Berlin air quality, DWD meteorology and VBB GTFS-Realtime, writes canonical state to `data/runtime/state.json`, writes RDF to `data/generated/latest.ttl`, and reports each source's availability/freshness. If a source fails, it is recorded as unavailable; no synthetic replacement is created.

## Start API

```bash
uvicorn berlin_urban_intelligence.api.app:app --host 0.0.0.0 --port 8000
```

Useful endpoints:

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
GET  /api/v1/resilience
GET  /api/v1/graph
POST /api/v1/scenarios/validate
POST /api/v1/orchestrate
POST /api/v1/assessments
POST /api/v1/routes
GET  /api/v1/reference
GET  /api/v1/map
```

OpenAPI is available at `http://localhost:8000/docs`.

## Dashboard

```bash
cd frontend
npm install
npm test
npm run dev
```

The dashboard shows agent/source health, latest canonical observations, epistemic state, quality, provenance and deterministic orchestration plans. It intentionally renders an explicit empty state when real data are unavailable.

## Docker

```bash
docker compose run --rm refresh
docker compose up --build backend frontend
```

Then open:

- Dashboard: `http://localhost:8080`
- API/OpenAPI: `http://localhost:8000/docs`

Generated runtime data remain on the local `./data` mount and are not committed.

## Testing and validation

The deterministic suite covers contracts, temporal semantics, CRS-aware distance, source registry/status, Berlin LQI and DWD adapters, agents, runtime persistence, RDF mapping, ontology artefacts, dependency staleness, scenarios, routing/accessibility, orchestration, API contracts and source-shape → agent → semantic integration.

GitHub Actions additionally runs formatting/linting, strict typing, frontend tests/build, OpenAPI generation, Docker/Compose checks and image builds. Live-source smoke tests are separate and scheduled/manual so third-party outages do not destabilise deterministic CI.

## Repository structure

```text
src/berlin_urban_intelligence/
  adapters/           verified external-source boundaries
  agents/             domain agents
  api/                FastAPI v1 surface
  knowledge/          RDF projection code
  orchestrator/       deterministic capability planning
  runtime/            refresh + persisted state
  scenario_engine/    explicit hypothetical overlays
  shared/             contracts, provenance, time, CRS, quality, dependencies
knowledge/
  ontology/           project vocabulary + SHACL shapes
  queries/            SPARQL artefacts
config/
  sources.yaml        machine-readable source registry
frontend/             React / TypeScript research UI
docs/                 architecture, methods, limitations, ADRs, migrations
scripts/              refresh and validation commands
tests/                deterministic unit/integration tests
.github/workflows/     deterministic CI + live source smoke
```

## Prototype migration

The standalone repositories remain reference prototypes. Current integration reuses canonical adapter and agent patterns without importing those repositories at runtime. Their current completion status has not been re-audited in this revision; older chat summaries must not be treated as current repository evidence. See [docs/integration.md](docs/integration.md).

## Scientific boundaries

This project does **not** claim a universal Berlin health/resilience score, causal effects from simple correlation, street-level precision unsupported by a source, complete critical-infrastructure truth from OSM, or forecast performance that has not been calculated. See [`docs/limitations.md`](docs/limitations.md).

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

## Licence note

No project-source licence has been added automatically. External datasets retain their own licences and attribution requirements as recorded in the source registry and documentation.
