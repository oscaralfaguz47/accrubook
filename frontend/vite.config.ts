import react from '@vitejs/plugin-react'
import { defineConfig } from 'vitest/config'

// https://vite.dev/config/ · https://vitest.dev/config/
export default defineConfig({
  plugins: [react()],
  test: {
    environment: 'jsdom',
    // Only our own code; never `tools/` or anything under node_modules.
    include: ['src/**/*.test.{ts,tsx}'],
    setupFiles: ['./src/test/setup.ts'],
    // Tests must not depend on anyone's `.env.*` files.
    env: { VITE_API_BASE_URL: 'http://api.test' },
  },
})
