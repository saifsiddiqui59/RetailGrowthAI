import { defineConfig } from '@playwright/test'
import { hostedConfig } from './hosted-support.mjs'

// Separate opt-in config: no Vite mock server; imported only by manual command.
// No GitHub Actions execution, deployments or migrations.
const target = hostedConfig(process.env)
export default defineConfig({
  testDir: '.',
  testMatch: '**/*.hosted.mjs',
  timeout: 45 * 60_000,
  workers: 1,
  retries: 0,
  expect: { timeout: 20_000 },
  use: {
    baseURL: target.frontend,
    browserName: 'chromium',
    headless: true,
    trace: 'off', // no tokens, business data or private media in trace archives
    screenshot: 'off',
    video: 'off',
  },
  reporter: 'list',
})
