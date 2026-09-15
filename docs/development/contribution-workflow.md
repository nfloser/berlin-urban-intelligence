# Contribution workflow

The repository should evolve in small, reviewable changes that keep tests and documentation synchronized.

## Required repository workflow

Substantive work starts from current `main` and follows this sequence:

```text
Issue / research question
        ↓
Dedicated branch from current main
        ↓
Expected behavior and boundary
        ↓
Failing test or reproducible check where applicable
        ↓
Implementation + synchronized documentation
        ↓
Logical incremental commits
        ↓
Pull request linked to the issue
        ↓
Complete CI: backend + frontend + containers
        ↓
Diff/review pass and resolved conversations
        ↓
Merge into main
```

Do not intentionally develop features directly on `main`. Repository-level enforcement is defined in [`repository-governance.md`](repository-governance.md), including the exact `main` ruleset and required status checks. Until the repository owner activates that ruleset in GitHub settings, this remains a documented workflow requirement rather than a claim of technical branch protection.

## Before implementation

Identify which boundary owns the change: adapter, canonical contract, agent/domain logic, persistence, scenario/orchestration, API, frontend or research/evaluation method.

For source-related work, verify provider semantics rather than inferring them from field names. For model-related work, define the evaluation evidence needed before implementation is described as an improvement.

Create the issue branch from the current `main` head rather than continuing an old or diverged feature branch. If older work contains useful behavior, audit and port the still-needed behavior with current tests instead of merging stale history blindly.

## Tests first where behavior changes

Prefer a failing test that describes the intended behavior before changing implementation. Provider network compatibility should be represented by deterministic fixtures for normal CI and verified separately by smoke workflows.

For documentation-only or repository-governance work, a deliberately failing product test is usually not meaningful. In that case, record the repository/configuration evidence being changed and still run the complete existing CI before merge.

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
- extension contracts or roadmap status;
- repository workflow or required CI checks.

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

Intermediate commits are useful recovery and review points. Do not squash away test-first evidence automatically when preserving that history materially improves auditability.

## Pull requests / review

Open the PR as draft while implementation or CI is incomplete. Link the issue and keep the PR body current with problem, design decisions, test evidence, known limitations and verification state. The repository PR template provides the minimum checklist.

A review should be able to answer:

1. What observable behavior changed?
2. Which contract/source assumption justifies it?
3. How is it tested?
4. What happens on missing/malformed/unavailable data?
5. Did epistemic state, quality or provenance change?
6. Did public API/configuration change?
7. Is any new performance/scientific claim supported by evidence?
8. Which documentation was updated?
9. Did the complete final-head CI (`backend`, `frontend`, `containers`) pass?
10. Are all review conversations resolved and remaining limitations explicit?

A PR should leave draft state only after its final intended head passes the required checks and no blocking review finding remains. Merge from the PR; do not recreate the same change by pushing directly to `main`.

## CI expectations

The required check contexts are currently:

- `backend`
- `frontend`
- `containers`

`containers` depends on the first two and includes Docker/Compose plus Playwright browser acceptance. Passing only unit tests or only the production build is not a substitute for the complete merge gate.

Live-source smoke workflows provide separate evidence about current provider compatibility. They do not replace deterministic PR CI, and deterministic CI does not claim that every external provider is currently available.

## Breaking changes

Changes to canonical semantics, contract version, persisted-state schema, API behavior or source identity can be breaking even if Python function signatures remain compatible. Such changes should be explicit, documented and accompanied by migration guidance where persisted/user-facing state is affected.

## Release process

A formal release/tagging process is not currently defined in the repository. Until one is implemented, do not describe a specific release automation, semantic-versioning guarantee or publication pipeline as existing. The package/repository version should remain internally consistent when intentional releases are made.