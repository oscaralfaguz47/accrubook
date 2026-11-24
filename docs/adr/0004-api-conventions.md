# ADR 0004: REST API conventions

- **Status:** Accepted
- **Date:** 2026-11-22
- **Deciders:** Oscar Alfaro

## Context

Accrubook's first endpoint (`/api/v1/currencies/`) is in place, and many more will follow in the next
slices: tenants, clients, timesheets, payment runs, invoices. Without written rules, every endpoint
ends up slightly different: different error shapes, some lists paginated and some not, some
endpoints public by accident. Clients (our React frontend, and later third-party integrations) would
have to handle each endpoint in its own way.

We need a small set of conventions that every endpoint follows, decided once, and enforced by
settings and tests rather than by memory.

## Decision

### 1. Versioning in the URL path

- Every client-facing endpoint lives under `/api/v1/`.
- A breaking change (removing or renaming a field, changing a type, changing a status code) creates
  `/api/v2/` for that resource; `v1` keeps working until clients migrate.
- Infrastructure endpoints are not part of the client contract and are **not** versioned:
  `/api/health/`, `/api/schema/`, `/api/docs/`.

### 2. Resource naming

- Plural nouns, lowercase, hyphens between words: `/currencies/`, `/payment-runs/`.
- Trailing slash on every URL (Django's default). A request without it gets a `301` redirect.
- Detail URLs use the resource's public identifier: `/currencies/{code}/`.

### 3. JSON only

- Requests and responses are JSON (`JSONParser`, `JSONRenderer`). No browsable API: Swagger UI covers
  interactive exploration with less attack surface.
- A non-JSON body returns `415`; a client that only accepts HTML gets `406`.

### 4. Secure by default

- The default permission is `IsAuthenticated`. A public endpoint must opt out explicitly with
  `permission_classes = [AllowAny]` and a comment explaining why.
- No authentication backends are enabled until JWT arrives in Slice 1 (DRF's default Basic
  authentication is disabled on purpose).
- Data from another tenant returns `404`, not `403`, so the API never confirms that a record exists
  (applies from Slice 1).

### 5. Serializers expose an explicit allowlist of fields

- `Meta.fields` always lists the fields by name. `"__all__"` is not allowed: exposing a field must be
  a decision, so a new internal field never goes public by accident.

### 6. Every list is paginated and ordered

- `PageNumberPagination` with a page size of 50, set globally. The response shape is
  `{"count", "next", "previous", "results"}`.
- Every model behind a list has a stable default `ordering`; without it, the same row could appear on
  two pages.

### 7. One error format: RFC 9457 Problem Details

Every `4xx` and `5xx` response from the API has the same shape and the content type
`application/problem+json`:

```json
{
  "type": "about:blank",
  "title": "Not Found",
  "status": 404,
  "detail": "Not found.",
  "code": "not_found",
  "instance": "/api/v1/currencies/XXX/"
}
```

- `code` is our extension: a stable, machine-readable reason (`invalid`, `parse_error`,
  `not_authenticated`, `permission_denied`, `not_found`, `method_not_allowed`, `throttled`,
  `server_error`…). Clients decide on `code`, never on the text of `detail`.
- Validation errors (`400`) add an `errors` object with the messages for each field.
- Three handlers produce this format, one per place an error can come from
  (all in `core/errors.py`):
  1. DRF's `EXCEPTION_HANDLER`, for errors inside API views.
  2. `handler404`, for URLs that match no route.
  3. `handler500`, for crashes in plain Django views.

  Non-API paths (the Django admin) keep Django's HTML pages.
- Validation errors use `400`, DRF's standard, not `422`.
- Unexpected errors return a generic message. The real exception and its traceback go to the logs,
  never to the client.

### 8. OpenAPI 3 documentation generated from the code

- `drf-spectacular` generates the schema from serializers and views; it is served at `/api/schema/`
  with Swagger UI at `/api/docs/`.
- A contract test (`core/tests/test_openapi.py`) runs `spectacular --validate --fail-on-warn`, so
  `make check` and CI fail if any endpoint cannot be documented.

## Alternatives considered

| Option | Why not |
|---|---|
| Version in a header (`Accept: application/vnd.accrubook.v1+json`) | Harder to see, test and share (a URL can't be pasted in a browser). The URL path is the most common choice and the easiest to debug. |
| `LimitOffsetPagination` / `CursorPagination` | Page numbers are the simplest for a finance UI with page controls. Cursor pagination may be added later for very large, append-only lists (e.g. ledger entries). |
| Our own error format | A standard is already known by other developers and supported by client libraries. |
| `drf-standardized-errors` library | Adds a dependency for ~100 lines of code we fully understand and test. |
| `422 Unprocessable Content` for validation | Valid, but DRF uses `400`. We follow the framework and separate cases with `code`. |
| `drf-yasg` for docs | Generates Swagger 2.0 only; `drf-spectacular` generates OpenAPI 3 and is actively maintained. |
| `DefaultRouter` | Adds an API root page meant for the browsable API, which we disabled. `SimpleRouter` is enough. |

## Consequences

**Positive**

- The frontend handles every error with one piece of code.
- New endpoints are safe by default: authenticated, paginated, documented, consistent errors.
- The rules are enforced by settings and tests, not by memory.

**Negative / trade-offs**

- Until JWT is added (Slice 1), a protected endpoint returns `403` instead of `401`, because with no
  authentication backend there is no `WWW-Authenticate` header to send.
- `handler404` and `handler500` only run with `DEBUG=False`. In local development, Django's debug pages
  still appear; tests always run with `DEBUG=False`, so the behavior is covered there.
- Swagger UI loads its assets from a CDN.

## Follow-ups

- Step 5 (production): decide whether `/api/schema/` and `/api/docs/` are public in production; add
  throttling; serve Swagger assets without a CDN if the Content Security Policy requires it.
- Document the Problem Details error responses in the OpenAPI schema, so generated clients know the
  error shape.
- Slice 1: JWT authentication, tenant isolation (`404` for other tenants' data), and `401` responses.
