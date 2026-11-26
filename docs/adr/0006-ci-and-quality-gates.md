# ADR 0006: CI and quality gates

- **Status:** Accepted
- **Date:** 2026-11-25
- **Amended:** 2026-11-25 (uv version policy, noreply commit email; see "Amendments")
- **Related:** ADR 0005 (frontend stack, TypeScript 5 in the isolated tool)

## Context

Every change to `main` must be linted, formatted and tested, and the result must not depend on
what is installed on one developer's machine. Four facts shaped the decisions below:

1. **Local checks can be skipped.** Git hooks only run if they are installed, and anyone can
   bypass them with `git commit --no-verify`. Bots such as Dependabot never run them.
2. **CI runs as a different user.** On GitHub-hosted runners the checked-out code belongs to
   uid 1001, while the backend container runs as uid 1000, so tools cannot write caches inside the
   bind-mounted `backend/`.
3. **CI dependencies are a supply-chain risk.** A tag such as `v7` can be moved to point at
   different code; a commit SHA cannot.
4. **A green check is only advice** unless the repository blocks merging when it is red.

## Decision

### CI runs the Makefile, nothing else

GitHub Actions (`.github/workflows/ci.yml`) runs on every pull request and on pushes to `main`.
The workflow only prepares a clean machine and calls `make`, so CI and local development run the
same commands. There are two jobs, which run in parallel and report separately:

| Job (check name) | Runs              | Environment                                                  |
| ---------------- | ----------------- | ------------------------------------------------------------ |
| `make check`     | `make check`      | The same Docker Compose stack used locally                   |
| `pre-commit`     | `make precommit`  | uv from `required-version` in `backend/pyproject.toml`, Node from `.nvmrc` |

Tool caches (Ruff, pytest) are written to `/tmp` inside the container, never to `backend/`.

### pre-commit for fast local feedback

`.pre-commit-config.yaml` runs hygiene hooks (whitespace, end of file, line endings, YAML/TOML
syntax, merge conflicts, large files, private keys) plus Ruff, Prettier and oxlint on staged
files. Ruff, Prettier and oxlint are **local hooks** that run the versions locked in `uv.lock`
and `package-lock.json`, so each tool has one version to maintain. Type checks and tests stay in
CI because they are too slow for every commit. The `pre-commit` CI job runs every hook on all
files, which closes the `--no-verify` gap.

### Everything pinned, updated by Dependabot

GitHub Actions and pre-commit hook repositories are pinned to full commit SHAs with a
`# vX.Y.Z` comment. Dependabot proposes updates weekly for seven ecosystems (Actions, uv, two
npm projects, Dockerfile, Docker Compose, pre-commit) with a 7-day cooldown, so a compromised
release has time to be detected before it reaches us. Deliberate upgrades are excluded: Python
minor and major, PostgreSQL major, `@types/node` major and TypeScript major in the isolated tool.

### `main` is protected by a ruleset

A repository ruleset on the default branch requires a pull request, requires the `make check` and
`pre-commit` checks to pass on a branch that is up to date with `main`, and blocks force pushes and
deletion. Required approvals are 0 because GitHub does not let authors approve their own pull
requests, and the project has one maintainer. The bypass list is empty, so admins follow the same
rule.

Rulesets are not available for private repositories on the free plan, so the repository is
public. Before that change, the full git history was checked for committed secrets.

## Consequences

**Positive**

- A change reaches `main` only through a pull request with both checks green.
- CI failures are reproducible locally with the same `make` target.
- Moved tags and freshly published malicious releases do not reach CI immediately.
- A formatting failure and a test failure show up as different checks.

**Negative / trade-offs**

- Required checks match job names: renaming a job in `ci.yml` blocks every pull request until
  the ruleset is updated.
- SHAs are harder to read than tags; the version comment must be kept in sync (Dependabot does it).
- The `pre-commit` job duplicates part of `make check` (Ruff, Prettier, oxlint) in exchange for a
  clearer failure and coverage of the hygiene hooks.
- The repository is public: the history, including author emails, is visible to anyone. New
  commits use the GitHub noreply address; older commits keep the original email, because
  rewriting a protected `main` would cost more than it protects.

## Alternatives considered

- **pre-commit.ci**: rejected; it runs hooks in its own environment with separately pinned tool
  versions, while we want the versions from our lockfiles and no extra external service.
- **Hooks only in `make check`**: rejected; one job would mix formatting and test failures.
- **Actions pinned to tags**: rejected; tags are mutable.
- **Classic branch protection**: rejected in favour of rulesets, which GitHub recommends for new
  setups and which can be read through the API.
- **GitHub Pro to keep the repository private**: rejected; a public repository is free and the
  project is meant to be shown.
- **Required approvals set to 1**: rejected; a single maintainer could never merge.

## Amendments

- **2026-11-25, uv version policy.** uv ran with a different version on each machine (0.11 in
  Docker and CI, 0.12 on the host), and nothing updated the pins, because Dependabot does not
  read `COPY --from=` or action inputs. Now `required-version` in `backend/pyproject.toml`
  declares the allowed range (0.13.x), and every uv refuses to run outside it. The Dockerfile
  pins the exact version on a `FROM` line that Dependabot updates. CI reads the range through
  `setup-uv`'s `version-file`. The image build runs `uv sync --locked`, so a stale `uv.lock`
  fails the build.
- **2026-11-25, commit email.** New commits use the GitHub noreply address, and GitHub blocks
  pushes that would expose the personal email. Older commits are unchanged (see Consequences).
