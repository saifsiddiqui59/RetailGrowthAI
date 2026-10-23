import { test, expect } from '@playwright/test'

const HOST = 'https://e2e.supabase.test'
const SHOP = 'a1000000-0000-4000-8000-000000000001'
const USER = 'a9000000-0000-4000-8000-000000000001'
function response(route, json) {
  return route.fulfill({
    status: 200, contentType: 'application/json',
    headers: { 'Access-Control-Allow-Origin': '*', 'Access-Control-Allow-Headers': '*' },
    body: JSON.stringify(json),
  })
}
async function mockUser(page, { viewer = false, failMetric = false } = {}) {
  const requests = []
  await page.route(HOST + '/**', async route => {
    const request = route.request()
    const u = new URL(request.url())
    const path = u.pathname
    requests.push({ path, method: request.method(), query: u.searchParams, headers: request.headers() })
    if (request.method() === 'OPTIONS') return response(route, {})
    if (path === '/auth/v1/user') return response(route, { id: USER, email: 'owner@example.test' })
    if (path === '/rest/v1/rpc/retail_platform_me') return response(route, false)
    if (path === '/rest/v1/shop_memberships') return response(route, [{ shop_id: SHOP, active: true,
      role: viewer ? 'VIEWER' : 'OWNER' }])
    if (path === '/rest/v1/shops') return response(route, [{ id: SHOP, name: 'Test Boutique', slug: 'test-boutique' }])
    if (request.method() === 'HEAD' && path.startsWith('/rest/v1/')) {
      return route.fulfill({
        status: failMetric ? 503 : 200,
        headers: { 'Content-Range': failMetric ? '*/0' : '0-0/1',
          'Access-Control-Allow-Origin': '*', 'Access-Control-Expose-Headers': 'Content-Range' },
        body: '',
      })
    }
    if (path === '/rest/v1/shop_subscriptions') return response(route, [{
      shop_id: SHOP, plan_code: 'TRIAL', status: 'TRIAL',
      valid_from: '2026-10-23T00:00:00Z',
      valid_until: '2099-10-30T00:00:00Z',
      period_start: '2026-10-23T00:00:00Z',
      period_end: '2099-10-30T00:00:00Z',
    }])
    if (path === '/rest/v1/business_profiles') return response(route, [])
    throw new Error('Unexpected test request ' + request.method() + ' ' + path)
  })
  await page.addInitScript(() => sessionStorage.setItem('retailgrowthai-auth-v1', JSON.stringify({
    access_token: 'offline-test-JWT', refresh_token: 'offline-refresh', expires_at: 2000000000,
  })))
  return requests
}

test('top-right account route, collapsible sidebar, and new subscription link work', async ({ page }) => {
  await mockUser(page)
  await page.goto('/')
  await expect(page.getByRole('button', { name: 'Open account menu' })).toBeVisible()
  await expect(page.getByRole('navigation', { name: 'Main navigation' })
    .getByRole('link', { name: 'Subscription' })).toBeVisible()
  await page.getByRole('button', { name: 'Collapse sidebar' }).click()
  await expect(page.getByRole('button', { name: 'Expand sidebar' })).toBeVisible()
  await expect(page.locator('.retail-shell')).toHaveClass(/sidebar-collapsed/)
  await page.reload()
  await expect(page.locator('.retail-shell')).toHaveClass(/sidebar-collapsed/)
  await page.getByRole('button', { name: 'Expand sidebar' }).click()
  await page.getByRole('navigation', { name: 'Main navigation' }).getByRole('link', { name: 'Subscription' }).click()
  await expect(page).toHaveURL(/\/subscription$/)
  await expect(page.getByRole('heading', { name: 'Subscription & plans' })).toBeVisible()
  await expect(page.getByText('No paid upgrades, payment checkout', { exact: false })).toBeVisible()
})

test('owner sees true RLS HEAD metrics, top-right account menu and quota status', async ({ page }) => {
  const requests = await mockUser(page)
  await page.goto('/')
  await expect(page.getByRole('button', { name: 'Open account menu' })).toBeVisible()
  await expect(page.getByRole('region', { name: 'Live business metrics' })
    .getByText('Campaigns created')).toBeVisible()
  await expect(page.getByRole('region', { name: 'Live business metrics' })
    .getByText('1', { exact: true }).first()).toBeVisible()
  const counts = requests.filter(r => r.method === 'HEAD')
  expect(counts).toHaveLength(4)
  expect(counts.every(r => r.headers.authorization === 'Bearer offline-test-JWT')).toBe(true)
  expect(counts.every(r => r.query.get('shop_id') === 'eq.' + SHOP)).toBe(true)
  await page.getByRole('button', { name: 'Open account menu' }).click()
  await page.getByRole('menuitem', { name: 'Plan & usage' }).click()
  await expect(page.getByText('TRIAL plan')).toBeVisible()
  await expect(page.getByText('1 of 2 used · 1 remaining').first()).toBeVisible()
  const reservations = requests.filter(r => r.path === '/rest/v1/shop_usage_reservations')
  expect(reservations).toHaveLength(2)
  expect(reservations.every(r => r.method === 'HEAD' && r.query.get('shop_id') === 'eq.' + SHOP)).toBe(true)
})

test('viewer subscription usage is inaccessible and unavailable metrics are never invented', async ({ page }) => {
  const requests = await mockUser(page, { viewer: true, failMetric: true })
  await page.goto('/')
  await expect(page.getByRole('alert')).toContainText('No totals are estimated')
  await page.goto('/subscription')
  await expect(page.getByText('Only the business OWNER can view plan')).toBeVisible()
  expect(requests.some(r => r.path === '/rest/v1/shop_subscriptions')).toBe(false)
  expect(requests.some(r => r.path === '/rest/v1/shop_usage_reservations')).toBe(false)
})
