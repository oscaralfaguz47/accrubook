import { describe, expect, it } from 'vitest'

import { config, ConfigError, loadConfig } from './config'

describe('loadConfig', () => {
  it.each(['http://localhost:8000', 'https://api.accrubook.com'])('accepts %s', (url) => {
    expect(loadConfig({ VITE_API_BASE_URL: url })).toEqual({ apiBaseUrl: url })
  })

  it.each([undefined, ''])('rejects a missing value (%j)', (value) => {
    expect(() => loadConfig({ VITE_API_BASE_URL: value })).toThrow(
      new ConfigError('VITE_API_BASE_URL is not set. Add it to frontend/.env.development.'),
    )
  })

  it.each(['/api', 'localhost', 'not a url'])('rejects a non-absolute URL (%s)', (value) => {
    expect(() => loadConfig({ VITE_API_BASE_URL: value })).toThrow(/must be an absolute URL/)
  })

  it.each(['ftp://files.example.com', 'javascript:alert(1)'])('rejects %s', (value) => {
    expect(() => loadConfig({ VITE_API_BASE_URL: value })).toThrow(/must use http or https/)
  })

  it('throws a ConfigError, so callers can tell config bugs apart', () => {
    expect(() => loadConfig({ VITE_API_BASE_URL: '' })).toThrow(ConfigError)
  })
})

describe('config', () => {
  it('is loaded from the environment', () => {
    expect(config.apiBaseUrl).toBe('http://api.test')
  })
})
