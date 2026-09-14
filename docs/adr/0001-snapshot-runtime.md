# ADR 0001: Explicit snapshot runtime

Status: accepted for research foundation, subject to replacement for v1.

Keep acquisition outside API requests. Persist canonical state and reconstruct agents from it. This makes the API deterministic with respect to saved inputs, exposes upstream failures and avoids network acquisition during ordinary page reads. Scenario overlays are immutable relative to these inputs.

Trade-offs: filesystem storage is single-host, per-request reconstruction has costs on large networks, and the RDF view is not a persistent shared knowledge service. PostGIS/Fuseki integration remains open. Do not label this decision as completion of those masterprompt requirements.
