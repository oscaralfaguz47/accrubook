import createClient from 'openapi-fetch'
import { describe, expect, expectTypeOf, it } from 'vitest'

import { ApiError } from './errors'
import type { components, paths } from './schema'
import { unwrap } from './unwrap'

type Currency = components['schemas']['Currency']

const usd: Currency = { code: 'USD', name: 'US dollar', decimal_places: 2, is_active: true }

// The real `openapi-fetch` client, with `fetch` replaced: no network, no `.env`.
function clientReturning(response: Response) {
  return createClient<paths>({ baseUrl: 'http://api.test', fetch: async () => response })
}

function json(body: unknown, status: number, contentType = 'application/json') {
  return new Response(JSON.stringify(body), { status, headers: { 'Content-Type': contentType } })
}

describe('unwrap', () => {
  it('returns typed data on success', async () => {
    const client = clientReturning(json(usd, 200))

    const currency = unwrap(
      await client.GET('/api/v1/currencies/{code}/', { params: { path: { code: 'USD' } } }),
    )

    expect(currency).toEqual(usd)
    expectTypeOf(currency).toEqualTypeOf<Currency>()
  })

  it('throws an ApiError built from a Problem Details response', async () => {
    const problem = {
      type: 'about:blank',
      title: 'Not Found',
      status: 404,
      detail: 'Not found.',
      code: 'not_found',
      instance: '/api/v1/currencies/XXX/',
    }
    const client = clientReturning(json(problem, 404, 'application/problem+json'))

    const result = await client.GET('/api/v1/currencies/{code}/', {
      params: { path: { code: 'XXX' } },
    })

    expect(() => unwrap(result)).toThrow(ApiError)
    expect(() => unwrap(result)).toThrow(expect.objectContaining({ status: 404, problem }))
  })

  it('throws an ApiError even when the error body is not JSON', async () => {
    const client = clientReturning(new Response('<html>Bad Gateway</html>', { status: 502 }))

    const result = await client.GET('/api/v1/currencies/')

    expect(() => unwrap(result)).toThrow(expect.objectContaining({ name: 'ApiError', status: 502 }))
  })

  it('refuses a success response without a body', async () => {
    const client = clientReturning(new Response(null, { status: 204 }))

    const result = await client.GET('/api/v1/currencies/')

    expect(() => unwrap(result)).toThrow('Expected a response body')
  })

  it('lets network failures reject before unwrap is ever called', async () => {
    const client = createClient<paths>({
      baseUrl: 'http://api.test',
      fetch: async () => {
        throw new TypeError('Failed to fetch')
      },
    })

    await expect(client.GET('/api/v1/currencies/')).rejects.toThrow(TypeError)
  })
})
