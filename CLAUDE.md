# Accrubook

Multi-tenant SaaS for the finance operations of consultancies: time reporting, approvals,
payment runs, accounts payable and the ledger. Monorepo with a Django REST API and a React SPA.

## Repository layout

- `backend/`: Django project (`config/`) and apps (`core/`, `currencies/`). `openapi.yaml` is generated.
- `frontend/`: React + TypeScript + Vite app. `frontend/tools/openapi-typescript/` is an isolated
  tool pinned to TypeScript 5 (see ADR 0005).
- `docs/adr/`: Architecture Decision Records.
- `.github/`: CI workflow (`workflows/ci.yml`) and `dependabot.yml`.
- Root: `docker-compose.yml`, `Makefile`, `.pre-commit-config.yaml`, `README.md`, `CONTRIBUTING.md`.

## Commands

The Makefile is the single source of commands. Run `make` from the repository root; `make help`
lists every target.

- `make setup`, `make up`, `make down`, `make restart`, `make logs`
- `make check`: everything CI runs (backend lint + tests, frontend check + tests)
- `make format`: auto-fix lint and formatting (backend + frontend)
- `make hooks`: install the git pre-commit hook; `make precommit`: run every hook on all files
- `make makemigrations`, `make migrate`, `make schema`, `make api-types`

Backend commands run inside the `backend` container (`docker compose exec backend ...`); the source
is bind-mounted at `/app`. The frontend runs on the host with Node 26 (`frontend/.nvmrc`).

## Stack

- Backend: Python 3.13, Django 5.2 LTS, Django REST Framework, drf-spectacular, PostgreSQL 17,
  uv (`uv.lock` committed), Ruff, pytest + pytest-django, gunicorn.
- Frontend: Node 26, npm (`package-lock.json` committed), Vite 8, React 19, TypeScript 7
  (`strict`, `noUncheckedIndexedAccess`), TanStack Query 5, openapi-fetch, oxlint,
  Prettier 3.10.1 (exact), Vitest, Testing Library, MSW 3.
- Production (planned): Railway (API), Neon (PostgreSQL), Cloudflare Pages (SPA).

## Backend conventions

- Configuration comes only from environment variables, read through `config/env.py`, and fails
  fast when a required value is missing. There is one `settings.py`.
- Ruff rules: E, F, I, B, UP, DJ, S, SIM; line length 100.
- Each app keeps its tests in `<app>/tests/`; cross-cutting code and its tests live in `core/`.
- Surrogate primary keys by default; natural keys only for standard codes such as ISO 4217.
- Validation in two layers: model/serializer validators and database constraints.
- Data migrations use `apps.get_model`, are idempotent and always define `reverse_code`.
- Synchronous Django (WSGI + gunicorn); async only where it clearly pays off (ADR 0003).
- Multi-tenancy (from Slice 1): shared schema + `tenant_id` + PostgreSQL row-level security.
  Requests for another tenant's data return 404, not 403.

## API conventions (ADR 0004)

- Base path `/api/v1/`; plural, kebab-case resource names with a trailing slash; JSON only.
- Secure by default: `IsAuthenticated` globally; public endpoints opt out explicitly.
- Serializers list `Meta.fields` explicitly; read-only serializers set `read_only_fields = fields`.
- Lists are paginated (page size 50) and deterministically ordered.
- Errors follow RFC 9457 Problem Details (`application/problem+json`), built in `core/errors.py`.
- The OpenAPI schema is generated from code (`make schema`) and committed; a drift test fails when
  it is stale.

## Frontend conventions (ADR 0005)

- `src/api/`: the generic API layer (client, errors, unwrap, query client, error view, generated
  `schema.d.ts`). `src/features/<feature>/`: queries, components and tests of one feature.
  `src/test/`: test setup and MSW handlers.
- Server state only through TanStack Query (never `useEffect` for fetching): one query-key factory
  per feature, `queryOptions`, and the shared `shouldRetry` policy.
- API types are generated (`make api-types`) and never edited by hand.
- Every data-loading component is tested in its four states (loading, error, empty, success) with MSW.
- Accessibility: native elements before ARIA roles, `role="alert"` for errors, tables with
  `<caption>` and `scope="col"`.

## Quality gates

- pre-commit runs fast checks on staged files: hygiene hooks, Ruff, Prettier and oxlint, using the
  tool versions locked in `uv.lock` and `package-lock.json`. Type checks and tests stay in CI.
- CI (`.github/workflows/ci.yml`) runs `make check` on every pull request and on `main`, with the
  same Docker Compose stack used locally.
- GitHub Actions and pre-commit hook repositories are pinned to full commit SHAs with a
  `# vX.Y.Z` comment. Dependabot proposes updates weekly with a 7-day cooldown; deliberate upgrades
  (Python, PostgreSQL major, TypeScript in the isolated tool) are excluded on purpose.
- Never edit generated files by hand: `backend/openapi.yaml`, `frontend/src/api/schema.d.ts`.
- Tests must not write inside `backend/` (use `tmp_path`): in CI the mounted code belongs to a
  different user (uid 1001) than the container user (uid 1000).

## Git and documentation

- Every change goes through a branch (`feat/`, `fix/`, `chore/`, `docs/`, `test/`) and a pull request.
- Conventional Commits: one logical change per commit, one subject line.
- The Definition of Done lives in `CONTRIBUTING.md`. Significant decisions get an ADR in
  `docs/adr/`. The README roadmap is updated in the pull request that completes a step.
- Never commit secrets or `.env` files. `.env.example` and `frontend/.env.development` are committed
  on purpose and contain no secrets.
