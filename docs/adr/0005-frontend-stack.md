# ADR 0005: Frontend stack and API integration

- **Status:** Accepted
- **Date:** 2026-11-24
- **Related:** ADR 0004 (API conventions)

## Context

Accrubook needs a web frontend that consumes the Django API. It must be type-safe end to end,
fail loudly when the contract changes, and be testable without a running backend. Since the
frontend ships as static files (Cloudflare Pages), it has no server of its own.

Two facts shaped the decisions below:

1. **TypeScript 7 removed the JavaScript compiler API** (`ts.factory`). Code generators that build
   TypeScript with it crash. On 2026-11-23, `openapi-typescript` 7.13.0 and `@hey-api/openapi-ts`
   0.99.0 both failed with `ts.factory` undefined, and npm `overrides` cannot relax their peer
   dependency.
2. **The backend's code is the source of truth for the API** (ADR 0004). The frontend must derive
   its types from it instead of writing them by hand.

## Decision

### Tooling

| Concern            | Choice                                                                                                                                          |
| ------------------ | ----------------------------------------------------------------------------------------------------------------------------------------------- |
| Runtime            | Node 26 LTS, pinned with `.nvmrc`, `engines` and `engine-strict=true`                                                                           |
| Build / dev server | Vite 8, React 19                                                                                                                                |
| Language           | TypeScript 7 with `strict` and `noUncheckedIndexedAccess`                                                                                       |
| Lint               | oxlint (`correctness` as errors; `react`, `jsx-a11y` plugins; `rules-of-hooks`, `exhaustive-deps`, `only-export-components`; `--deny-warnings`) |
| Format             | Prettier 3.10.1, exact version                                                                                                                  |
| Package manager    | npm with a committed `package-lock.json`; `npm ci` in setup and CI                                                                              |

The frontend runs directly in WSL, not in Docker (fast HMR; production is static files).
In development it uses real CORS against Django, not Vite's proxy, so dev matches production.

### API contract and types

```
Django code → backend/openapi.yaml → frontend/src/api/schema.d.ts → apiClient
             (make schema)          (generate:api)
```

- `backend/openapi.yaml` is generated with `manage.py spectacular --file` and committed.
  A pytest drift test fails if it is out of date.
- `frontend/src/api/schema.d.ts` is generated with `openapi-typescript` and committed.
  `npm run check:api` fails if it is out of date.
- `make api-types` regenerates both. Generated files are never edited or formatted by hand.

**Isolated generator.** Because of TypeScript 7, `openapi-typescript` runs from its own package in
`frontend/tools/openapi-typescript/` with TypeScript 5.9.3 pinned, separate from the app's
TypeScript 7. The app only consumes the generated `.d.ts` file.

**Exit condition:** when `openapi-typescript` supports TypeScript 7, move it back into
`frontend/package.json`, delete `frontend/tools/openapi-typescript/`, update the Makefile and
this ADR.

### HTTP client and errors

- One typed client: `apiClient = createClient<paths>(...)` from `openapi-fetch`.
  It resolves `fetch` on every call (`fetch: (request) => globalThis.fetch(request)`), because
  `openapi-fetch` otherwise keeps the `fetch` it saw at import time, and anything that replaces
  `globalThis.fetch` later (MSW in tests) would be bypassed.
- `VITE_API_BASE_URL` is validated at startup (`loadConfig`, fail fast, http/https only).
- `unwrap()` turns a non-2xx response into an `ApiError` that carries the RFC 9457 Problem
  Details body, validated at runtime (`toProblemDetails`). A network failure stays a `TypeError`.
- `toErrorView()` maps errors to what the UI shows: API errors show `detail` and `code`,
  network errors show a connection message, anything else a generic message.

### Server state

- **TanStack Query** owns all server state. Components never fetch with `useEffect`; the query
  key acts as the dependency list.
- Each feature has a key factory (`currencyKeys`) and `queryOptions` builders, so the cache key
  and the data type stay linked.
- A custom retry policy (`shouldRetry`) replaces the default (which retries every error three
  times, including 404): retry network errors, 408, 429 and 5xx, at most twice; fail fast on
  other 4xx and on programming errors. Mutations do not retry.
- Reference data such as currencies uses a long `staleTime` (1 hour).

### Structure

- `src/api/`: generic API code (client, errors, `unwrap`, query client, error view, generated schema).
- `src/features/<feature>/`: everything for one feature (queries, components, tests), like a Django app.
- `src/test/`: shared test infrastructure.

### Testing

- Vitest 5 with jsdom; Testing Library (query by role and text, not by CSS classes); user-event.
- **MSW 3** mocks the network, not modules, so components, TanStack Query, `apiClient` and
  `unwrap` all run for real. `onUnhandledFrame: 'error'` fails any test that makes an unexpected
  request (MSW 2 called this option `onUnhandledRequest`).
- Each test gets a fresh `QueryClient` with `retry: false`; the retry policy has its own tests.
- Mock URLs are built with `apiUrl(path: keyof paths)`, so a mock for a path that is not in the
  contract does not compile.
- Every component that loads data is tested in its loading, error, empty and success states.

## Consequences

**Positive**

- A breaking API change fails `make check` in three places: the schema drift test, `check:api`,
  and the TypeScript compiler.
- Errors are typed and consistent with the backend's Problem Details.
- Component tests need no backend and no module mocks.

**Negative / trade-offs**

- Two TypeScript versions live in the repo until the exit condition is met.
- Generated files are committed, so API changes produce larger diffs.
- The error responses are not in the OpenAPI schema yet, so `error` is validated at runtime
  instead of being typed by the generator (follow-up from ADR 0004).

## Alternatives considered

- **Orval** (works with TypeScript 7): rejected for now because it generates hooks and clients;
  we want types only plus hand-written `queryOptions`, to learn and control the data layer.
- **Downgrade the app to TypeScript 6**: rejected; the app should stay on the current major.
- **ESLint instead of oxlint**: rejected; the Vite template no longer ships ESLint, and oxlint
  covers the rules we need. oxfmt instead of Prettier: rejected while it is 0.x.
- **Vite proxy in development**: rejected in favour of real CORS (dev/prod parity).
- **Start MSW at import time instead of resolving `fetch` per call**: rejected; it depends on
  module import order, which is fragile.
- **`useEffect` + `useState` for fetching**: rejected; it misses caching, retries, cancellation
  and race-condition handling, and invites stale-closure bugs.