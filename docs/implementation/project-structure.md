# Project structure

The repository is a modular Python/TypeScript monorepo. The important top-level areas are:

```text
.
├── config/                    Machine-readable source configuration
├── data/                      Local/generated data boundary (runtime artefacts are not source)
├── docs/                      Technical/research documentation and ADRs
├── frontend/                  React + TypeScript + MapLibre dashboard
├── knowledge/                 Project ontology, SHACL shapes and SPARQL queries
├── scripts/                   Explicit acquisition, evaluation and validation entry points
├── src/berlin_urban_intelligence/
│   ├── adapters/              Provider-specific access/parsing
│   ├── agents/                Domain and aggregation agents
│   ├── api/                   FastAPI application
│   ├── energy/                Forecast evaluation/workflow/persistence
│   ├── knowledge/             RDF projection implementation
│   ├── orchestrator/          Deterministic workflows and integrated assessment
│   ├── runtime/               Live/reference acquisition and persistence
│   ├── scenario_engine/       Scenario contracts and transformations
│   └── shared/                Canonical contracts and cross-cutting utilities
└── tests/                     Backend automated tests
```

## `config/`

`config/sources.yaml` is the source registry. It records data-provider scope, URLs, authority, licensing/attribution, update semantics and limitations. It is configuration metadata rather than a secret store.

## `data/`

Generated snapshots are written under `data/runtime/`; generated RDF is written under `data/generated/`. These artefacts are operational outputs, not hand-maintained source datasets. See `data/README.md` and repository ignore rules before adding data.

## `knowledge/`

`knowledge/ontology/bui.ttl` defines the project ontology and `shapes.ttl` contains SHACL validation shapes. `knowledge/queries/` contains version-controlled example/operational SPARQL queries.

The Python projection logic is separate under `src/.../knowledge/` so ontology artefacts and executable graph construction can evolve with explicit tests.

## `scripts/`

Scripts are thin operational entry points:

- `refresh_live.py` — acquire live sources, persist runtime state and live RDF;
- `refresh_reference.py` — acquire reference sources and optional OSM, persist reference state/RDF;
- `evaluate_energy.py` — explicit chronological energy evaluation and one-step forecast;
- `live_smoke.py` — external-provider compatibility smoke path;
- `validate_knowledge.py` — semantic artefact validation;
- `check_production_data.py` — guard against synthetic production data paths;
- `check_secrets.py` — repository secret guard.

Business/domain logic belongs in the package, not in scripts.

## `frontend/`

The frontend is an independently built Vite application with a committed npm lockfile. `frontend/src/api.ts` defines client-side API shapes/helpers; `App.tsx` is the main dashboard surface. Production serving uses nginx and proxies API routes to the backend.

## Tests

Backend tests are under `tests/`; frontend tests are colocated in `frontend/src/` and executed with Vitest. CI also validates OpenAPI generation, ontology/knowledge artefacts and actual container startup.

## Structural rule

New code should be placed according to responsibility rather than data domain alone. Provider schema logic belongs in adapters, shared interoperability semantics in contracts, domain behavior in agents/modules, and process/CLI wiring in scripts/API. This keeps source changes from leaking across unrelated layers.
