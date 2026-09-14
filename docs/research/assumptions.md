# Assumptions

This page records assumptions that affect correctness or interpretation. Assumptions should be revisited when sources, use cases or architecture change.

## Data assumptions

1. **Source identity is meaningful.** Provider/dataset URLs and identifiers recorded in the registry/provenance refer to the intended source scope at acquisition time.
2. **Provider timestamps are usable according to documented semantics.** The platform normalizes timezone handling but cannot independently prove upstream clock accuracy.
3. **Missing is not zero.** Unless a provider explicitly defines otherwise, absent values/updates are not interpreted as normal or zero state.
4. **Authority is scoped.** An authoritative facility-location dataset is authoritative for the documented identity/location purpose, not automatically for real-time operations.
5. **Source resolution bounds interpretation.** The platform does not infer finer spatial/temporal precision than the provider supports.

## Temporal assumptions

6. **Snapshot operation is acceptable for current workflows.** The platform serves explicit persisted snapshots rather than a streaming event state.
7. **Freshness thresholds are application choices.** The current two-hour air-quality, one-hour DWD and fifteen-minute VBB thresholds are reasonable operational defaults for the implemented research UI, not provider SLAs.
8. **API startup load is acceptable.** State replacement can require restart/reload; clients are expected to tolerate snapshot semantics.

## Spatial assumptions

9. **EPSG:4326 is suitable for interchange.** Metric Berlin calculations explicitly transform to a projected CRS.
10. **EPSG:25833 is appropriate for current Berlin metric calculations.** A different geography could require a different projected CRS.
11. **Nearest-node snapping is an approximation.** Geometric proximity is used where no explicit facility/network access relation exists; it does not prove operational access.

## Energy assumptions

12. **Input schema is inspected.** Timestamp/value columns and units are supplied explicitly rather than inferred from ambiguous headings.
13. **Chronological holdout is a valid first evaluation boundary.** It avoids random leakage but does not replace repeated/nested temporal validation for stronger scientific claims.
14. **Regular cadence is required for next-step forecast timestamp derivation.** Irregular series are rejected for this step.
15. **Dataset fingerprint represents the evaluated content.** It binds model evidence to the canonicalized input snapshot but is not a replacement for archiving/licensing the source data.
16. **The configured Stromnetz publication is interpreted only within its documented network-level scope.** It is not assumed to equal total Berlin electricity demand.

## Mobility and resilience assumptions

17. **GTFS-Realtime update absence is ambiguous.** It can reflect coverage/publication behavior rather than absence of disruption.
18. **Network travel-time attributes are analytical inputs, not guaranteed live travel times.** Optional OSM speed imputation is a model assumption.
19. **Scenario edge penalties/closures represent hypothetical interventions/disruptions.** They are not probabilities or calibrated event models.

## Architecture assumptions

20. **Canonical typed contracts are the shared semantic boundary.** Cross-domain components should not depend on untyped provider payloads.
21. **In-process agents are sufficient for version 0.1.0.** Distribution is deferred until semantics are stable enough to justify transport complexity.
22. **Deterministic orchestration is preferable for current reproducibility.** Human-language interpretation can be layered above typed requests later.
23. **No universal composite score is defensible without an explicit validated weighting model.** Dimensions remain separate.
24. **Partial state is preferable to fabricated completeness.** Unavailable domains are allowed and expected.

## Operational assumptions

25. **Current public providers require no project-managed credentials.** This can change and must be documented if a source later requires authentication.
26. **Generated state files fit in process memory for current research workloads.** This has not been validated at arbitrary city-scale volumes.
27. **Single-backend snapshot consistency is sufficient.** Multi-process/distributed consistency is not implemented or claimed.

## Review trigger

An assumption should be promoted to an explicit requirement, ADR or evaluated hypothesis when a new use case depends critically on it. If an assumption becomes false, documentation and affected implementation/tests should be updated rather than silently preserving the old interpretation.
