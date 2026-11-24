import { describe, expect, it } from 'vitest'

import { ApiError, type ProblemDetails } from './errors'
import { createQueryClient, MAX_RETRIES, shouldRetry } from './queryClient'

function apiError(status: number): ApiError {
  const problem: ProblemDetails = { type: 'about:blank', title: `HTTP ${status}`, status }
  return new ApiError(problem)
}

const networkError = new TypeError('Failed to fetch')

describe('shouldRetry', () => {
  it.each([
    { name: '500 Internal Server Error', error: apiError(500) },
    { name: '503 Service Unavailable', error: apiError(503) },
    { name: '408 Request Timeout', error: apiError(408) },
    { name: '429 Too Many Requests', error: apiError(429) },
    { name: 'network failure (TypeError)', error: networkError },
  ])('retries $name', ({ error }) => {
    expect(shouldRetry(0, error)).toBe(true)
  })

  it.each([
    { name: '400 Bad Request', error: apiError(400) },
    { name: '403 Forbidden', error: apiError(403) },
    { name: '404 Not Found', error: apiError(404) },
    { name: 'a programming error', error: new Error('Empty body for HTTP 200') },
  ])('does not retry $name', ({ error }) => {
    expect(shouldRetry(0, error)).toBe(false)
  })

  it('stops after MAX_RETRIES failures', () => {
    expect(shouldRetry(MAX_RETRIES - 1, networkError)).toBe(true)
    expect(shouldRetry(MAX_RETRIES, networkError)).toBe(false)
  })
})

describe('createQueryClient', () => {
  // Runs a query that always fails and counts how many times TanStack Query called it.
  async function countAttempts(error: unknown): Promise<number> {
    const client = createQueryClient()
    let attempts = 0
    await expect(
      client.fetchQuery({
        queryKey: ['always-fails'],
        queryFn: () => {
          attempts += 1
          throw error
        },
        retryDelay: 0, // keep the test fast; the default delay is exponential (1s, 2s, ...)
      }),
    ).rejects.toBe(error)
    return attempts
  }

  it('makes 1 + MAX_RETRIES attempts for a retryable error', async () => {
    expect(await countAttempts(apiError(503))).toBe(1 + MAX_RETRIES)
  })

  it('makes a single attempt for a client error', async () => {
    expect(await countAttempts(apiError(404))).toBe(1)
  })
})
