// Typed, validated configuration, read once when the app starts.
// Same idea as `backend/config/env.py`: fail fast with a clear message
// instead of failing later with a confusing network error.

export type AppConfig = {
  readonly apiBaseUrl: string
}

type RawEnv = Pick<ImportMetaEnv, 'VITE_API_BASE_URL'>

export class ConfigError extends Error {
  override name = 'ConfigError'
}

function requireHttpUrl(name: string, value: string | undefined): string {
  if (!value) {
    throw new ConfigError(`${name} is not set. Add it to frontend/.env.development.`)
  }
  if (!URL.canParse(value)) {
    throw new ConfigError(`${name} must be an absolute URL, got "${value}".`)
  }
  const { protocol } = new URL(value)
  if (protocol !== 'http:' && protocol !== 'https:') {
    throw new ConfigError(`${name} must use http or https, got "${protocol}".`)
  }
  return value
}

export function loadConfig(env: RawEnv): AppConfig {
  return {
    apiBaseUrl: requireHttpUrl('VITE_API_BASE_URL', env.VITE_API_BASE_URL),
  }
}

export const config = loadConfig(import.meta.env)
