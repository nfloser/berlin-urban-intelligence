# Orchestration

POST `/api/v1/orchestrate` accepts one of urban_snapshot, heat_energy, mobility_exposure, mobility_resilience or heat_mobility_resilience. It returns a deterministic plan and the availability of participating agents. This endpoint does not imply the execution of a numerical causal model.

POST `/api/v1/assessments` executes supported explicit scenario dimensions. Results list unavailable dimensions and errors; no composite score is produced. The dependency graph propagates staleness to descendants, and invalid cyclic changes are rejected without destroying existing dependencies.
