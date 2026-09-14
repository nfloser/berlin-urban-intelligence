# Scenario semantics

Scenarios are explicit hypothetical overlays. They never alter persisted observed/reference state.

Supported parameter families include extreme-heat deltas, network edge closures/penalties, energy-demand deltas and infrastructure degradation/unavailability. Scenario requests are validated before use and identify themselves as hypothetical.

Examples:

- applying `+3 Cel` to a measured temperature creates a `scenario` result linked to the baseline observation;
- applying an energy-demand delta transforms a validated forecast into a scenario value while preserving the forecast baseline identity;
- closing or penalizing a road edge builds a copied network view and compares the resulting route/accessibility with the baseline;
- an unavailable facility in a scenario affects accessibility analysis but does not rewrite the facility's recorded source identity.

Resilience route comparisons preserve baseline/scenario node paths and edge IDs; where stored network coordinates are available, the API also returns LineString geometries for map display.

Integrated assessments can combine multiple requested scenario dimensions, but the dimensions remain separate and no artificial city-wide score is calculated.

No scenario output is persisted back as `observed`. Scenario results retain baseline identifiers so the counterfactual can be audited.