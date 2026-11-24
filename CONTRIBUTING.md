# Contributing

## Workflow

1. Create a branch from `main`: `feat/<short-description>`, `fix/...`, `chore/...`, `docs/...`.
2. Make small, focused commits.
3. Run `make check` before pushing.
4. Open a pull request into `main`. CI must pass before merging.

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
