# ADR 001 — Modular monorepo

**Status:** Accepted

Use one repository for the integration platform while preserving domain modules and typed boundaries.

The historical prototypes differ in maturity and stack. Runtime coupling to six repositories would make reproducibility and contract evolution unnecessarily fragile. A monorepo provides one CI and one versioned contract surface without requiring agent implementations to become tightly coupled.
