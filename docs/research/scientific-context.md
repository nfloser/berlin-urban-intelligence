# Scientific context

Berlin Urban Intelligence is positioned as a research software platform for modular urban digital-twin integration rather than as a single-domain predictive model.

## Research problem class

The relevant problem class combines several concerns:

- heterogeneous urban data integration;
- semantic distinction between measured, modelled, forecast and hypothetical state;
- cross-domain software modularity;
- provenance and reproducibility;
- geospatial/temporal interoperability;
- source failure and data-quality transparency;
- scenario-based analytical composition; and
- extensibility across independently evolving domain capabilities.

The repository's current research contribution is primarily an executable architecture and methodology for preserving these boundaries while integrating multiple domains.

## Architectural positioning

The platform can be characterized as **agent-extensible** because domain capabilities implement a common descriptor/health boundary and can be combined by orchestration. In the current version these agents are in-process deterministic software modules. “Agent” should not be interpreted as implying autonomous language-model reasoning.

It can be characterized as **federated/modular at the domain boundary** because domains retain distinct responsibilities and source semantics, although the deployed implementation is a monorepo/single backend rather than a distributed federation of services.

It has a **semantic projection** because canonical objects can be mapped into RDF using project ontology terms plus PROV-O/SOSA-related vocabulary. The RDF layer is not currently the primary transactional data store or a deployed knowledge-graph service.

## Digital-twin interpretation

The system provides a dynamic representation of selected urban conditions and reference structures, but it does not claim exhaustive physical replication. The representation is intentionally partial and source-qualified.

The “twin” aspect is strongest where the platform links identifiable urban entities/state with current observations, modelled reference layers, network structure, provenance and explicit scenarios. It is weaker where no live/validated source exists; the platform represents that absence instead of filling it synthetically.

## Research themes supported by the implementation

The current architecture can support future studies on:

- whether explicit epistemic-state contracts reduce integration ambiguity;
- how typed agent boundaries affect extension effort and reproducibility;
- how source degradation propagates through cross-domain workflows;
- how semantic lineage can be maintained across JSON/API/RDF representations;
- how different urban-domain modules can be composed without a universal score;
- comparative orchestration approaches; and
- reproducible evaluation of cross-domain scenario workflows.

These are research directions, not findings established by the current repository.

## Related-system comparison

The repository contains an existing `docs/world-avatar-comparison.md` technical comparison that motivated some architectural concepts. Any external-system comparison should remain factual, scoped to documented architecture and supported by verifiable references before publication. Conceptual inspiration does not imply code reuse, compatibility or affiliation.

## Publication readiness

The documentation is structured so a future paper can derive material for system architecture, methodology, implementation, reproducibility, evaluation and limitations. A paper should nevertheless define a narrower research question and add empirical evaluation rather than reproducing repository documentation.

The most defensible current paper direction is architectural: agent-extensible/federated urban digital-twin integration with explicit state/provenance semantics, demonstrated on Berlin domains and evaluated through reproducibility, extension/failure experiments and selected quantitative domain experiments. Such broader evaluation is planned rather than already completed.

## Literature references

This page intentionally does not fabricate a bibliography. A future publication should add a reviewed related-work section using verified primary sources and clearly separate cited literature from claims demonstrated by this repository.
