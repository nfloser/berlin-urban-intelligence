# Scenario semantics

Scenarios are explicit hypothetical overlays. They never alter persisted observed/reference state.

Supported parameter families include extreme-heat deltas, network edge closures/penalties, energy-demand deltas and infrastructure degradation/unavailability. Scenario requests are validated before use and identify themselves as hypothetical. An `extreme_heat` scenario requires an explicit `temperature_delta_c`; an `energy_demand` scenario requires an explicit `energy_demand_delta_pct`. Supplying either delta without its matching scenario kind is also invalid.

Examples:

- applying `+3 Cel` to a measured temperature creates a `scenario` result linked to the baseline observation;
- applying an energy-demand delta transforms a validated forecast into a scenario value while preserving the forecast baseline identity;
- closing or penalizing a road edge builds a copied network view and compares the resulting route/accessibility with the baseline;
- an unavailable facility in a scenario affects accessibility analysis but does not rewrite the facility's recorded source identity.

Integrated scenario assessment does not treat any historical value as a current baseline. Heat assessment accepts only `air_temperature_2m` observations that are no more than one hour old, are not in the future and are not marked `stale` or `invalid`. Energy assessment accepts only forecasts whose interval satisfies `issued_at <= assessment_time <= valid_at`. If no qualifying baseline exists, that dimension is reported as unavailable instead of fabricating or reusing stale state.

Resilience route comparisons preserve baseline/scenario node paths and edge IDs; where stored network coordinates are available, the API also returns LineString geometries for map display.

Integrated assessments can combine multiple requested scenario dimensions, but the dimensions remain separate and no artificial city-wide score is calculated.

No scenario output is persisted back as `observed`. Scenario results retain baseline identifiers so the counterfactual can be audited.