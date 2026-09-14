# Deterministic orchestration

The orchestrator plans **and executes** workflows from typed `OrchestrationRequest` values and registered `AgentDescriptor` capabilities. Supported workflows combine domain agents without requiring an LLM.

Current workflow families include urban snapshot, heat + energy, mobility + exposure, mobility + resilience, and heat + mobility + resilience.

A plan records ordered steps and required capabilities. Execution reports each step explicitly and does not convert an unavailable domain into a fabricated success. The API exposes both plan and execution through `POST /api/v1/orchestrate`.

## Integrated assessment

`POST /api/v1/assess` uses `IntegratedAssessmentService` to evaluate explicitly requested scenario dimensions using Heat, Energy and Resilience inputs that are actually available. Each dimension retains its own state/status. Missing prerequisites are surfaced as insufficient/model-unavailable/derivation failures rather than replaced with defaults.

The assessment deliberately has no synthetic `composite_score`. Combining dimensions into a single policy score would require an explicit and defendable weighting model and would otherwise hide uncertainty.

## Optional language interpretation

Language-model use, if added, belongs outside the deterministic core. An LLM may translate human language into a typed workflow/scenario request, but it must not invent sensor values, source availability, model performance, routing outcomes or scenario results.