# ADR 002 — Typed in-process contracts first

**Status:** Accepted

Agents exchange Pydantic canonical models inside the current deployment. Every important value carries epistemic state, quality and provenance.

Distributed messaging can be added later, but adding transport complexity before stable semantics would obscure errors. Contract versioning is therefore established before remote-agent protocols.
