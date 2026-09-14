# ADR 003 — RDF projection, file-backed foundation

**Status:** Accepted

Canonical application objects are authoritative for the running Python foundation and can be projected to RDF. SOSA/PROV-O/QUDT are reused where appropriate.

A mandatory triple store is deferred. This keeps deterministic tests and local reproduction lightweight while preserving a migration path to a graph service.
