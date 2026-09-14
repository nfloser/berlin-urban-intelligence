# Data architecture overview

Berlin Urban Intelligence treats data integration as a lifecycle with explicit boundaries:

```text
source -> acquisition -> parsing/validation -> canonicalization -> persisted snapshot -> analysis -> API/RDF/UI
```

The platform does not maintain one undifferentiated city-state object. Three stores separate current runtime state, slow-changing reference state and evaluated energy forecasts.

## Lifecycle stages

### 1. Source registration

`config/sources.yaml` records source identity, provider, role/domain, reference/API URL where applicable, authority classification, licence/attribution, expected update cadence, coverage and known limitations. This registry describes source boundaries; it is not a live health store.

### 2. Acquisition

Live acquisition is coordinated by `RefreshCoordinator`; reference acquisition is coordinated separately; energy input is supplied explicitly to the evaluation CLI. Provider network I/O is not hidden inside API requests.

### 3. Provider-specific parsing

Adapters under `src/berlin_urban_intelligence/adapters/` contain assumptions about external schemas, missing-value conventions and provider transport. Schema changes therefore fail at a defined boundary rather than silently altering domain behavior.

### 4. Canonicalization

Accepted data crosses domain boundaries as canonical contracts. Values retain epistemic state, quality, timestamps, units, spatial reference and provenance where applicable.

### 5. Persistence

| Class | Store | Typical content |
|---|---|---|
| current/live | `data/runtime/state.json` | observations, mobility summary, source runtime status |
| reference/model | `data/runtime/reference.json` | facilities, climate features, stops, network topology |
| evaluated predictive | `data/runtime/energy.json` | evaluation metric and matching forecast artefacts |

Generated RDF is written under `data/generated/`; it is a semantic projection rather than the canonical persistence mechanism.

### 6. Analysis

Domain agents and scenario services consume canonical objects. Resilience analysis uses reference network/facility state; integrated assessment can combine available domain calculations but preserves dimensions independently.

### 7. Presentation

FastAPI exposes typed JSON/text views and the frontend consumes those responses. Missing data remains visible as unavailable/null/degraded state rather than a fabricated client-side measurement.

## Update cadence separation

The architecture intentionally separates cadences:

- Berlin air quality, DWD and VBB GTFS-Realtime: current/live refresh;
- hospitals, fire stations, official climate layers and static VBB stops: reference refresh;
- OSM road topology: optional reference acquisition;
- energy: explicit evaluation/forecast run against a selected publication.

A deployment that needs periodic updates must schedule the appropriate commands outside the API process.

## Failure isolation

Live source attempts are independent. A failed source receives an error code and unavailable transport status; valid values from other sources are retained. When a prior snapshot exists, last-known-good values can be retained for the failed source while their freshness continues to age.

Reference refresh uses the same principle by source/category. It does not replace an independently failed reference layer with fabricated data.

## Provenance and lineage

Source provenance travels with canonical values instead of being inferred from endpoint or filename. The RDF projection additionally expresses `prov:wasDerivedFrom` and `prov:wasGeneratedBy` relationships. Energy dataset fingerprints strengthen lineage between evaluation and forecast artefacts.

Detailed pages:

- [Data sources](data-sources.md)
- [Data model](data-model.md)
- [Data processing](data-processing.md)
- [Data quality](data-quality.md)
- [Provenance](provenance.md)
