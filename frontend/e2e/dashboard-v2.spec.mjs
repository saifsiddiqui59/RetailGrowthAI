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

test('business settings saves only validated fields with JWT and real server confirmation', async ({ page }) => {
  await signedIn(page)
  const profile = { shop_id: SHOP, business_name: 'Example Boutique', category:'Clothing',
    description:'Sample description', brand_voice:'Warm', city:'Nagpur',
    website_url:'', contact_email:'' }
  const writes = []
  await page.route(HOST + '/rest/v1/business_profiles**', route => {
    const req = route.request()
    if (req.method() === 'PATCH') {
      writes.push({body: JSON.parse(req.postData() || '{}'), auth:req.headers()['authorization']})
      return route.fulfill({status:200,contentType:'application/json',
        headers:{'Access-Control-Allow-Origin':'*','Access-Control-Allow-Headers':'*'},
        body:JSON.stringify([{...profile,...writes.at(-1).body}])})
    }
    return route.fulfill({status:200,contentType:'application/json',
      headers:{'Access-Control-Allow-Origin':'*','Access-Control-Allow-Headers':'*'},
      body:JSON.stringify([profile])})
  })
  await page.goto('/settings')
  const editor = page.getByRole('form', {name:'Business profile settings'})
  await expect(editor.getByLabel('Business name')).toHaveValue('Example Boutique')
  await expect(editor.getByRole('button',{name:'Save business profile'})).toBeDisabled()
  await editor.getByLabel('City').fill('Pune')
  await editor.getByRole('button',{name:'Save business profile'}).click()
  await expect(page.getByText('Business profile saved and verified for this business.')).toBeVisible()
  expect(writes).toHaveLength(1)
  expect(writes[0].auth).toBe('Bearer offline-test-JWT')
  expect(writes[0].body.city).toBe('Pune')
  // Existing Supabase client always includes updated_at on profile edits.
  expect(Object.keys(writes[0].body).sort()).toEqual(['city','updated_at'])
  expect(Number.isFinite(Date.parse(writes[0].body.updated_at))).toBe(true)
})

test('settings shows VIEWER profile without issuing any mutation', async ({ page }) => {
  await signedIn(page)
  const profile = {shop_id:SHOP,business_name:'Viewer Business',category:'Retail',
    description:'',brand_voice:'',city:'',website_url:'',contact_email:''}
  const methods = []
  await page.route(HOST + '/rest/v1/shop_memberships**',route => route.fulfill({
    status:200,contentType:'application/json',
    headers:{'Access-Control-Allow-Origin':'*','Access-Control-Allow-Headers':'*'},
    body:JSON.stringify([{shop_id:SHOP,active:true,role:'VIEWER'}])
  }))
  await page.route(HOST + '/rest/v1/business_profiles**',route => {
    methods.push(route.request().method())
    return route.fulfill({status:200,contentType:'application/json',
      headers:{'Access-Control-Allow-Origin':'*','Access-Control-Allow-Headers':'*'},
      body:JSON.stringify([profile])})
  })
  await page.goto('/settings')
  const editor=page.getByRole('form',{name:'Business profile settings'})
  await expect(editor.getByLabel('Business name')).toHaveValue('Viewer Business')
  await expect(editor.getByLabel('Business name')).toHaveAttribute('readonly','')
  await expect(editor.getByRole('button',{name:'Save business profile'})).toBeDisabled()
  expect(methods).toEqual(['GET'])
})

test('settings refuses cross-tenant profile response and never shows foreign data', async ({page})=>{
  await signedIn(page)
  await page.route(HOST + '/rest/v1/business_profiles**',route=>route.fulfill({
    status:200,contentType:'application/json',
    headers:{'Access-Control-Allow-Origin':'*','Access-Control-Allow-Headers':'*'},
    body:JSON.stringify([{shop_id:'a1000000-0000-4000-8000-000000000002',
      business_name:'Foreign Retailer',category:'Other'}])
  }))
  await page.goto('/settings')
  await expect(page.getByRole('alert')).toContainText('Profile cannot be verified')
  await expect(page.getByText('Foreign Retailer')).toHaveCount(0)
  await expect(page.getByRole('button',{name:'Save business profile'})).toHaveCount(0)
})

test('rapid workspace navigation reuses principal-scoped shop list without extra GET', async ({ page }) => {
  const calls = await signedIn(page)
  await page.route(HOST + '/rest/v1/business_profiles**', route => route.fulfill({
    status:200, contentType:'application/json',
    headers:{'Access-Control-Allow-Origin':'*','Access-Control-Allow-Headers':'*'},
    body:'[]'
  }))
  await page.goto('/')
  await expect(page.getByRole('heading',{name:'Campaign workspace'})).toBeVisible()
  await expect.poll(()=>calls.filter(path=>path==='/rest/v1/shops').length).toBe(1)
  await page.getByRole('navigation',{name:'Main navigation'}).getByRole('link',{name:'Media library'}).click()
  await expect(page.getByRole('heading',{name:'Media library'})).toBeVisible()
  await page.getByRole('navigation',{name:'Main navigation'}).getByRole('link',{name:'Settings'}).click()
  await expect(page.getByRole('heading',{name:'Workspace settings'})).toBeVisible()
  expect(calls.filter(path=>path==='/rest/v1/shops')).toHaveLength(1)
})

test('selected business persists across all Feature 1 routes using verified memberships', async ({ page }) => {
  const SECOND = 'a1000000-0000-4000-8000-000000000002'
  const calls = await signedIn(page)
  await page.route(HOST + '/rest/v1/shop_memberships**',route=>route.fulfill({
    status:200,contentType:'application/json',
    headers:{'Access-Control-Allow-Origin':'*','Access-Control-Allow-Headers':'*'},
    body:JSON.stringify([{shop_id:SHOP,active:true,role:'OWNER'}, {shop_id:SECOND,active:true,role:'EDITOR'}])
  }))
  await page.route(HOST + '/rest/v1/shops**',route=>route.fulfill({
    status:200,contentType:'application/json',
    headers:{'Access-Control-Allow-Origin':'*','Access-Control-Allow-Headers':'*'},
    body:JSON.stringify([{id:SHOP,name:'Example Boutique',slug:'example-boutique'},
      {id:SECOND,name:'Second Shop',slug:'second-shop'}])
  }))
  await page.route(HOST + '/rest/v1/media_assets**',route=>route.fulfill({
    status:200,contentType:'application/json',
    headers:{'Access-Control-Allow-Origin':'*','Access-Control-Allow-Headers':'*'},
    body:'[]'
  }))
  await page.route(HOST + '/rest/v1/business_profiles**',route=>route.fulfill({
    status:200,contentType:'application/json',
    headers:{'Access-Control-Allow-Origin':'*','Access-Control-Allow-Headers':'*'},
    body:'[]'
  }))
  await page.goto('/')
  await expect(page.getByLabel('Dashboard business')).toHaveValue(SHOP)
  await page.getByLabel('Dashboard business').selectOption(SECOND)
  await page.getByRole('navigation',{name:'Main navigation'}).getByRole('link',{name:'Media library'}).click()
  await expect(page.getByLabel('Media library business')).toHaveValue(SECOND)
  await page.getByRole('navigation',{name:'Main navigation'}).getByRole('link',{name:'Settings'}).click()
  await expect(page.getByLabel('Settings business')).toHaveValue(SECOND)
  await page.getByRole('navigation',{name:'Main navigation'}).getByRole('link',{name:'Campaign calendar'}).click()
  await expect(page.getByLabel('Calendar business')).toHaveValue(SECOND)
  await page.reload()
  await expect(page.getByLabel('Calendar business')).toHaveValue(SECOND)
  expect(await page.evaluate(user=>sessionStorage.getItem('retailgrowthai-selected-business:'+user),USER)).toBe(SECOND)
  expect(calls.some(path=>path.includes('/retail_platform_notifications'))).toBe(false)
})

test('stored business ID not in membership cannot drive data requests', async ({ page }) => {
  const forged = 'a1000000-0000-4000-8000-000000000009'
  const calls = await signedIn(page)
  await page.addInitScript(({user,shop}) =>
    sessionStorage.setItem('retailgrowthai-selected-business:'+user,shop),
    {user:USER,shop:forged})
  await page.goto('/media-library')
  await expect(page.getByLabel('Media library business')).toHaveValue(SHOP)
  await expect(page.getByText('1 matching registered images')).toBeVisible()
  await expect.poll(()=>calls.filter(path=>path==='/rest/v1/media_assets').length).toBe(1)
  // Never issue a query for a forged shop that is absent from the signed-in
  // member list; the server retains RLS as the decisive authorization layer.
  expect(await page.evaluate(user=>sessionStorage.getItem('retailgrowthai-selected-business:'+user),USER)).toBe(forged)
})

test('unverified guest cannot deep-link to dashboard subroutes', async ({ page }) => {
  await page.goto('/connections')
  await expect(page).toHaveURL(/\/account$/)
  await expect(page.getByRole('heading', { name: 'Connected accounts' })).toHaveCount(0)
})
