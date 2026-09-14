# Architecture

Berlin Urban Intelligence is a modular monorepo for an agent-extensible urban digital twin. The monorepo is an integration boundary, not a monolith: domain agents remain independently testable and communicate only through versioned canonical contracts.

## Layers

1. **Source adapters** isolate external APIs/files and schema assumptions.
2. **Canonical contracts** carry value, unit, UTC time, CRS where spatial, epistemic state, quality and provenance.
3. **Domain agents** implement Live State, Mobility, Environmental Exposure, Urban Heat, Energy Forecasting and Resilience capabilities.
4. **Runtime/reference stores** persist atomic JSON state. Live state and slower reference layers remain distinct.
5. **Knowledge projection** maps canonical objects to RDF using project vocabulary plus SOSA, PROV-O and QUDT terms where applicable.
6. **Scenario engine** creates explicitly hypothetical values or network overlays without mutating observed state.
7. **Deterministic orchestrator** selects capabilities from typed workflow requests. An LLM is not required for execution.
8. **FastAPI and dashboard** expose inspectable state and analysis results.

## Invariants

- Production paths never synthesize missing urban measurements.
- Observed, official-modelled, project-modelled, forecast, derived, interpolated and scenario states are not interchangeable.
- Numeric cross-agent values require explicit units.
- Datetimes crossing agent boundaries are timezone-aware and normalized to UTC.
- WGS84 is used for interchange; metric Berlin calculations use an explicit projected CRS (EPSG:25833 by default).
- A scenario operates on a copy/overlay and cannot rewrite the baseline state.
- Source failure is represented as availability/freshness/quality metadata rather than hidden fallback data.

## Runtime topology

The backend is stateless with respect to external acquisition: refresh commands write persisted state; API processes load that state and expose it. The frontend consumes only API outputs. External services therefore remain outside deterministic unit/CI tests.
