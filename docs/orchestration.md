# Deterministic orchestration

The orchestrator plans workflows from typed `OrchestrationRequest` values and registered `AgentDescriptor` capabilities. Supported workflows combine domain agents without requiring an LLM.

The plan records ordered steps and required capabilities. Execution reports each step explicitly and does not treat an unavailable domain as a fabricated success.

Language-model use, if added, belongs outside this deterministic core: an LLM may interpret a human request into a typed workflow request, but it must not invent sensor values, source availability, model performance or scenario outputs.

Cross-domain results are reported by dimension. The platform intentionally avoids a universal city/resilience score because such a score would require an explicit, defendable weighting model and could otherwise hide uncertainty.
