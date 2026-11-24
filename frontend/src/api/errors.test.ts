import { describe, expect, it } from 'vitest'

import { ApiError, toProblemDetails } from './errors'

// The real body that `backend/core/errors.py` returns for an unknown currency.
const notFoundBody = {
  type: 'about:blank',
  title: 'Not Found',
  status: 404,
  detail: 'Not found.',
  code: 'not_found',
  instance: '/api/v1/currencies/XXX/',
}

describe('toProblemDetails', () => {
  it('maps every member of a backend Problem Details body', () => {
    const response = new Response(null, { status: 404, statusText: 'Not Found' })

    expect(toProblemDetails(response, notFoundBody)).toEqual(notFoundBody)
  })

  it('trusts the HTTP status over the advisory `status` member', () => {
    const response = new Response(null, { status: 503 })

    expect(toProblemDetails(response, { ...notFoundBody, status: 404 }).status).toBe(503)
  })

  it.each([
    ['an HTML page from a proxy', '<html>Bad Gateway</html>'],
    ['an empty body', undefined],
    ['a JSON array', ['unexpected']],
  ])('falls back to safe defaults for %s', (_label, body) => {
    const response = new Response(null, { status: 502, statusText: 'Bad Gateway' })

    expect(toProblemDetails(response, body)).toEqual({
      type: 'about:blank',
      title: 'Bad Gateway',
      status: 502,
    })
  })

  it('uses "HTTP <status>" when there is no status text either', () => {
    expect(toProblemDetails(new Response(null, { status: 500 }), undefined).title).toBe('HTTP 500')
  })

  it('ignores members with the wrong type instead of trusting them', () => {
    const response = new Response(null, { status: 400, statusText: 'Bad Request' })

    const problem = toProblemDetails(response, { title: 42, detail: ['x'], code: null })

    expect(problem).toEqual({ type: 'about:blank', title: 'Bad Request', status: 400 })
  })
})

describe('ApiError', () => {
  it('is a real Error with the status and the full problem', () => {
    const error = new ApiError({ ...notFoundBody })

    expect(error).toBeInstanceOf(Error)
    expect(error.name).toBe('ApiError')
    expect(error.status).toBe(404)
    expect(error.problem.code).toBe('not_found')
  })

  it('uses `detail` as the message, or `title` when there is no detail', () => {
    expect(new ApiError(notFoundBody).message).toBe('Not found.')
    expect(new ApiError({ type: 'about:blank', title: 'Bad Gateway', status: 502 }).message).toBe(
      'Bad Gateway',
    )
  })
})
