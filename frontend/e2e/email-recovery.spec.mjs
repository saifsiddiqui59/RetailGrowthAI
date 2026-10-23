import { test, expect } from '@playwright/test'

const HOST = 'https://e2e.supabase.test'
function reply(route, data, status = 200) {
  return route.fulfill({ status, contentType: 'application/json',
    headers: { 'Access-Control-Allow-Origin': '*',
      'Access-Control-Allow-Methods': 'GET, POST, PUT, OPTIONS',
      'Access-Control-Allow-Headers': 'apikey, authorization, content-type' },
    body: JSON.stringify(data) })
}

test('password reset request targets this website and does not expose account existence', async ({ page }) => {
  const targets = []
  await page.route(HOST + '/**', route => {
    const request = route.request()
    const url = new URL(request.url())
    if (request.method() === 'OPTIONS') return reply(route, {})
    if (url.pathname === '/auth/v1/recover') {
      targets.push({ method: request.method(), redirect: url.searchParams.get('redirect_to'),
        email: request.postDataJSON().email })
      return reply(route, {})
    }
    throw new Error('Unexpected request ' + url.pathname)
  })
  await page.goto('/account')
  await page.getByRole('button', { name: 'Forgot password?' }).click()
  await expect(page.getByRole('heading', { name: 'Reset your password' })).toBeVisible()
  await page.getByLabel('Email').fill('offline-user@example.invalid')
  await page.getByRole('button', { name: 'Email reset link' }).click()
  await expect(page.getByRole('status')).toContainText('If this email has an account')
  expect(targets).toEqual([{ method: 'POST',
    redirect: new URL('/account', page.url()).href, email: 'offline-user@example.invalid' }])
})

test('verified recovery link clears fragment, resets password and signs out', async ({ page }) => {
  const requests = []
  await page.route(HOST + '/**', route => {
    const request = route.request()
    const u = new URL(request.url())
    requests.push({ path: u.pathname, method: request.method(),
      body: request.postDataJSON?.() })
    if (request.method() === 'OPTIONS') return reply(route, {})
    if (u.pathname === '/auth/v1/user' && request.method() === 'GET') {
      return reply(route, { id: '12345678-1234-4123-8123-123456789abc',
        email: 'offline-user@example.invalid' })
    }
    if (u.pathname === '/auth/v1/user' && request.method() === 'PUT') return reply(route, {})
    if (u.pathname === '/auth/v1/logout') return reply(route, {})
    if (u.pathname === '/rest/v1/rpc/retail_platform_me') return reply(route, false)
    throw new Error('Unexpected request ' + request.method() + ' ' + u.pathname)
  })
  await page.goto('/account#access_token=offline-access-token&refresh_token=offline-refresh-token&type=recovery&expires_in=3600')
  await expect(page.getByRole('heading', { name: 'Set a new password' })).toBeVisible()
  expect(page.url()).toBe(new URL('/account', page.url()).href)
  await expect(page.getByRole('heading', { name: 'Platform Control' })).toHaveCount(0)
  await page.getByLabel('Password').fill('example-only-strong-password')
  await page.getByLabel('Confirm new password').fill('example-only-strong-password')
  await page.getByRole('button', { name: 'Save new password' }).click()
  await expect(page.getByText('Password updated. Sign in using your new password.')).toBeVisible()
  await expect(page.getByRole('heading', { name: 'Sign in to continue' })).toBeVisible()
  const change = requests.filter(x => x.path === '/auth/v1/user' && x.method === 'PUT')
  expect(change).toHaveLength(1)
  expect(change[0].body.password).toBe('example-only-strong-password')
  expect(requests.filter(x => x.path === '/auth/v1/logout')).toHaveLength(1)
})

test('invalid recovery email tokens never expose a tenant dashboard', async ({ page }) => {
  await page.goto('/account#access_token=bad&type=recovery')
  await expect(page.getByRole('heading', { name: 'Sign in to continue' })).toBeVisible()
  await expect(page.getByRole('navigation', { name: 'Main navigation' })).toHaveCount(0)
  expect(page.url()).toBe(new URL('/account', page.url()).href)
})
