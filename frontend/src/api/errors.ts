// Turns any failed HTTP response into one typed error: `ApiError`.
// The backend sends RFC 9457 Problem Details (`application/problem+json`, see
// `backend/core/errors.py`), but a proxy or a crash can send anything, so every
// member is checked at runtime: TypeScript types do not exist on the network.

export type ProblemDetails = {
  readonly type: string
  readonly title: string
  readonly status: number
  readonly detail?: string
  readonly instance?: string
  // Extension member: a stable, machine-readable code (e.g. "not_found").
  readonly code?: string
}

export class ApiError extends Error {
  override name = 'ApiError'
  readonly status: number
  readonly problem: ProblemDetails

  constructor(problem: ProblemDetails) {
    super(problem.detail ?? problem.title)
    this.status = problem.status
    this.problem = problem
  }
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === 'object' && value !== null
}

function optionalString(value: unknown): string | undefined {
  return typeof value === 'string' ? value : undefined
}

export function toProblemDetails(response: Response, body: unknown): ProblemDetails {
  const fields = isRecord(body) ? body : {}
  return {
    type: optionalString(fields.type) ?? 'about:blank',
    title: optionalString(fields.title) ?? (response.statusText || `HTTP ${response.status}`),
    // The real HTTP status wins: RFC 9457 says the `status` member is only advisory.
    status: response.status,
    detail: optionalString(fields.detail),
    instance: optionalString(fields.instance),
    code: optionalString(fields.code),
  }
}
