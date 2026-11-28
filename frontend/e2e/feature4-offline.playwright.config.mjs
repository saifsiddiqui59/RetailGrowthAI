// Offline-only browser configuration. Never use hosted credentials or flags.
import { defineConfig } from '@playwright/test'
import base from './playwright.config.mjs'
export default defineConfig({
  ...base,
  testMatch: 'feature4-review.f4-check.mjs',
  webServer: {
    ...base.webServer,
    env: {
      ...base.webServer.env,
      VITE_FEATURE4_PLAN_REVIEW_ENABLED:'true',
      VITE_FEATURE4_PLAN_ISSUE_ENABLED:'false',
      VITE_FEATURE4_CPU_RENDER_ENABLED:'true',
    },
  },
})
