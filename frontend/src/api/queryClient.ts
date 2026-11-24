import { QueryClient } from '@tanstack/react-query'

import { ApiError } from './errors'

/** Retries after the first failure, so at most 1 + MAX_RETRIES attempts in total. */
export const MAX_RETRIES = 2

/** Statuses where trying again can succeed: timeout, rate limit, and server errors. */
function isRetryableStatus(status: number): boolean {
  return status === 408 || status === 429 || status >= 500
}

/**
 * Decides whether a failed query runs again.
 * `failureCount` is how many attempts have failed so far (0 on the first failure).
 */
export function shouldRetry(failureCount: number, error: unknown): boolean {
  if (failureCount >= MAX_RETRIES) return false
  if (error instanceof ApiError) return isRetryableStatus(error.status)
  // fetch() rejects with a TypeError when the network fails (server down, DNS, CORS).
  return error instanceof TypeError
}

/** A factory, not a singleton: every test gets a fresh cache, so tests never share state. */
export function createQueryClient(): QueryClient {
  return new QueryClient({
    defaultOptions: {
      queries: { retry: shouldRetry },
    },
  })
}
