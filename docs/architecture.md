# Architecture

Berlin Urban Intelligence is a modular monorepo for an agent-extensible urban digital twin. The monorepo is an integration boundary rather than a domain monolith: domain agents remain independently testable and communicate through versioned canonical contracts.

## Layers

1. **Source adapters** isolate external APIs/files and make schema assumptions explicit.
2. **Canonical contracts** carry value, unit, UTC time, CRS where spatial, epistemic state, quality and provenance.
3. **Domain agents** implement Live State, Mobility, Environmental Exposure, Urban Heat, Energy Forecasting and Resilience capabilities.
4. **Runtime/reference/energy stores** persist atomic JSON state; fast-changing state, slower reference layers and evaluated forecasts remain separate.
5. **Knowledge projection** maps canonical objects to RDF using project vocabulary plus SOSA, PROV-O and QUDT where applicable.
6. **Scenario engine** creates explicitly hypothetical values or network overlays without mutating observed/reference state.
7. **Deterministic orchestrator** plans and executes typed workflows; an LLM is not required.
8. **Integrated assessment** combines available heat, energy and resilience dimensions without inventing a composite city score.
9. **FastAPI and dashboard** expose inspectable state, provenance, reference layers and analysis results.

## Invariants

- Production paths never synthesize missing urban measurements.
- `observed`, `official_modelled`, `project_modelled`, `forecast`, `derived`, `interpolated` and `scenario` are not interchangeable.
- Numeric cross-agent values require explicit units.
- Datetimes crossing agent boundaries are timezone-aware and normalized to UTC.
- WGS84 is used for interchange; Berlin metric calculations use an explicit projected CRS, EPSG:25833 by default.
- Scenario operations use copied/overlay state and cannot rewrite the baseline.
- Source availability, freshness and last-known-good state are represented separately.
- Reference acquisition retains valid data per source when an independent reference source fails.
- Energy forecasts are accepted only when evaluation/model metadata and dataset fingerprints match.

## Runtime topology

Acquisition is explicit and separate from API serving:

- `scripts/refresh_live.py` writes `data/runtime/state.json` and live RDF.
- `scripts/refresh_reference.py` writes `data/runtime/reference.json` and reference RDF.
- `scripts/evaluate_energy.py` writes `data/runtime/energy.json` after chronological evaluation.
- the API loads persisted state at process startup and exposes it without contacting providers during normal requests;
- the frontend consumes only API outputs.

Because API state is loaded at process startup, a long-running backend must be restarted/reloaded after replacing persisted state files. This keeps request behavior deterministic and prevents hidden network acquisition inside API handlers.

External services therefore remain outside deterministic tests. A separate live-source workflow verifies current provider compatibility.