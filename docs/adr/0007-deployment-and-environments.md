# ADR 0007: Deployment and environments

- **Status:** Proposed
- **Date:** 2026-11-26
- **Amended:** 2026-11-27 (step 5h: image registry, region check, uptime)
- **Related:** ADR 0002 (hosting), ADR 0003 (sync Django), ADR 0005 (frontend, isolated tools),
  ADR 0006 (CI and quality gates)
- **Spike:** Railway project `accrubook-spike`, deleted after the spike

## Context

Slice 0 ends with the API, the database and the SPA running on the internet. ADR 0002 chose
Railway (API), Neon (PostgreSQL) and Cloudflare (SPA). This ADR decides how we deploy to them.
Six facts, checked against the providers' documentation on 2026-11-26, shaped the decisions:

1. **Railway Config as Code is deprecated.** `railway.toml` / `railway.json` stop being read on
   2026-12-01. The replacement is Infrastructure as Code: a TypeScript file applied with
   `railway config plan` / `apply`.
2. **Railway has no "promote this deployment" feature.** "Deploy Latest Commit" deploys the head
   of the branch, which may not be the commit that was tested in staging.
3. **Railway runs health checks only during a deploy**, from the host `healthcheck.railway.app`,
   and runs the pre-deploy command in a separate container whose files are not kept.
4. **Neon's pooler uses PgBouncer in transaction mode.** Session-level `SET`, `LISTEN/NOTIFY`
   and server-side cursors do not work through it; migrations must use the direct endpoint.
5. **Neon roles created in the console belong to `neon_superuser`, which has `BYPASSRLS`.**
   An application connecting with such a role ignores row-level security.
6. **A Cloudflare Pages apex domain requires the zone on Cloudflare.** The registrar
   (Vercel) can stay; only the nameservers move.

A spike on Railway (project `accrubook-spike`) added six more facts:

7. **A prebuilt image can be promoted.** The same image was deployed to a second environment
   without Railway rebuilding it.
8. **`railway config plan` ignores region changes.** A service's region is fixed when the
   service is created; editing it in `railway.ts` shows no change in the plan.
9. **The Free plan forces serverless.** Every service sleeps when idle. On Hobby,
   `sleepApplication` can be set per environment.
10. **The SDK file is an ES module.** `infra/railway/package.json` needs `"type": "module"`, and
    any machine that runs the Railway CLI with it needs Node.
11. **Variables managed in Railway need `preserve()`.** A variable set in Railway, not in
    `railway.ts`, must still be declared in the file with `preserve()`.
12. **Containers see the host's CPUs.** Inside a Railway container the CPU count is 48, so a
    value derived from it scales with the host, not with the service.

Step 5h (image registry) added two more:

13. **Private registry pulls need Railway Pro.** Railway's docs: "Private Docker registry
    deployments require the Pro plan", with a classic personal access token for GHCR. Hobby
    can pull public images only.
14. **A package that a workflow creates in a public repository starts public.** A public package
    can never be made private again; it can only be deleted (while no version has more than
    5,000 downloads).

## Decision

### Two environments: staging and production

| Layer    | Staging                          | Production                 |
| -------- | -------------------------------- | -------------------------- |
| SPA      | `staging.accrubook.com`          | `accrubook.com`            |
| API      | `api.staging.accrubook.com`      | `api.accrubook.com`        |
| Railway  | environment `staging`            | environment `production`   |
| Neon     | project `accrubook-staging`      | project `accrubook-prod`   |
| Database | PostgreSQL 17                    | PostgreSQL 17              |
| Region   | US East (Virginia)               | US East (Virginia)         |
| Sleep    | on                               | off                        |

- Both environments run the same code and image; they differ only in environment variables
  (`config/env.py`). There is no environment branch: everything ships from `main`.
- Staging and production use **separate Neon projects**, so they have separate credentials and
  separate compute quotas. A leaked staging credential cannot reach production data.
- PostgreSQL 17 matches local development and CI. Neon defaults to 18; a major upgrade stays a
  deliberate, separate change.
- Railway and Neon run in the same region to keep query latency low. Neon regions cannot be
  changed after creation.
- Each Railway service gets its region when it is created, because `railway config plan` ignores
  region changes (fact 8). For go-live, the region is checked by hand when each service is
  created and recorded in that pull request. A CI check that reads it from the deployment record
  replaces the manual check later (#17).
- Sleep is explicit per environment (fact 9): `sleepApplication` is `false` in production and
  `true` in staging. Production needs the Hobby plan, because Free forces every service to sleep.

### Build once, promote the same image

1. A pull request merges to `main` only with CI green (ADR 0006).
2. On `main`, CI builds the production backend image once, smoke-tests it (`make smoke-image`:
   gunicorn, production settings, a real PostgreSQL) and pushes that same image to GitHub
   Container Registry, tagged with the full commit SHA and labeled with its source and revision.
   It records the registry digest and signs a build provenance attestation for it. Pull requests
   run the same build and smoke test without pushing.
3. CI deploys that image to staging automatically.
4. A `production` GitHub environment with a required reviewer gates the production job, which
   deploys **the same image digest**. Nothing is rebuilt for production.

Rollback means deploying a previous digest. This is only safe because of the next rule.

### Image registry

- The image is `ghcr.io/oscaralfaguz47/accrubook/backend`, a **public** package (fact 14), so
  Railway Hobby pulls it without credentials (fact 13). The repository is public, so the image
  exposes no code that is not public already, and it contains no secrets.
- Only the `publish image` job, which runs on `main` only, has `packages: write`. Pull request
  jobs build and test with read-only permissions.
- Deploys reference the digest, never a tag. There is no moving tag such as `latest` or `main`:
  Railway watches image tags and offers (or, with automatic updates, applies) a redeploy when
  a tag's digest changes.
- Before promoting a digest, CI verifies its attestation with
  `gh attestation verify --source-ref refs/heads/main`, so an image built from a pull request
  cannot reach production.
- If the repository becomes private: publish to a new private package, give Railway (Pro) a
  read-only token, and delete the public package.

### Migrations

- `python manage.py migrate` runs as Railway's **pre-deploy command**, after the build and before
  the new version takes traffic. If it fails, the deployment stops and the old version keeps
  serving.
- Migrations must be **backward compatible** (expand/contract): the old version keeps serving
  traffic against the migrated schema while the new one starts, and during a rollback.
- Migrations connect through Neon's **direct** endpoint; the application uses the **pooled**
  endpoint.

### Database connections

- TLS with `sslmode=verify-full` on every connection.
- Through the pooler: `disable_server_side_cursors=True`; `conn_max_age` stays below Neon's
  5-minute scale-to-zero window; `conn_health_checks=True`.
- Tenant context (Slice 1) is set with transaction-local settings (`SET LOCAL`), never with
  session-level `SET`, so it cannot leak to another tenant through a reused connection.
- Roles (implemented in Slice 1, with RLS): an owner role runs migrations; the application
  connects with a role created in SQL, without `BYPASSRLS`.

### Railway configuration as code

- The Railway project is described in `infra/railway/railway.ts` and applied with the Railway
  CLI. The SDK is an isolated tool with its own `package.json` and lockfile (same pattern as
  ADR 0005).
- `infra/railway/package.json` declares `"type": "module"` (fact 10). The CI job that runs
  `railway config plan` / `apply` sets up Node itself; jobs do not share machines.
- The Railway CLI is pinned to an exact version (5.75.0), in CI and in `CONTRIBUTING.md`.
- Secrets never appear in the file: they are set in Railway per environment. Every variable
  managed in Railway, secret or not, is declared with `preserve()` (fact 11). CI authenticates
  with project tokens scoped to one environment, stored as GitHub environment secrets.
- Health check: `/api/health/` (readiness, checks the database). `healthcheck.railway.app` is in
  `DJANGO_ALLOWED_HOSTS`.

### Application server

- gunicorn runs a fixed number of workers, set explicitly per environment. It is never derived
  from the CPU count, because containers see the host's 48 CPUs (fact 12).

### Static files

- WhiteNoise serves the Django admin's static files from gunicorn, with
  `CompressedManifestStaticFilesStorage` (hashed names, cached forever, gzip).
- `collectstatic` runs at image build time, so the image is complete and immutable.
- Swagger UI and the schema endpoint are disabled unless an environment variable enables them
  (local and staging). Where enabled, the Swagger UI version is pinned instead of `@latest`.

### Django production hardening

- `python manage.py check --deploy` must pass with production-like settings.
- HTTPS is enforced (HSTS, secure cookies). Railway terminates TLS, so Django trusts the
  forwarded protocol header only from Railway's proxy.

### SPA and DNS

- The SPA is deployed with **Cloudflare Pages** from `frontend/`. Every branch gets a preview
  whose `VITE_API_URL` points to staging, never to production.
- DNS moves to **Cloudflare (Free plan)**; Vercel stays the registrar. The API records are
  **DNS only**, so Railway terminates TLS with its own certificate. Proxying through Cloudflare
  would require weakening the origin certificate check ("Full" instead of "Full (strict)").

## Alternatives considered

- **Production only:** cheaper, but every migration would meet the real database first in
  production.
- **Staging as a Neon branch of the production project:** shares the compute quota and the
  roles with production.
- **Railway dashboard configuration:** fast, but not reviewed in pull requests and not
  reproducible.
- **"Deploy Latest Commit" for production:** simpler, but production could get a commit that
  never ran in staging.
- **Cloudflare Workers for the SPA:** Cloudflare's recommended platform for new projects, but its
  docs do not cover per-branch build variables, and it needs `wrangler` as a dependency.
  Revisit when the SPA needs server-side code.
- **Object storage for static files:** more moving parts and credentials for a few admin files.

## Consequences

**Positive**

- What runs in production is provably what passed CI and staging.
- Infrastructure changes are reviewed in pull requests like code.
- Staging is isolated from production, including credentials.

**Negative / trade-offs**

- Cost: Railway Hobby is $5/month including $5 of usage, and production requires it (fact 9).
  The estimate of $5–6/month assumed two always-on services; with staging asleep when idle it
  is an upper bound. Neon Free and Cloudflare Free cost $0.
- Staging sleeps when idle, so its first request after a quiet period waits for it to wake.
- `railway config plan` does not catch a wrong region (fact 8). Until the CI check exists (#17),
  only the manual check at service creation does.
- Railway runs health checks only during a deploy (fact 3). Until an external uptime monitor
  exists (#16), nothing reports that production is down.
- The image package is public for good (fact 14); going private means a new package.
- Neon Free compute scales to zero after 5 minutes; the first query after that takes a few
  hundred milliseconds. Free projects have no IP allow list.
- Expand/contract migrations take two deploys for a destructive schema change.
- One more isolated Node tool (`infra/railway/`) to keep updated with Dependabot.
- Hobby keeps 7 days of logs.
- Throttle counters live in each gunicorn worker's memory: limits are approximate (up to one
  counter per worker) and reset on deploy. Revisit with a shared cache in Slice 1.

## To verify before implementation

- [x] Railway CLI plans `railway.ts` with the SDK installed in `infra/railway/` (spike, fact 10).
- [ ] `railway config apply` runs from CI with a project token scoped to one environment.
- [x] A prebuilt image is promoted to a second environment without a rebuild (spike, fact 7).
- [x] CI pushes the tested image to GHCR, tagged with the commit SHA, and records its digest;
      the registry serves that digest to anonymous clients (PR #23).
- [ ] CI sets the image per environment, by digest.
- [ ] Railway accepts an image reference by digest (`image@sha256:…`).
- [ ] How CI reads a service's region from the deployment record (#17; manual for go-live).
- [ ] How the pre-deploy command receives the direct database URL.
- [x] Which forwarded-protocol header Railway sets: `X-Forwarded-Proto: https` (Railway docs,
      "Specs and limits").
- [ ] Railway sets `X-Real-IP` to the client address and overwrites a client-sent value
      (test on staging).
- [ ] GitHub environment required reviewers on a public repository with one maintainer.
- [ ] The base image has the CA bundle for `verify-full`; the bundled libpq version.
- [ ] Pages applies preview variables at build time (test build).
- [ ] DNSSEC status of `accrubook.com` before changing nameservers.
- [ ] `neondb_owner` attributes (`rolbypassrls`) once the projects exist.
