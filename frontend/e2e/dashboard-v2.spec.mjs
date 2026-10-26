import { test, expect } from '@playwright/test'

const HOST = 'https://e2e.supabase.test'
const SHOP = 'a1000000-0000-4000-8000-000000000001'
const USER = 'a9000000-0000-4000-8000-000000000001'

async function signedIn(page) {
  const calls = []
  await page.route(HOST + '/**', route => {
    const request = route.request()
    const url = new URL(request.url())
    calls.push(url.pathname)
    const responses = {
      '/auth/v1/user': { id: USER, email: 'owner@example.test' },
      '/rest/v1/rpc/retail_platform_me': false,
      '/rest/v1/rpc/retail_onboarding_status': { status: 'APPROVED', approval_required: false },
      '/rest/v1/shop_memberships': [{ shop_id: SHOP, active: true, role: 'OWNER' }],
      '/rest/v1/shops': [{ id: SHOP, name: 'Example Boutique', slug: 'example-boutique' }],
      '/rest/v1/media_assets': [
        {id: 'a1000000-0000-4000-8000-000000000010', shop_id: SHOP, license_name: 'owned', mime_type:'image/png'},
        {id: 'a1000000-0000-4000-8000-000000000020', shop_id: 'a1000000-0000-4000-8000-000000000002', license_name:'owned',mime_type:'image/jpeg'}
      ],
    }
    if (request.method() === 'OPTIONS') return route.fulfill({ status: 204, body: '',
      headers: { 'Access-Control-Allow-Origin': '*', 'Access-Control-Allow-Headers': '*' } })
    if (request.method() === 'HEAD') return route.fulfill({ status: 200,
      headers: { 'Content-Range': '*/0', 'Access-Control-Allow-Origin': '*' }, body: '' })
    if (!(url.pathname in responses)) throw Error('Unexpected API request ' + url.pathname)
    return route.fulfill({ status: 200, contentType: 'application/json',
      headers: { 'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Headers': '*' }, body: JSON.stringify(responses[url.pathname]) })
  })
  await page.addInitScript(() => sessionStorage.setItem('retailgrowthai-auth-v1', JSON.stringify({
    access_token: 'offline-test-JWT', refresh_token: 'offline-refresh', expires_at: 2000000000,
  })))
  return calls
}

test('desktop routes show honest unavailable contracts, not invented data', async ({ page }) => {
  const calls = await signedIn(page)
  await page.goto('/')
  for (const [path, heading] of [
    ['/calendar', 'Campaign calendar'], ['/creative-studio', 'Creative Studio'],
    ['/connections', 'Connected accounts'],
    ['/publishing', 'Publishing calendar & history'], ['/notifications', 'Notifications'],
    ['/settings', 'Workspace settings'],
  ]) {
    await page.goto(path)
    await expect(page.getByRole('heading', { name: heading })).toBeVisible()
    await expect(page.getByText('No fabricated live data')).toBeVisible()
  }
  await page.goto('/media-library')
  await expect(page.getByRole('heading', { name: 'Media library' })).toBeVisible()
  await expect(page.getByRole('region', { name: 'Authorized media records' }).getByText('Image a1000000')).toBeVisible()
  await expect(page.getByText('image/jpeg')).toHaveCount(0)
  expect(calls.some(path => path.includes('/retail_platform_notifications'))).toBe(false)
  expect(calls.some(path => path.includes('/social_accounts'))).toBe(false)
})

test('320px mobile drawer, new navigation, and dark mode persist without overflow', async ({ page }) => {
  await page.setViewportSize({ width: 320, height: 740 })
  await signedIn(page)
  await page.goto('/')
  await page.getByRole('button', { name: 'Switch to dark mode' }).click()
  await expect(page.locator('html')).toHaveAttribute('data-rg-theme', 'dark')
  await page.getByRole('button', { name: 'Toggle navigation' }).click()
  await page.getByRole('navigation', { name: 'Main navigation' })
    .getByRole('link', { name: 'Media library' }).click()
  await expect(page.getByRole('heading', { name: 'Media library' })).toBeVisible()
  await expect(page.locator('.retail-shell')).not.toHaveClass(/mobile-open/)
  await expect.poll(() => page.evaluate(() =>
    document.documentElement.scrollWidth <= document.documentElement.clientWidth)).toBe(true)
  await page.reload()
  await expect(page.locator('html')).toHaveAttribute('data-rg-theme', 'dark')
  await page.getByRole('button', { name: 'Switch to light mode' }).click()
  await expect(page.locator('html')).toHaveAttribute('data-rg-theme', 'light')
})

test('media library filters business-owned records without public blob URLs', async ({ page }) => {
  const calls = await signedIn(page)
  await page.goto('/media-library')
  await expect(page.getByText('1 matching registered images')).toBeVisible()
  await page.getByLabel('Search media').fill('does-not-exist')
  await expect(page.getByText('0 matching registered images')).toBeVisible()
  await page.getByLabel('Search media').fill('')
  await page.getByLabel('Media file type').selectOption('image/jpeg')
  await expect(page.getByText('0 matching registered images')).toBeVisible()
  expect(calls.filter(path=>path==='/rest/v1/media_assets')).toHaveLength(1)
  await expect(page.locator('a[href*="/storage/v1/object"]')).toHaveCount(0)
})

test('unverified guest cannot deep-link to dashboard subroutes', async ({ page }) => {
  await page.goto('/connections')
  await expect(page).toHaveURL(/\/account$/)
  await expect(page.getByRole('heading', { name: 'Connected accounts' })).toHaveCount(0)
})
