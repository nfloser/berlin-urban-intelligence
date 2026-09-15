# Deterministic orchestration

> This compatibility page is retained for existing links. The primary documentation is [architecture/components.md](architecture/components.md) and [architecture/interfaces.md](architecture/interfaces.md).

The orchestrator supports five typed `WorkflowKind` families, but it does not hard-code concrete agent identifiers into those workflows. `Orchestrator._WORKFLOW_CAPABILITIES` declares the capabilities each workflow requires, and `AgentRegistry` resolves those capabilities to registered agents while preserving validated agent-dependency order.

Supported workflows are:

- `urban_snapshot`
- `heat_energy`
- `mobility_exposure`
- `mobility_resilience`
- `heat_mobility_resilience`

`plan()` returns the resolved agent identifiers, required capabilities and any missing capabilities, and records `requires_llm=false`. If more than one registered agent provides the same required capability, planning fails explicitly rather than selecting one ambiguously. Registry validation rejects missing agent dependencies and dependency cycles.

`execute()` queries the health of the resolved agents and derives an overall availability status. It does not calculate domain-specific numerical results and does not fabricate replacement values for unavailable domains. Workflow-specific numerical analysis remains the responsibility of domain components or explicit coordination services.

`POST /api/v1/orchestrate` exposes both plan and execution results.

## Current boundary limitation

Capability resolution and dependency ordering are registry-driven, but not every cross-agent coordination path is yet expressed exclusively through that boundary. In particular, the current `LiveStateAgent` still receives other agent instances and invokes their `health()` methods directly. Issue #13 tracks moving that aggregation across a typed orchestration/service boundary and completing real-agent descriptor metadata.

## Integrated assessment

`POST /api/v1/assess` is a separate domain-coordination path implemented by `IntegratedAssessmentService`. It can calculate supported Heat, Energy and Resilience scenario dimensions from explicit current/valid baselines and prerequisites. Missing dimensions are reported with explicit errors.

The assessment contract deliberately fixes `composite_score` to `null`; no cross-domain weighting model is currently implemented or claimed.

## Optional future language layer

A future language-model component may translate natural language into a typed workflow/scenario request, but it is not part of the current deterministic execution core and must not invent measurements, model metrics, source availability, routing results or scenario outcomes.
