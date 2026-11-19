# 2. Technology stack and hosting

- **Status:** Accepted
- **Date:** 2026-11-18

## Context

Accrubook is a rebuild of an internal .NET finance platform as a multi-tenant SaaS. It needs a mature ecosystem for transactional business logic, a relational database with strong consistency guarantees, a modern SPA frontend, and low hosting costs during early development.

## Decision

- **Backend:** Python 3.13 + Django 5.2 LTS (+ Django REST Framework for the API). LTS gives long-term security support. Django's ORM, migrations and admin speed up the delivery of a data-heavy domain.
- **Database:** PostgreSQL. ACID transactions, row-level locking and Row-Level Security support multi-tenancy and a double-entry ledger.
- **Frontend:** React + TypeScript + Vite, deployed as a static site.
- **Python tooling:** uv for dependency management with a committed lockfile. Ruff for linting and formatting. pytest for tests.
- **Local environment:** Docker Compose, so the only prerequisite is Docker.
- **Hosting:** Railway for the API (and, later, workers), Neon for managed PostgreSQL, Cloudflare Pages for the frontend. Chosen for low cost and always-on behavior (no cold starts on the API).

## Consequences

- Frontend and API live on different origins, so CORS and auth must be configured explicitly.
- Neon's free tier scales to zero, so the first request after a period of inactivity may be slightly slower.
- Costs are re-evaluated when background workers and Redis are introduced.
