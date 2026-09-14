# Agent contracts

| Agent | Inputs | Outputs and limits |
|---|---|---|
| Live State | domain health | availability aggregation, no scientific score |
| Mobility | VBB realtime messages | feed coverage and delay summary, not a complete timetable |
| Exposure | official Berlin LQI payload | provisional index grades, not pollutant concentrations |
| Heat | DWD records and official climate GeoJSON | measured meteorology and separately labelled model features |
| Energy | evaluation and matching forecast artifact | fingerprint-checked forecast; no invented Berlin series |
| Resilience | explicit road edges, nodes and facilities | routes, travel-time accessibility and disruption comparison |

To extend the platform, implement BaseAgent, publish an AgentDescriptor, preserve canonical provenance and quality, add deterministic input and failure fixtures, register the agent in the API assembly and add the required workflow dependencies. Registration currently requires a code change; there is no dynamic plugin discovery service.
