import { http, HttpResponse } from 'msw'

import type { components, paths } from '../api/schema'
import { config } from '../config'

type Currency = components['schemas']['Currency']
type PaginatedCurrencyList = components['schemas']['PaginatedCurrencyList']

/** Builds an absolute URL from a path that must exist in the API contract. */
export function apiUrl(path: keyof paths): string {
  return new URL(path, config.apiBaseUrl).href
}

export const currencies = [
  { code: 'CRC', name: 'Costa Rican Colon', decimal_places: 2, is_active: true },
  { code: 'JPY', name: 'Japanese Yen', decimal_places: 0, is_active: false },
] satisfies Currency[]

export function currencyPage(results: Currency[]): PaginatedCurrencyList {
  return { count: results.length, next: null, previous: null, results }
}

/** Happy-path handlers. A test overrides one with server.use(...) for its own scenario. */
export const handlers = [
  http.get(apiUrl('/api/v1/currencies/'), () => HttpResponse.json(currencyPage(currencies))),
]
