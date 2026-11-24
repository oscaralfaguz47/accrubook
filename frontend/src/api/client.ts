// The one typed HTTP client for the Accrubook API.
// Every path, parameter and response type comes from `schema.d.ts`,
// which is generated from the backend's OpenAPI contract.

import createClient from 'openapi-fetch'

import { config } from '../config'
import type { paths } from './schema'

export const apiClient = createClient<paths>({ baseUrl: config.apiBaseUrl })
