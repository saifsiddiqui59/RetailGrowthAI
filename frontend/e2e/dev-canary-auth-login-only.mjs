// Real hosted DEV Playwright login/logout for two disposable Auth-only users.
// Called ONLY by the existing protected workflow; no shop, ROOT or paid calls.
import { chromium, expect } from '@playwright/test'

const FRONTEND = 'https://purple-dune-06b5da200.2.azurestaticapps.net'
const SYNTHETIC_EMAIL = /^rgai-p0249-jwt-[0-9a-f]{16}@example\.invalid$/
const users = [
  { email: process.env.RGAI_DEV_LOGIN_A_EMAIL || '', password: process.env.RGAI_DEV_LOGIN_A_PASSWORD || '' },
  { email: process.env.RGAI_DEV_LOGIN_B_EMAIL || '', password: process.env.RGAI_DEV_LOGIN_B_PASSWORD || '' },
]
let stage = 'guard'
let browser

async function main() {
  if (process.env.GITHUB_ACTIONS !== 'true' ||
      process.env.RGAI_DEV_CANARY_APPROVAL !== 'AUTHORIZED_RETAILGROWTHAI_DEV_ONLY' ||
      process.env.RGAI_DEV_LOGIN_ONLY !== '1' ||
      users.some(user => !SYNTHETIC_EMAIL.test(user.email) || user.password.length < 24) ||
      users[0].email === users[1].email || users[0].password === users[1].password) {
    throw new Error('Protected DEV synthetic credentials required')
  }
  stage = 'chromium'
  browser = await chromium.launch({ headless: true })
  for (const [index, user] of users.entries()) {
    stage = `signin-${index + 1}`
    const context = await browser.newContext({
      serviceWorkers: 'block', acceptDownloads: false,
      recordVideo: undefined,
    })
    try {
      const page = await context.newPage()
      await page.goto(FRONTEND + '/account', { waitUntil: 'domcontentloaded', timeout: 30000 })
      await expect(page.getByRole('heading', { name: 'Sign in to continue' })).toBeVisible({ timeout: 30000 })
      await page.getByLabel('Email', { exact: true }).fill(user.email)
      await page.getByLabel('Password', { exact: true }).fill(user.password)
      await page.getByRole('button', { name: 'Sign in', exact: true }).click()
      await expect(page.getByText('Signed in as ' + user.email)).toBeVisible({ timeout: 30000 })
      await expect(page.getByRole('heading', { name: 'Your businesses' })).toBeVisible()
      await expect(page.getByText('No businesses yet. Create one below.')).toBeVisible()
      console.log(`P0249_PLAYWRIGHT_REAL_AUTH_LOGIN_USER_${index + 1}=PASS`)
      stage = `signout-${index + 1}`
      await page.getByRole('button', { name: 'Sign out', exact: true }).click()
      await expect(page.getByRole('heading', { name: 'Sign in to continue' })).toBeVisible({ timeout: 30000 })
      console.log(`P0249_PLAYWRIGHT_REAL_AUTH_LOGOUT_USER_${index + 1}=PASS`)
    } finally {
      await context.close()
    }
  }
  console.log('P0249_PLAYWRIGHT_TWO_DISPOSABLE_AUTH_LOGINS=PASS')
}

try {
  await main()
} catch {
  // Never print credentials, tokens, URL query strings, page content or screenshots.
  console.error('P0249_PLAYWRIGHT_AUTH_ONLY_FAILED_STAGE=' + stage)
  process.exitCode = 1
} finally {
  if (browser) await browser.close()
}
