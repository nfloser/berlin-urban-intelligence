# Deterministic orchestration

> This compatibility page is retained for existing links. The primary documentation is [architecture/components.md](architecture/components.md) and [architecture/interfaces.md](architecture/interfaces.md).

The current orchestrator uses a fixed mapping from five typed `WorkflowKind` values to ordered agent identifiers. The mapping is defined in `Orchestrator._PLANS`; it is **not** dynamically derived from `AgentDescriptor.capabilities` in version 0.1.0.

Supported workflows are:

- `urban_snapshot`
- `heat_energy`
- `mobility_exposure`
- `mobility_resilience`
- `heat_mobility_resilience`

`plan()` returns the configured agent list and records `requires_llm=false`. `execute()` queries the health of the requested domain agents, reports missing agents and derives an overall availability status. It does not calculate domain-specific numerical results and does not fabricate replacement values for unavailable domains.

`POST /api/v1/orchestrate` exposes both plan and execution results.

## Integrated assessment

`POST /api/v1/assess` is a separate domain-coordination path implemented by `IntegratedAssessmentService`. It can calculate supported Heat, Energy and Resilience scenario dimensions from explicit baselines and prerequisites. Missing dimensions are reported with explicit errors.

The assessment contract deliberately fixes `composite_score` to `null`; no cross-domain weighting model is currently implemented or claimed.

## Optional future language layer

A future language-model component may translate natural language into a typed workflow/scenario request, but it is not part of the current deterministic execution core and must not invent measurements, model metrics, source availability, routing results or scenario outcomes.
