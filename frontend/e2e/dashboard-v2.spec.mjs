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
    ['/creative-studio', 'Creative Studio'],
    ['/connections', 'Connected accounts'],
    ['/publishing', 'Publishing calendar & history'], ['/notifications', 'Notifications'],
    ['/settings', 'Workspace settings'],
  ]) {
    await page.goto(path)
    await expect(page.getByRole('heading', { name: heading })).toBeVisible()
    await expect(page.getByText('No fabricated live data')).toBeVisible()
  }
  await page.goto('/calendar')
  await expect(page.getByRole('heading', { name: 'Campaign calendar' })).toBeVisible()
  await expect(page.getByRole('button', { name: 'Load recent campaign' })).toBeVisible()
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

test('calendar verifies last campaign against JWT shop and denies cross-tenant days', async ({ page }) => {
  await signedIn(page)
  const CAMPAIGN = 'c1000000-0000-4000-8000-000000000001'
  let foreign = false
  const apiCalls = []
  await page.route('https://api.e2e.retailgrowth.test/**', route => {
    const req = route.request()
    apiCalls.push({ method: req.method(), url: req.url(), auth: req.headers()['authorization'] })
    const headers = { 'Access-Control-Allow-Origin': '*', 'Access-Control-Allow-Headers': 'authorization,content-type' }
    if (req.method() === 'OPTIONS') return route.fulfill({ status: 204, headers, body:'' })
    return route.fulfill({ status: 200, headers, contentType: 'application/json',
      body: JSON.stringify({id: CAMPAIGN,
        shop_id: foreign ? 'a1000000-0000-4000-8000-000000000002' : SHOP,
        status: 'DRAFT', days: [{
          id: 'd1000000-0000-4000-8000-000000000001',campaign_id: CAMPAIGN,
          shop_id: foreign ? 'a1000000-0000-4000-8000-000000000002' : SHOP,
          day_index: 1, scheduled_date:'2026-11-07',topic:'Approved draft example',
          review_status: 'DRAFT'
        }] })
    })
  })
  await page.addInitScript(({user,shop,campaign}) => sessionStorage.setItem(
    'retailgrowthai-last-campaign:' + user + ':' + shop, campaign
  ), {user:USER,shop:SHOP,campaign:CAMPAIGN})
  await page.goto('/calendar')
  expect(apiCalls).toHaveLength(0)
  await page.getByRole('button', { name: 'Load recent campaign' }).click()
  await expect(page.getByText('Approved draft example')).toBeVisible()
  await expect(page.getByText('Not published')).toBeVisible()
  expect(apiCalls.filter(x=>x.method==='GET')).toHaveLength(1)
  expect(apiCalls.some(x=>x.method==='GET' && x.auth==='Bearer offline-test-JWT')).toBe(true)
  foreign = true
  await page.getByRole('button', { name: 'Load recent campaign' }).click()
  await expect(page.getByRole('alert')).toContainText('No dates or posts are assumed')
  await expect(page.getByText('Approved draft example')).toHaveCount(0)
})

test('unverified guest cannot deep-link to dashboard subroutes', async ({ page }) => {
  await page.goto('/connections')
  await expect(page).toHaveURL(/\/account$/)
  await expect(page.getByRole('heading', { name: 'Connected accounts' })).toHaveCount(0)
})
