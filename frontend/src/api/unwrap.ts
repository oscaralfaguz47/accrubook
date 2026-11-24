// Converts an `openapi-fetch` result into "data or throw".
// Use it for endpoints that return a body; network failures never get here,
// because `fetch` itself rejects with a `TypeError`.

import { ApiError, toProblemDetails } from './errors'

type FetchResult<T> = {
  readonly data?: T
  readonly error?: unknown
  readonly response: Response
}

export function unwrap<T>({ data, error, response }: FetchResult<T>): T {
  if (!response.ok) {
    throw new ApiError(toProblemDetails(response, error))
  }
  if (data === undefined) {
    throw new Error(`Expected a response body from ${response.url || 'the API'}, got none.`)
  }
  return data
}
