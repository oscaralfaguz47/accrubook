// Types for the variables in `.env.*` files.
// Vite inlines every `VITE_*` variable into the JavaScript bundle at build time,
// so they are PUBLIC: never put a secret in one.

interface ViteTypeOptions {
  // Only the keys declared below exist: a typo like `VITE_API_BASEURL` is a type error.
  strictImportMetaEnv: unknown
}

interface ImportMetaEnv {
  // Optional on purpose: the file may be missing, so `loadConfig` must check it.
  readonly VITE_API_BASE_URL?: string
}
