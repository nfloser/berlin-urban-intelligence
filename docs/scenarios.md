# Scenario semantics

Scenarios are explicit hypothetical overlays. They never alter persisted observed/reference state.

Supported parameter families include extreme-heat deltas, network disruptions/edge penalties, energy-demand deltas and infrastructure degradation/unavailability. A scenario is validated before use and always identifies itself as hypothetical.

Examples:

- applying `+3 Cel` to a measured temperature produces a scenario result linked to the baseline observation;
- closing a road edge builds a copied network view and compares the resulting route/accessibility with baseline;
- an unavailable facility in a scenario affects accessibility but does not change the facility's recorded source identity.

No scenario output is written back as `observed`. Scenario results must preserve baseline identifiers so that the counterfactual can be audited.
