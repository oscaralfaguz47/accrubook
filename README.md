# Accrubook

Multi-tenant finance operations platform for consultancies: from approved hours to consultant payouts, client invoices and double-entry journals.

> **Status:** early development (walking skeleton). See the [roadmap](#roadmap).

## Tech stack

| Layer | Technology |
|---|---|
| Backend | Python 3.13, Django 5.2 LTS |
| Database | PostgreSQL 17 |
| Frontend | React + TypeScript + Vite *(coming in Slice 0)* |
| Tooling | uv (Python packages), Ruff (lint + format), pytest |
| Local environment | Docker Compose |
| Hosting | Railway (API), Neon (PostgreSQL), Cloudflare Pages (frontend) |

Architecture decisions are recorded in [`docs/adr/`](docs/adr/).

## Getting started

### Prerequisites

- [Docker](https://docs.docker.com/get-docker/) with Compose v2
- `make`
- Optional, for editor autocompletion only: [uv](https://docs.astral.sh/uv/getting-started/installation/)

You do **not** need Python or PostgreSQL installed locally. Everything runs in containers.

### First-time setup

```bash
git clone https://github.com/<your-user>/accrubook.git
cd accrubook
make setup      # creates .env from .env.example and builds the images
make up         # starts PostgreSQL and the API
make migrate    # applies database migrations
```

Check that it works:

```bash
curl http://localhost:8000/api/health/
# {"status": "ok", "database": "ok"}
```

| Service | URL |
|---|---|
| API | http://localhost:8000/api/ |
| Health check | http://localhost:8000/api/health/ |
| Django admin | http://localhost:8000/admin/ (create a user with `make superuser`) |

### Connecting a database client (pgAdmin, DBeaver…)

| Setting | Value |
|---|---|
| Host | `127.0.0.1` |
| Port | `POSTGRES_HOST_PORT` from your `.env` (default `5432`) |
| Database / user / password | `POSTGRES_DB` / `POSTGRES_USER` / `POSTGRES_PASSWORD` from your `.env` |

Use `127.0.0.1` rather than `localhost`: the port is published on IPv4 only, and some clients try IPv6 first.

### Editor setup (optional)

Your editor needs a local virtual environment to resolve imports and run linters:

```bash
cd backend
uv sync         # creates backend/.venv from uv.lock
```

Then point your editor's Python interpreter to `backend/.venv`. This environment is only for the editor. The application always runs in Docker.

## Common commands

Run `make help` to see them all.

| Command | What it does |
|---|---|
| `make up` / `make down` | Start / stop all services |
| `make restart` | Recreate services (picks up `.env` changes) |
| `make logs` | Follow service logs |
| `make migrate` | Apply migrations |
| `make makemigrations` | Create migrations from model changes |
| `make test` | Run the test suite |
| `make lint` | Check linting and formatting |
| `make format` | Auto-fix lint issues and format code |
| `make check` | Run everything CI runs (lint + tests) |

## Managing dependencies

Python dependencies are managed with **uv**:

- `backend/pyproject.toml` declares the direct dependencies and their allowed version ranges.
- `backend/uv.lock` pins the **exact** version of every package, including transitive ones. It is committed, so every machine and every environment installs the same thing.
- The Docker image installs strictly from the lockfile (`uv sync --frozen`). Production images skip development tools (`--no-dev`).

To add or remove a package:

```bash
cd backend
uv add <package>             # runtime dependency
uv add --dev <package>       # development-only dependency (tests, linters)
uv remove <package>
cd .. && make setup && make restart   # rebuild the image with the new lockfile
```

Always commit `pyproject.toml` and `uv.lock` together.

## Project structure

```
accrubook/
├── backend/                 # Django API
│   ├── config/              # Settings, root URLs, WSGI/ASGI, env helpers
│   ├── core/                # Cross-cutting endpoints (health check)
│   ├── Dockerfile
│   ├── pyproject.toml       # Dependencies and tool configuration
│   └── uv.lock              # Locked dependency versions
├── docs/adr/                # Architecture Decision Records
├── docker-compose.yml       # Local development environment
├── Makefile                 # Developer commands
└── .env.example             # Environment variables template
```

## Configuration

All configuration comes from environment variables ([12-factor](https://12factor.net/config)). See [`.env.example`](.env.example) for the full list. The app refuses to start if a required variable is missing.

## Troubleshooting

| Problem | Fix |
|---|---|
| `ports are not available ... 5432` | Another PostgreSQL is using the port. Set `POSTGRES_HOST_PORT=5433` in `.env` and run `make restart` |
| `Makefile: *** missing separator` | Makefile recipes must be indented with tabs: `sed -i 's/^    /\t/' Makefile` |
| `Missing required environment variable: ...` | Your `.env` is missing that variable. Compare it with `.env.example` |

## Roadmap

Built as vertical slices, each one deployed to production:

- [ ] **Slice 0:** walking skeleton (backend, frontend, CI, deploy)
- [ ] **Slice 1:** tenants and authentication (JWT)
- [ ] **Slice 2:** legal entities, clients and projects
- [ ] **Slice 3:** consultants and effective-dated rate cards
- [ ] **Slice 4:** time reporting and approval workflow
- [ ] **Slice 5:** payment runs, accounts payable and double-entry ledger

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md).

## API

- Interactive docs (Swagger UI): http://127.0.0.1:8000/api/docs/
- OpenAPI 3 schema: http://127.0.0.1:8000/api/schema/
- Conventions (versioning, errors, pagination): [ADR 0004](docs/adr/0004-api-conventions.md)