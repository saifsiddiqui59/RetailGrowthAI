import { test, expect } from '@playwright/test'

test('desktop login has decorative branded background without hiding auth controls', async ({ page }) => {
  await page.setViewportSize({ width: 1440, height: 900 })
  await page.goto('/')
  await expect(page.locator('.login-story')).toBeVisible()
  await expect(page.getByRole('heading', { name: 'Sign in to continue' })).toBeVisible()
  await expect(page.getByLabel('Email')).toBeVisible()
  const background = await page.locator('.login-story').evaluate((node) => getComputedStyle(node).backgroundImage)
  expect(background).toContain('gradient')
  const formBackground = await page.locator('.login-form-side').evaluate((node) => getComputedStyle(node).backgroundImage)
  expect(formBackground).toContain('gradient')
})

test('mobile login, signup and password recovery stay usable on narrow screens', async ({ page }) => {
  for (const width of [320, 375, 390, 768]) {
    await page.setViewportSize({ width, height: 780 })
    await page.goto('/')
    await expect(page.locator('.login-story')).toBeHidden()
    await expect(page.locator('.login-mobile-brand')).toBeVisible()
    await expect(page.getByRole('heading', { name: 'Sign in to continue' })).toBeVisible()
    await expect(page.getByRole('button', { name: 'Sign in', exact: true })).toBeVisible()

    const mobile = await page.evaluate(() => {
      const form = document.querySelector('.login-card')
      const rect = form.getBoundingClientRect()
      return { scrollWidth: document.documentElement.scrollWidth,
        viewportWidth: window.innerWidth, cardLeft: rect.left, cardRight: rect.right,
        background: getComputedStyle(document.querySelector('.login-form-side')).backgroundImage }
    })
    expect(mobile.scrollWidth).toBeLessThanOrEqual(mobile.viewportWidth + 1)
    expect(mobile.cardLeft).toBeGreaterThanOrEqual(-1)
    expect(mobile.cardRight).toBeLessThanOrEqual(mobile.viewportWidth + 1)
    expect(mobile.background).toContain('gradient')

    await page.getByRole('button', { name: 'Create an account' }).click()
    await expect(page.getByRole('heading', { name: 'Create your account' })).toBeVisible()
    await page.getByRole('button', { name: 'Sign in', exact: true }).click()
    await page.getByRole('button', { name: 'Forgot password?' }).click()
    await expect(page.getByRole('heading', { name: 'Reset your password' })).toBeVisible()
    await page.getByRole('button', { name: 'Sign in', exact: true }).click()
  }
})
