import { test, expect } from '@playwright/test'

// Configured RetailGrowthAI (even on local test server) is login-first;
// never expose tenant dashboards to guest users as a navigation shortcut.
test('single site / starts with login form, not a tenant or root dashboard', async ({ page }) => {
  await page.goto('/')
  await expect(page).toHaveURL(/\/$/)
  await expect(page.getByRole('heading', { name: 'Sign in to continue' })).toBeVisible()
  await expect(page.getByRole('button', { name: 'Sign in', exact: true })).toBeVisible()
  await expect(page.getByRole('navigation', { name: 'Main navigation' })).toHaveCount(0)
  await expect(page.getByRole('heading', { name: 'Campaign workspace' })).toHaveCount(0)
  await expect(page.getByRole('heading', { name: 'Platform Control' })).toHaveCount(0)
})

test('guest visiting campaign or superadmin route redirects to the same login', async ({ page }) => {
  for (const route of ['/campaigns', '/platform-admin', '/subscription', '/business']) {
    await page.goto(route)
    await expect(page).toHaveURL(/\/account$/)
    await expect(page.getByRole('heading', { name: 'Sign in to continue' })).toBeVisible()
  }
})

test('one login offers standard signup without separate administrator credentials', async ({ page }) => {
  await page.goto('/account')
  await expect(page.getByRole('heading', { name: 'Sign in to continue' })).toBeVisible()
  await page.getByRole('button', { name: 'Create an account' }).click()
  await expect(page.getByRole('heading', { name: 'Create your account' })).toBeVisible()
  await expect(page.getByLabel('Password')).toHaveAttribute('autocomplete', 'new-password')
  await page.getByRole('button', { name: 'Sign in', exact: true }).click()
  await expect(page.getByRole('heading', { name: 'Sign in to continue' })).toBeVisible()
})


test('signup confirmation requests redirect to this website, never a stale Supabase localhost Site URL', async ({ page }) => {
  let redirectTo = null
  await page.route('https://e2e.supabase.test/**', async route => {
    const url = new URL(route.request().url())
    if (url.pathname !== '/auth/v1/signup') {
      throw new Error('Unexpected auth route during signup: ' + url.pathname)
    }
    redirectTo = url.searchParams.get('redirect_to')
    await route.fulfill({
      status: 200, contentType: 'application/json',
      headers: { 'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Headers': 'apikey, content-type' },
      body: JSON.stringify({ user: { email: 'test-user@example.invalid' } }),
    })
  })
  await page.goto('/')
  const expected = new URL('/account', page.url()).href
  await page.getByRole('button', { name: 'Create an account' }).click()
  await page.getByLabel('Email').fill('test-user@example.invalid')
  await page.getByLabel('Password').fill('offline-only-secret')
  await page.getByRole('button', { name: 'Create account' }).click()
  await expect(page.getByText(/Registration submitted/)).toBeVisible()
  expect(redirectTo).toBe(expected)
  expect(redirectTo).not.toContain('localhost:3000')
})
