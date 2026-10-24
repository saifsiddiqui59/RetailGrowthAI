/**
 * Real Azure Free SWA public login smoke only. No sign in, user emails,
 * password entry, account creation, backend mutation or privileged auth.
 * Output screenshots contain anonymous, public login UI only.
 */
import { chromium, expect } from '@playwright/test'
import { mkdir } from 'node:fs/promises'

const BASE = 'https://purple-dune-06b5da200.2.azurestaticapps.net'
const OUT = 'output/public-login-qa'

async function run() {
  await mkdir(OUT, { recursive: true })
  const browser = await chromium.launch({ headless: true })
  try {
    for (const [label, width, height] of [
      ['desktop', 1440, 900],
      ['iphone-like', 390, 844],
      ['narrow-mobile', 320, 740],
      ['tablet', 768, 900],
    ]) {
      const page = await browser.newPage({
        viewport: { width, height }, deviceScaleFactor: 1,
      })
      try {
        const response = await page.goto(BASE + '/account', {
          waitUntil: 'domcontentloaded', timeout: 40_000,
        })
        if (!response || response.status() !== 200) {
          throw new Error('Hosted DEV /account failed public HTTPS load')
        }
        await expect(page.getByRole('heading', { name: 'Sign in to continue' }))
          .toBeVisible({ timeout: 20_000 })
        await expect(page.getByLabel('Email')).toBeVisible()
        await expect(page.getByRole('button', { name: 'Sign in', exact: true })).toBeVisible()
        const dims = await page.evaluate(() => {
          const card = document.querySelector('.login-card')
          if (!card) return null
          const r = card.getBoundingClientRect()
          return {
            scrollWidth: document.documentElement.scrollWidth,
            viewport: window.innerWidth,
            left: r.left, right: r.right,
          }
        })
        if (!dims || dims.scrollWidth > dims.viewport + 1 ||
            dims.left < -1 || dims.right > dims.viewport + 1) {
          throw new Error('Hosted anonymous login has horizontal overflow')
        }
        if (width <= 768) {
          await expect(page.locator('.login-mobile-brand')).toBeVisible()
          await expect(page.locator('.login-story')).toBeHidden()
        } else {
          await expect(page.locator('.login-story')).toBeVisible()
        }
        await page.screenshot({ path: OUT + '/' + label + '.png', fullPage: true })
        await page.getByRole('button', { name: 'Create an account' }).click()
        await expect(page.getByRole('heading', { name: 'Create your account' })).toBeVisible()
        await page.getByRole('button', { name: 'Sign in', exact: true }).click()
        await page.getByRole('button', { name: 'Forgot password?' }).click()
        await expect(page.getByRole('heading', { name: 'Reset your password' })).toBeVisible()
        // Do NOT submit email or create any account.
        console.log('PUBLIC_LOGIN_RESPONSIVE_PASS=' + label)
      } finally {
        await page.close()
      }
    }
    const page = await browser.newPage()
    try {
      for (const path of ['/campaigns', '/platform-admin', '/platform-alerts']) {
        const response = await page.goto(BASE + path, {
          waitUntil: 'domcontentloaded', timeout: 40_000,
        })
        if (!response || response.status() !== 200)
          throw new Error('Protected SPA path failed HTTPS shell')
        await expect(page.getByRole('heading', { name: 'Sign in to continue' }))
          .toBeVisible({ timeout: 20_000 })
        if (await page.locator('[data-private-campaign]').count() !== 0)
          throw new Error('Private campaign leaked into anonymous browser')
        console.log('PUBLIC_PROTECTED_ROUTE_DENIED=' + path)
      }
    } finally {
      await page.close()
    }
    console.log('PUBLIC_DEV_BROWSER_SMOKE=PASS')
  } finally {
    await browser.close()
  }
}
run().catch(() => {
  // Do not print potentially private browser/response stack or URL details.
  console.error('PUBLIC_DEV_BROWSER_SMOKE=FAIL')
  process.exitCode = 1
})
