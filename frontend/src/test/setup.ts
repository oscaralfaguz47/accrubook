import '@testing-library/jest-dom/vitest'
import { cleanup } from '@testing-library/react'
import { afterAll, afterEach, beforeAll } from 'vitest'

import { server } from './server'

// Fail any test that makes a request no handler expects (no silent real network calls).
beforeAll(() => server.listen({ onUnhandledFrame: 'error' }))

afterEach(() => {
  cleanup() // unmount what the test rendered
  server.resetHandlers() // drop handlers a test added with server.use()
})

afterAll(() => server.close())
