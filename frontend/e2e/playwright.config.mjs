import { defineConfig } from '@playwright/test'
import { fileURLToPath } from 'node:url'

const baseURL = 'http://127.0.0.1:5173'
export default defineConfig({
  testDir: '.',
  testMatch: '**/*.spec.mjs',
  timeout: 45_000,
  retries: process.env.CI ? 1 : 0,
  workers: 1,
  expect: { timeout: 10_000 },
  use: {
    baseURL,
    browserName: 'chromium',
    headless: true,
    trace: 'retain-on-failure',
  },
  reporter: process.env.CI ? 'github' : 'list',
  webServer: {
    command: 'npm run dev -- --host 127.0.0.1 --port 5173 --strictPort',
    cwd: fileURLToPath(new URL('../', import.meta.url)),
    url: baseURL,
    reuseExistingServer: false,
    timeout: 60_000,
    env: {
      VITE_SUPABASE_URL: 'https://e2e.supabase.test',
      VITE_SUPABASE_PUBLISHABLE_KEY: 'sb_publishable_offline_test_only',
      VITE_CAMPAIGN_API_BASE_URL: 'https://api.e2e.retailgrowth.test',
      // Offline browser tests exercise guarded UI; never deployed as live flags.
      VITE_PART2_SOCIAL_ENABLED: 'true',
      VITE_PART2_SOCIAL_AUTHORING_ENABLED: 'true',
      VITE_PART2_SOCIAL_OAUTH_ENABLED: 'false',
    },
  },
})
