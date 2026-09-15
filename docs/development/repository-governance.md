# Repository governance

This repository uses an issue-linked, pull-request-based development workflow. Substantive work should move through:

```text
Issue → branch from current main → failing test/repro where applicable → implementation → documentation → PR → complete CI → review → merge
```

Direct feature development on `main` is not part of the project workflow.

## Verified repository state

The governance state was inspected on 2026-09-15 while addressing issue #5 and re-verified after repository-owner configuration.

- Repository ruleset `Protect main` (ruleset id `23438336`) is **Active** and targets the default branch.
- The ruleset has no bypass actors; the connected user cannot bypass it under the current configuration.
- Branch deletion and non-fast-forward/force-push updates are blocked.
- Changes to the default branch require a pull request.
- Required approving review count is `0`, appropriate for the current single-maintainer repository, while review-thread resolution is required.
- Required status checks use strict/up-to-date branch semantics.
- The required checks are exactly `backend`, `frontend` and `containers`, each bound to the GitHub Actions integration.
- The current `CI` workflow runs on pull requests and on pushes to `main` and was not weakened by the governance change.

This means `main` is now technically protected as well as governed by project policy.

## Required `main` ruleset

The active `Protect main` ruleset is expected to retain this configuration:

1. **Enforcement status:** `Active`.
2. **Target:** repository default branch (`main`).
3. **Bypass actors:** none for routine development.
4. **Restrict deletions:** enabled.
5. **Block force pushes / non-fast-forward updates:** enabled.
6. **Require a pull request before merging:** enabled.
   - Required approving reviews: `0` for the current single-maintainer setup.
   - Review conversations must be resolved before merge.
7. **Require status checks to pass:** enabled with strict/up-to-date branch semantics.
   - `backend`
   - `frontend`
   - `containers`
   - Expected source application for each check: GitHub Actions.
8. **Require linear history:** not required while the project intentionally preserves merge commits and incremental test-first history.

Do not replace the three required checks with a weaker aggregate or skip the `containers` gate; it includes Docker/Compose and Playwright browser acceptance.

## How to verify the rule

Repository maintainers should periodically verify:

1. **Settings → Rules → Rulesets** shows `Protect main` as **Active**.
2. The ruleset targets the default branch and has no unintended bypass actor.
3. Required checks remain `backend`, `frontend`, and `containers`, sourced from GitHub Actions.
4. Pull requests cannot merge while one of those checks is pending/failing or while the branch is behind `main`.
5. Review conversations must be resolved before merge.

Do not test protection by force-pushing or rewriting useful history. Inspect the ruleset/rule evaluation UI or use an ordinary disposable PR if verification is needed.

## CI contract

`.github/workflows/ci.yml` is the current merge-quality contract:

- `backend` installs the Python project and live extras, checks Ruff formatting/lint, strict mypy, pytest with coverage, knowledge validation, production-data protection, secret scanning and OpenAPI generation;
- `frontend` runs frontend tests and the production build;
- `containers` depends on backend and frontend, validates Compose, builds both images, seeds deterministic acceptance-only state, starts the composed application and runs Playwright browser acceptance.

A feature PR is not considered merge-ready because only one or two of these jobs passed. All required jobs must succeed on the final PR head/base combination.

## Emergency changes

There is no standing bypass actor. If a future production-critical repository change genuinely requires temporary relaxation of a rule, record why in an issue/PR, make the smallest possible administrative change, and restore the normal ruleset immediately afterward.

## Scope and limitations

Repository protection governs how code reaches `main`; it does not prove scientific validity, live-provider availability, production security, performance or completion of the project-wide v1.0 gates. Those remain separate verification concerns.
