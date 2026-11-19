# 3. Synchronous Django on WSGI for the API

- **Status:** Accepted
- **Date:** 2026-11-19

## Context

Django supports both WSGI (synchronous) and ASGI (asynchronous) servers. Async improves concurrency when requests spend a long time waiting on I/O, but it doesn't make a single request faster.

The Accrubook API is mostly transactional CRUD on PostgreSQL with millisecond queries. Its core features (payment runs, the double-entry ledger, invoice numbering) depend on `transaction.atomic()` and `select_for_update()`, and Django's transactions don't work in async mode yet. Django REST Framework is also mainly synchronous.

## Decision

Run the Django API synchronously on WSGI with Gunicorn, scaling through multiple workers.

Use async only where it pays off:

- An async-native service (FastAPI) for slow LLM calls (Slice 10).
- Background jobs (Celery) for slow integrations like email, accounting connectors and reports (Slice 6), so they never block a request.

## Consequences

- Simpler code and full support for database transactions and DRF.
- Persistent database connections (`CONN_MAX_AGE`) stay enabled.
- Concurrency is limited by the number of Gunicorn workers. If the workload changes, this decision will be revisited in a new ADR.
