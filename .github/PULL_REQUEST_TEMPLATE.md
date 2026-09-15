## Linked issue

Closes #

## Problem and boundary

Describe the observable problem, the owning boundary (adapter, canonical contract, agent, persistence, orchestration/scenario, API, frontend, evaluation or documentation), and explicit non-goals.

## Changes

Describe the implementation and any contract, data, API, configuration or documentation changes.

## Test-driven evidence

- [ ] A failing test or reproducible check was added first for substantive behavior changes, where applicable.
- [ ] The implementation makes the new/changed test pass without weakening existing tests.
- [ ] Missing, malformed and unavailable input behavior is covered where relevant.
- [ ] Epistemic state, quality and provenance semantics remain explicit.

For documentation-only/repository-governance changes, explain why a failing product test is not applicable and identify the repository evidence used instead.

## Verification

The PR is not merge-ready until the complete required CI set succeeds on the final head:

- [ ] `backend`
- [ ] `frontend`
- [ ] `containers` (Docker/Compose + Playwright acceptance)

Add any feature-specific smoke/evaluation evidence here. External live-provider smoke results must be distinguished from deterministic CI.

## Review

- [ ] The complete diff was reviewed for unintended changes.
- [ ] Review conversations are resolved.
- [ ] Documentation was updated when architecture, contracts, behavior, configuration, deployment or limitations changed.
- [ ] No secret, generated runtime snapshot or production synthetic fallback was introduced.
- [ ] Remaining risks/limitations are stated rather than hidden.

## Release impact

State whether this PR warrants a version/tag/release. Do not create a release for an ordinary internal change unless there is a meaningful user-facing or research milestone.