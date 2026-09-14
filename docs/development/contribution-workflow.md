# Contribution workflow

The repository should evolve in small, reviewable changes that keep tests and documentation synchronized.

## Recommended workflow

```text
Issue / research question
        ↓
Expected behavior and boundary
        ↓
Test or reproducible check
        ↓
Implementation
        ↓
Validation
        ↓
Documentation
        ↓
Logical commit
```

## Before implementation

Identify which boundary owns the change: adapter, canonical contract, agent/domain logic, persistence, scenario/orchestration, API, frontend or research/evaluation method.

For source-related work, verify provider semantics rather than inferring them from field names. For model-related work, define the evaluation evidence needed before implementation is described as an improvement.

## Tests first where behavior changes

Prefer a failing test that describes the intended behavior before changing implementation. Provider network compatibility should be represented by deterministic fixtures for normal CI and verified separately by smoke workflows.

## Documentation impact

Every change should consider whether it changes:

- project scope or limitations;
- architecture/component responsibility;
- source metadata/licence/quality semantics;
- canonical contracts or data flow;
- configuration/CLI/environment variables;
- API request/response behavior;
- test/evaluation methodology;
- deployment/reproducibility;
- extension contracts or roadmap status.

Documentation-only changes should still be grounded in current code/configuration/tests.

## Commits

Prefer logical, incremental commit messages such as:

```text
test: define source freshness failure behavior
fix: preserve last-known-good mobility snapshot
docs: document source-status semantics
feat: add validated reference source adapter
```

Avoid accumulating unrelated implementation and documentation changes into one final repository-wide commit. When code, tests and documentation are one coherent behavior change, keeping them in the same commit is appropriate.

## Pull requests / review

A review should be able to answer:

1. What observable behavior changed?
2. Which contract/source assumption justifies it?
3. How is it tested?
4. What happens on missing/malformed/unavailable data?
5. Did epistemic state, quality or provenance change?
6. Did public API/configuration change?
7. Is any new performance/scientific claim supported by evidence?
8. Which documentation was updated?

## Breaking changes

Changes to canonical semantics, contract version, persisted-state schema, API behavior or source identity can be breaking even if Python function signatures remain compatible. Such changes should be explicit, documented and accompanied by migration guidance where persisted/user-facing state is affected.

## Release process

A formal release/tagging process is not currently defined in the repository. Until one is implemented, do not describe a specific release automation, semantic-versioning guarantee or publication pipeline as existing. The package/repository version should remain internally consistent when intentional releases are made.
