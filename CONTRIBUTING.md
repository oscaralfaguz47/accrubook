# Contributing

## Workflow

1. Once per clone, install the git hook: `make hooks` (needs
   [uv](https://docs.astral.sh/uv/getting-started/installation/) on your machine, in the range
   set by `required-version` in `backend/pyproject.toml`).
2. Create a branch from `main`: `feat/<short-description>`, `fix/...`, `chore/...`, `docs/...`,
   `test/...`.
3. Make small, focused commits. The hook checks the staged files on every commit. If a hook fixes
   a file, the commit stops: review the change, `git add` the file and commit again.
4. Run `make check` before pushing.
5. Open a pull request into `main`. It can only be merged when CI passes (see below).

## Quality gates

| Where                | What runs                                                | When                     |
| -------------------- | -------------------------------------------------------- | ------------------------ |
| Your machine         | pre-commit hooks on staged files (hygiene, Ruff, Prettier, oxlint) | `git commit`   |
| CI, `make check` job | Backend lint + tests, frontend check + tests             | Every pull request and push to `main` |
| CI, `pre-commit` job | Every hook on all files (`make precommit`)               | Every pull request and push to `main` |

Don't use `git commit --no-verify` to get past a failing hook. CI runs the same hooks, and the
pull request can't be merged until they pass. To run every hook on all files locally:
`make precommit`.

### Branch protection on `main`

A repository ruleset protects `main` (Settings → Rules → Rulesets → `main`):

- Changes arrive only through pull requests. Required approvals are 0 because the project has one
  maintainer, and GitHub doesn't let authors approve their own pull requests.
- The `make check` and `pre-commit` checks must pass on a branch that is up to date with `main`.
- Force pushes and deleting the branch are blocked. Nobody can bypass the rule, admins included.

**Renaming a CI job:** the ruleset waits for a check with the job's exact `name:` in
`.github/workflows/ci.yml`. A pull request that renames a job stays blocked until the required
check in the ruleset is renamed too. Change it right before merging that pull request.

The reasons behind these rules are in [ADR 0006](docs/adr/0006-ci-and-quality-gates.md).

## Commit messages

We follow [Conventional Commits](https://www.conventionalcommits.org/):

```
<type>(<optional scope>): <imperative summary>

feat(ledger): add journal entry balancing validation
fix(auth): reject expired refresh tokens
chore: bump Django to 5.2.x
docs: document local setup
test(timesheets): cover rejection workflow
refactor(payments): extract pricing service
```

## Definition of done

A change is done when:

- [ ] It has tests (unit and/or integration) and `make test` passes
- [ ] `make lint` passes
- [ ] Migrations are included and reversible (when models change)
- [ ] New environment variables are added to `.env.example`
- [ ] Docs (README / ADR) are updated if behavior or architecture changed
- [ ] It is deployed and verified in production

- [ ] If you changed the API (serializers, views, URLs), you ran `make api-types` and committed
      `backend/openapi.yaml` and `frontend/src/api/schema.d.ts`.
- [ ] New frontend data fetching uses TanStack Query (`queryOptions` in the feature's
      `queries.ts`), never `useEffect`.
- [ ] Components that load data are tested in their loading, error, empty and success states,
      with MSW for the network (no module mocks).
- [ ] UI uses native HTML elements before ARIA roles, and errors are announced (`role="alert"`).

## Code guidelines

- Business logic lives in service modules, not in views or serializers.
- Use enums / `TextChoices` for statuses and types, never display strings.
- Money uses `Decimal`, never `float`.
- Every tenant-scoped query must filter by tenant. Isolation is covered by tests.
- No secrets in code or in the repository. Configuration comes from environment variables.
