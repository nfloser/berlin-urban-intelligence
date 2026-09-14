# ADR 004 — Scenarios never mutate observed state

**Status:** Accepted

Hypothetical changes use dedicated scenario contracts and copied/overlay network state. They cannot overwrite observations or reference truth.

This protects scientific traceability: a user can always distinguish what was measured/provided from what was imposed as a counterfactual.
