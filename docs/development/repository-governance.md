# Repository governance

This repository uses an issue-linked, pull-request-based development workflow. Substantive work should move through:

```text
Issue → branch from current main → failing test/repro where applicable → implementation → documentation → PR → complete CI → review → merge
```

Direct feature development on `main` is not part of the project workflow.

## Verified repository state

The governance state was inspected on 2026-09-15 while addressing issue #5.

- The repository rulesets endpoint was readable and returned an empty list: no repository ruleset was configured at that time.
- Reading classic branch protection for `main` returned HTTP 403 `Resource not accessible by integration`.
- The connected GitHub integration can work with repository content, branches, issues, pull requests and CI, but it does not expose an administration mutation that can create or edit branch protection/rulesets in this session.
- The current `CI` workflow runs on pull requests and on pushes to `main` and was not weakened by the governance change.
- The check-run contexts emitted by the current GitHub Actions workflow are exactly `backend`, `frontend` and `containers`.

Therefore this document does **not** claim that `main` is currently protected. Repository-owner administration is required to activate the rule below.

## Required `main` ruleset

Configure the repository in GitHub under **Settings → Rules → Rulesets → New ruleset → New branch ruleset**.

Use the following configuration:

1. Name the ruleset `Protect main`.
2. Set **Enforcement status** to **Active**.
3. Under **Target branches**, include the repository's **default branch** (`main`).
4. Leave the bypass list empty for normal development. Add a bypass actor only for a documented emergency process; routine feature work must not bypass the ruleset.
5. Enable **Restrict deletions**.
6. Enable **Block force pushes**.
7. Enable **Require a pull request before merging**.
   - For this single-maintainer repository, use **0 required approving reviews** so the owner is not locked out of their own PRs. Review still occurs through the documented self-review/diff-review process and resolved conversations.
   - Enable **Require conversation resolution before merging** if that option is presented separately in the current GitHub UI.
8. Enable **Require status checks to pass** and add these GitHub Actions checks:
   - `backend`
   - `frontend`
   - `containers`
9. Enable **Require branches to be up to date before merging** for those required checks so the result corresponds to the current `main` base.
10. Do **not** enable **Require linear history** while the project intentionally uses merge commits to preserve the test-first and incremental commit history of reviewed PRs.
11. Do not replace the three required checks with a weaker aggregate or skip the `containers` gate; it includes Docker/Compose and Playwright browser acceptance.
12. Save the ruleset and confirm its status is **Active**.

With an active ruleset and no routine bypass actor, direct feature pushes to `main` are rejected and changes must arrive through a pull request satisfying the required checks.

## How to verify the rule after manual activation

After saving the ruleset:

1. Re-open **Settings → Rules → Rulesets** and verify `Protect main` is **Active** and targets the default branch.
2. Confirm the ruleset lists required checks `backend`, `frontend`, and `containers`.
3. Open a small PR from a non-`main` branch and verify GitHub reports all three checks as required before merge.
4. Do not test protection by force-pushing or rewriting useful history. If a direct-push verification is desired, use a disposable no-op branch/ref workflow or inspect GitHub's rule evaluation UI instead.

## CI contract

`.github/workflows/ci.yml` is the current merge-quality contract:

- `backend` installs the Python project and live extras, checks Ruff formatting/lint, strict mypy, pytest with coverage, knowledge validation, production-data protection, secret scanning and OpenAPI generation;
- `frontend` runs frontend tests and the production build;
- `containers` depends on backend and frontend, validates Compose, builds both images, seeds deterministic acceptance-only state, starts the composed application and runs Playwright browser acceptance.

A feature PR is not considered merge-ready because only one or two of these jobs passed. All required jobs must succeed on the current PR head/base combination.

## Emergency changes

If a production-critical repository change ever requires bypassing the normal flow, record why in an issue/PR and restore normal protection immediately afterward. The research repository currently has no standing emergency-bypass actor and no reason to weaken normal CI for routine work.

## Scope and limitations

Repository protection governs how code reaches `main`; it does not prove scientific validity, live-provider availability, production security, performance or completion of the project-wide v1.0 gates. Those remain separate verification concerns.