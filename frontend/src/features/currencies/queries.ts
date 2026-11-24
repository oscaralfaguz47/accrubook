import { queryOptions } from '@tanstack/react-query'

import { apiClient } from '../../api/client'
import { unwrap } from '../../api/unwrap'

/** ISO 4217 currencies are reference data: they almost never change. */
const ONE_HOUR_MS = 60 * 60 * 1000

/** One place for every cache key of this feature, from general to specific. */
export const currencyKeys = {
  all: ['currencies'] as const,
  list: () => [...currencyKeys.all, 'list'] as const,
}

export function currencyListQuery() {
  return queryOptions({
    queryKey: currencyKeys.list(),
    queryFn: async ({ signal }) => unwrap(await apiClient.GET('/api/v1/currencies/', { signal })),
    staleTime: ONE_HOUR_MS,
  })
}
