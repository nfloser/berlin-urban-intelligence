# Scenario semantics

Scenarios must be hypothetical and name their kinds. extreme_heat requires temperature_delta_c in [-20,20]; energy_demand requires energy_demand_delta_pct in [-100,500]. Edge penalties must be between 1 and 100. Network changes require network_disruption; facility changes require infrastructure_degradation.

POST `/api/v1/assessments` accepts `{ "scenario": { "name": "Heat +3", "kinds": ["extreme_heat"], "temperature_delta_c": 3 } }`. Heat uses a measured baseline at most one hour old; energy requires a forecast whose validity interval includes the assessment time. A scenario result identifies its baseline and never overwrites it. A temperature delta is arithmetic sensitivity analysis, not a forecast of causal urban heating.

POST `/api/v1/routes` accepts origin, destination and an optional scenario. Invalid or disconnected routes return a structured 404. Network/infrastructure assessment additionally requires origin_node and actual persisted facilities and nodes. A network closure copies the graph before editing it.
