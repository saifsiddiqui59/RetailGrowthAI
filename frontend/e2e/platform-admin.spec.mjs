import { test, expect } from '@playwright/test'

const SUPABASE = 'https://e2e.supabase.test'
const SHOP = 'f1000000-0000-4000-8000-000000000011'
const USER = 'f1000000-0000-4000-8000-000000000001'
const roles = ['ROOT', 'OWNER', 'EDITOR', 'VIEWER']

function fulfill(route, body, status = 200) {
  return route.fulfill({
    status, contentType: 'application/json',
    headers: { 'Access-Control-Allow-Origin': '*',
      'Access-Control-Allow-Headers': 'apikey, authorization, content-type',
    }, body: JSON.stringify(body),
  })
}
async function loginAs(page, role, { invalid = false } = {}) {
  const requests = []
  await page.route(SUPABASE + '/**', async route => {
    const req = route.request()
    const u = new URL(req.url())
    const path = u.pathname
    requests.push({ path, method: req.method(), body: req.postDataJSON?.() })
    if (req.method() === 'OPTIONS') return fulfill(route, {})
    if (req.method() === 'HEAD' && ['/rest/v1/campaigns','/rest/v1/render_jobs'].includes(path)) {
      return route.fulfill({ status: 200, headers: {
        'Content-Range': '*/0', 'Access-Control-Allow-Origin': '*',
        'Access-Control-Expose-Headers': 'Content-Range',
      }, body: '' })
    }
    if (path === '/auth/v1/token' && u.searchParams.get('grant_type') === 'password') {
      return invalid ? fulfill(route, { error_description: 'Invalid login credentials' }, 400)
        : fulfill(route, { access_token: 'role-jwt', refresh_token: 'role-refresh',
            expires_in: 3600, user: { id: USER, email: role.toLowerCase() + '@example.invalid' } })
    }
    if (path === '/auth/v1/user') return fulfill(route, { id: USER, email: role.toLowerCase() + '@example.invalid' })
    if (path === '/auth/v1/logout') return fulfill(route, {})
    if (path === '/rest/v1/rpc/retail_platform_me') return fulfill(route, role === 'ROOT')
    if (path === '/rest/v1/rpc/retail_onboarding_status') return fulfill(route, {status:'APPROVED',approval_required:false})
    if (path === '/rest/v1/rpc/retail_platform_summary') {
      return role === 'ROOT'
        ? fulfill(route, { retailers: 1, trial_shops: 1, active_paid_shops: 0,
            expired_or_suspended: 0, campaigns: 2, reels_completed: 1 })
        : fulfill(route, { message: 'PLATFORM_ADMIN_REQUIRED' }, 403)
    }
    if (path === '/rest/v1/rpc/retail_platform_shops') {
      return role === 'ROOT'
        ? fulfill(route, { total: 1, shops: [{ shop_id: SHOP,
            name: 'Test Retailer', slug: 'test-retailer', plan_code: 'TRIAL',
            subscription_status: 'TRIAL', campaigns: 2, renders: 1,
            valid_until: '2099-10-01T00:00:00Z' }] })
        : fulfill(route, { message: 'PLATFORM_ADMIN_REQUIRED' }, 403)
    }
    if (path === '/rest/v1/rpc/retail_platform_subscription_watch') {
      return role === 'ROOT' ? fulfill(route, {
        total:1,all_retailers:56,counts:{expiring:5,expired:4,suspended:2,unknown:1,healthy:44},
        shops:[{shop_id:SHOP,name:'Test Retailer',slug:'test-retailer',plan_code:'TRIAL',
          subscription_status:'TRIAL',health:'healthy',valid_until:'2099-10-01T00:00:00Z'}],
      }) : fulfill(route,{message:'PLATFORM_ADMIN_REQUIRED'},403)
    }
    if (path === '/rest/v1/rpc/retail_platform_set_subscription') {
      return role === 'ROOT'
        ? fulfill(route, { shop_id: SHOP, plan_code: 'GROWTH', status: 'ACTIVE' })
        : fulfill(route, { message: 'PLATFORM_ADMIN_REQUIRED' }, 403)
    }
    if (path === '/rest/v1/shop_memberships') return fulfill(route, role === 'ROOT' ? [] : [{
      shop_id: SHOP, role, active: true,
    }])
    if (path === '/rest/v1/shops') return fulfill(route, role === 'ROOT' ? [] : [{
      id: SHOP, name: 'Test Retailer', slug: 'test-retailer',
    }])
    if (path === '/rest/v1/business_profiles') return fulfill(route, [])
    if (path === '/rest/v1/shop_subscriptions') return fulfill(route, [])
    throw new Error('Unexpected mock request: ' + req.method() + ' ' + path)
  })
  await page.goto('/account')
  await page.getByLabel('Email').fill(role.toLowerCase() + '@example.invalid')
  await page.getByLabel('Password').fill(invalid ? 'wrong-password' : 'offline-only-password')
  await page.getByRole('button', { name: 'Sign in', exact: true }).click()
  // Wait for the actual Supabase user and server-side platform grant to settle
  // before any test reloads the SPA or asserts route isolation. This guards
  // against a raced reload, not against denied roles.
  if (!invalid) {
    await expect(page.getByText('Signed in as ' + role.toLowerCase() + '@example.invalid')).toBeVisible()
    if (role === 'ROOT') await expect(page.getByRole('navigation', { name: 'Main navigation' })
      .getByRole('link', { name: 'Platform Control' })).toBeVisible()
  }
  return requests
}

test('ROOT uses ordinary login, sees platform menu, cross-retailer metrics, audited change', async ({ page }) => {
  const calls = await loginAs(page, 'ROOT')
  await expect(page.getByText('Signed in as root@example.invalid')).toBeVisible()
  const nav = page.getByRole('navigation', { name: 'Main navigation' })
  await expect(nav.getByRole('link', { name: 'Platform Control' })).toBeVisible()
  await page.getByRole('button', { name: 'Open account menu' }).click()
  await expect(page.getByRole('menuitem', { name: 'Platform Control' })).toBeVisible()
  await page.getByRole('menuitem', { name: 'Platform Control' }).click()
  await expect(page.getByRole('heading', { name: 'Platform Control' })).toBeVisible()
  await expect(page.getByRole('table').getByText('Test Retailer')).toBeVisible()
  await expect(page.getByRole('region', { name: 'Platform overview metrics' })
    .getByText('Total retailers')).toBeVisible()
  await page.getByRole('table').getByRole('button', { name: 'Manage plan' }).click()
  await page.getByLabel('Subscription tier').selectOption('GROWTH')
  await page.getByLabel('Access end date').fill('2027-01-01')
  await page.getByLabel('Audit reason').fill('Approved test change with audit')
  await page.getByRole('checkbox', { name: /I approve this manual entitlement/ }).check()
  await page.getByRole('button', { name: 'Apply privileged change' }).click()
  await expect(page.getByRole('status').filter({ hasText: 'Audited subscription change saved' })).toBeVisible()
  const mutation = calls.filter(r => r.path === '/rest/v1/rpc/retail_platform_set_subscription')
  expect(mutation).toHaveLength(1)
  expect(mutation[0].body.p_plan_code).toBe('GROWTH')
  expect(mutation[0].body.p_reason).toBe('Approved test change with audit')
})

for (const role of roles.filter(x => x !== 'ROOT')) {
  test(role + ' login cannot see or call root console', async ({ page }) => {
    const calls = await loginAs(page, role)
    await expect(page.getByText('Signed in as ' + role.toLowerCase() + '@example.invalid')).toBeVisible()
    await expect(page.getByRole('navigation', { name: 'Main navigation' })
      .getByRole('link', { name: 'Platform Control' })).toHaveCount(0)
    await page.goto('/platform-admin')
    await expect(page.getByRole('heading', { name: 'Platform access denied' })).toBeVisible()
    expect(calls.filter(x => x.path === '/rest/v1/rpc/retail_platform_summary')).toHaveLength(0)
    expect(calls.filter(x => x.path === '/rest/v1/rpc/retail_platform_set_subscription')).toHaveLength(0)
  })
}

test('invalid login never opens platform console or admin API', async ({ page }) => {
  const calls = await loginAs(page, 'ROOT', { invalid: true })
  await expect(page.getByRole('alert')).toContainText('Invalid login credentials')
  await expect(page.getByRole('navigation', { name: 'Main navigation' })
    .getByRole('link', { name: 'Platform Control' })).toHaveCount(0)
  await page.goto('/platform-admin')
  await expect(page).toHaveURL(/\/account$/)
  expect(calls.filter(x => x.path.includes('/rpc/retail_platform'))).toHaveLength(0)
})


test('root arrives at SaaS control from the single home URL; warnings state what is verified', async ({ page }) => {
  await loginAs(page, 'ROOT')
  await page.goto('/')
  await expect(page).toHaveURL(/\/platform-admin$/)
  await expect(page.getByRole('heading', { name: 'Platform Control' })).toBeVisible()
  await expect(page.getByRole('region', { name: 'Platform monitoring warnings' })).toBeVisible()
  await expect(page.getByText('Payments and external platform metrics are not active')).toBeVisible()
  await expect(page.getByRole('navigation', { name: 'Main navigation' })
    .getByRole('link', { name: 'My business' })).toBeVisible()
})

test('root directory paging does not repeat global metrics RPC, reducing database requests', async ({ page }) => {
  const calls = await loginAs(page, 'ROOT')
  const directoryCalls = []
  await page.route(SUPABASE + '/rest/v1/rpc/retail_platform_shops', route => {
    const offset = route.request().postDataJSON().p_offset
    directoryCalls.push(offset)
    const rows = Array.from({length: offset ? 1 : 25}, (_,i) => ({
      shop_id: 'f1000000-0000-4000-8000-' + String(offset+i+1).padStart(12,'0'),
      name: 'Store '+(offset+i+1), slug: 'store-'+(offset+i+1),
      plan_code: 'STARTER',subscription_status:'ACTIVE',campaigns:0,renders:0,
      valid_until: '2099-10-01T00:00:00Z',
    }))
    return fulfill(route,{total:26,shops:rows})
  })
  await page.goto('/platform-admin')
  await expect(page.getByRole('table').getByText('Store 1', {exact: true})).toBeVisible()
  await expect(page.getByRole('status').filter({hasText:'26 retailers'})).toBeVisible()
  const initialSummaryReads = calls.filter(c=>c.path==='/rest/v1/rpc/retail_platform_summary').length
  const initialDirectoryReads = directoryCalls.length
  expect(initialSummaryReads).toBeGreaterThan(0)
  expect(initialDirectoryReads).toBeGreaterThan(0)
  await page.getByRole('button',{name:'Next',exact:true}).last().click()
  await expect(page.getByRole('table').getByText('Store 26')).toBeVisible()
  await expect(page.getByText('Page 2', {exact: true})).toBeVisible()
  expect(directoryCalls.at(-1)).toBe(25)
  expect(directoryCalls).toHaveLength(initialDirectoryReads + 1)
  expect(calls.filter(c=>c.path==='/rest/v1/rpc/retail_platform_summary')).toHaveLength(initialSummaryReads)
  // Existing explicit Refresh rechecks both independent server sources.
  await page.getByRole('button',{name:'Refresh',exact:true}).last().click()
  await expect.poll(() => calls.filter(c=>c.path==='/rest/v1/rpc/retail_platform_summary').length).toBe(initialSummaryReads + 1)
  await expect.poll(() => directoryCalls.length).toBe(initialDirectoryReads + 2)
})

test('a failed directory page does not invent zero platform metrics or warnings', async ({ page }) => {
  const calls = await loginAs(page, 'ROOT')
  await page.route(SUPABASE + '/rest/v1/rpc/retail_platform_shops', route => {
    const offset = route.request().postDataJSON().p_offset
    if (offset) return fulfill(route,{message:'temporary error'},503)
    return fulfill(route,{total:26,shops:Array.from({length:25},(_,i)=>({
      shop_id:'f1000000-0000-4000-8000-'+String(i+1).padStart(12,'0'),
      name:'Store '+(i+1),slug:'store-'+(i+1),campaigns:0,renders:0,
    }))})
  })
  await page.goto('/platform-admin')
  await expect(page.getByRole('region',{name:'Platform overview metrics'})
    .getByText('Total retailers')).toBeVisible()
  await expect(page.getByRole('status').filter({hasText:'26 retailers'})).toBeVisible()
  const initialSummaryReads = calls.filter(c=>c.path==='/rest/v1/rpc/retail_platform_summary').length
  expect(initialSummaryReads).toBeGreaterThan(0)
  await page.getByRole('button',{name:'Next',exact:true}).last().click()
  await expect(page.getByRole('alert')).toContainText('Retailer directory could not be verified')
  await expect(page.getByRole('region',{name:'Platform overview metrics'})
    .locator('.metric').filter({hasText:'Total retailers'}).locator('strong')).toHaveText('1')
  await expect(page.getByText('Platform monitoring is unavailable')).toHaveCount(0)
  expect(calls.filter(c=>c.path==='/rest/v1/rpc/retail_platform_summary')).toHaveLength(initialSummaryReads)
})

test('root console mobile layout uses shared cards and no subscription mutations on view',async ({page})=>{
  // The shared login helper asserts desktop sidebar visibility; verify it
  // before narrowing to the intentionally collapsed mobile navigation.
  const calls=await loginAs(page,'ROOT')
  await page.setViewportSize({width:320,height:740})
  await page.goto('/platform-admin')
  await expect(page.getByRole('heading',{name:'Platform Control'})).toBeVisible()
  await expect(page.getByRole('region',{name:'Platform overview metrics'})
    .locator('[data-slot="card"]')).toHaveCount(6)
  await expect(page.getByRole('region',{name:'Retailer approval center'}))
    .toHaveAttribute('data-slot','card')
  // Keep the hard no-overflow assertion and record the offending layout
  // geometry if the browser finds a regression at 320px.
  const layout = await page.evaluate(() => ({
    document: [document.documentElement.scrollWidth,document.documentElement.clientWidth],
    body: [document.body.scrollWidth,document.body.clientWidth],
    ancestors: ['html','body','.shell','.retail-shell','.page','.content','.platform-page','.platform-table-wrap'].map(selector => {
      const node = document.querySelector(selector)
      if (!node) return {selector,missing:true}
      const bounds = node.getBoundingClientRect()
      return {selector,left:Math.round(bounds.left),right:Math.round(bounds.right),
        width:Math.round(bounds.width),scroll:node.scrollWidth,client:node.clientWidth,
        overflowX:getComputedStyle(node).overflowX}
    }),
    overflow: Array.from(document.querySelectorAll('body *')).filter(element =>
      !element.closest('.platform-table-wrap') &&
      element.getBoundingClientRect().right > window.innerWidth - 3 &&
      getComputedStyle(element).visibility !== 'hidden').slice(0,30).map(element => ({
        element: element.tagName.toLowerCase(), className:element.getAttribute('class')?.slice(0,90),
        left:Math.round(element.getBoundingClientRect().left),
        right:Math.round(element.getBoundingClientRect().right),
        scroll:element.scrollWidth,client:element.clientWidth,
      })),
  }))
  expect(layout.document[0], JSON.stringify(layout)).toBeLessThanOrEqual(layout.document[1])
  expect(calls.filter(x=>x.path.includes('retail_platform_set_subscription'))).toHaveLength(0)
})

test('shop owner lands on own workspace rather than global SaaS metrics', async ({ page }) => {
  await loginAs(page, 'OWNER')
  await page.goto('/')
  await expect(page).toHaveURL(/\/$/)
  await expect(page.getByRole('heading', { name: 'Campaign workspace' })).toBeVisible()
  await expect(page.getByRole('region', { name: 'Platform overview metrics' })).toHaveCount(0)
  await expect(page.getByRole('navigation', { name: 'Main navigation' })
    .getByRole('link', { name: 'Platform Control' })).toHaveCount(0)
})


test('root reviews an onboarding request without exposing it to a shop user', async ({ page }) => {
  const calls = await loginAs(page, 'ROOT')
  const requested = 'f1000000-0000-4000-8000-000000000005'
  let approved = false
  await page.route(SUPABASE + '/rest/v1/rpc/retail_platform_onboarding_requests', route =>
    fulfill(route, approved ? [] : [{
      user_id: requested, email: 'new-retailer@example.invalid',
      status: 'PENDING', requested_at: '2026-10-23T18:00:00Z',
    }] ))
  await page.route(SUPABASE + '/rest/v1/rpc/retail_platform_review_onboarding', route => {
    const body = route.request().postDataJSON()
    calls.push({ path:'/rest/v1/rpc/retail_platform_review_onboarding', body })
    approved = true
    return fulfill(route, {user_id:requested,status:'APPROVED'})
  })
  await page.goto('/platform-admin')
  await page.getByRole('button', { name: 'Review requests' }).click()
  await expect(page.getByText('new-retailer@example.invalid')).toBeVisible()
  await page.getByRole('button',{name:'Review account'}).click()
  await page.getByLabel('Decision reason').fill('Verified retailer in controlled DEV test')
  await page.getByRole('checkbox',{name:/I verified this account request/}).check()
  await page.getByRole('button',{name:'Approve',exact:true}).click()
  await expect(page.getByRole('status').filter({hasText:'Retailer onboarding approved.'})).toBeVisible()
  await expect(page.getByText('No pending retailer approval requests.')).toBeVisible()
  const actions = calls.filter(c=>c.path==='/rest/v1/rpc/retail_platform_review_onboarding')
  expect(actions).toHaveLength(1)
  expect(actions[0].body).toMatchObject({
    p_user_id:requested,p_approve:true,p_reason:'Verified retailer in controlled DEV test',
  })
})

test('unapproved shop user sees pending notice and not Create business action', async ({ page }) => {
  await loginAs(page, 'OWNER')
  await page.route(SUPABASE + '/rest/v1/rpc/retail_onboarding_status',
    route=>fulfill(route,{status:'PENDING',approval_required:true}))
  await page.goto('/account')
  await expect(page.getByRole('heading',{name:'Retailer access request: PENDING'})).toBeVisible()
  await expect(page.getByRole('button',{name:'Create business'})).toHaveCount(0)
})


test('root has a persistent inbox, marks a verified signal read and can reverse it', async ({ page }) => {
  const calls=await loginAs(page,'ROOT')
  let read=false
  await page.route(SUPABASE+'/rest/v1/rpc/retail_platform_notifications',route=>{
    const body=route.request().postDataJSON()
    calls.push({path:'/rest/v1/rpc/retail_platform_notifications',body})
    return fulfill(route,{
      total_active:2,unread_active:read?1:2,database_checked_at:'2026-10-24T08:00:00Z',
      azure_telemetry:'NOT_CONNECTED',
      items:body.p_category==='queue'?[]:[{
        id:101,event_key:'job:campaign:test',category:'job',severity:'critical',
        title:'Campaign planning failed',detail:'A database-backed job ended FAILED.',
        first_seen_at:'2026-10-24T07:00:00Z',active:true,read_at:read?'2026-10-24T08:00:00Z':null,
      }],
    })
  })
  await page.route(SUPABASE+'/rest/v1/rpc/retail_platform_set_notification_read',route=>{
    const body=route.request().postDataJSON()
    calls.push({path:'/rest/v1/rpc/retail_platform_set_notification_read',body})
    read=body.p_read
    return fulfill(route,{id:101,read})
  })
  await page.goto('/platform-alerts')
  await expect(page.getByRole('heading',{name:'Notifications & alerts'})).toBeVisible()
  await expect(page.getByText('2 unread / 2 active alerts')).toBeVisible()
  await expect(page.getByText('Campaign planning failed')).toBeVisible()
  await expect(page.getByText(/Azure infrastructure uptime and real queue depths are not connected/)).toBeVisible()
  await page.getByRole('button',{name:/Mark read — Campaign planning failed/}).click()
  await expect(page.getByText('1 unread / 2 active alerts')).toBeVisible()
  await page.getByRole('button',{name:/Mark unread — Campaign planning failed/}).click()
  await expect(page.getByText('2 unread / 2 active alerts')).toBeVisible()
  await page.getByRole('button',{name:'Queue health'}).click()
  await expect(page.getByText('No matching verified notifications.')).toBeVisible()
  expect(calls.filter(c=>c.path==='/rest/v1/rpc/retail_platform_set_notification_read')
    .map(c=>c.body.p_read)).toEqual([true,false])
})
test('super admin alert filter revisits reuse short-lived verified reads, manual refresh re-queries',async({page})=>{
  const calls=await loginAs(page,'ROOT')
  const notified=[]
  await page.route(SUPABASE+'/rest/v1/rpc/retail_platform_notifications',route=>{
    const p=route.request().postDataJSON()
    notified.push(p)
    return fulfill(route,{
      total_active:2,unread_active:2,database_checked_at:'2026-10-24T08:00:00Z',
      azure_telemetry:'NOT_CONNECTED',
      items:p.p_category==='queue'?[]:[{
        id:101,event_key:'job:campaign:cached',category:'job',severity:'critical',
        title:'Cached job warning',detail:'Server-recorded job status',
        first_seen_at:'2026-10-24T07:00:00Z',active:true,read_at:null,
      }],
    })
  })
  await page.goto('/platform-alerts')
  await expect(page.getByText('Cached job warning')).toBeVisible()
  const activeReads=notified.filter(p=>p.p_category==='all').length
  expect(activeReads).toBeGreaterThan(0)
  await page.getByRole('button',{name:'Queue health'}).click()
  await expect(page.getByText('No matching verified notifications.')).toBeVisible()
  await page.getByRole('button',{name:'All',exact:true}).click()
  await expect(page.getByText('Cached job warning')).toBeVisible()
  expect(notified.filter(p=>p.p_category==='all')).toHaveLength(activeReads)
  await page.getByRole('button',{name:'Refresh alerts'}).click()
  await expect.poll(()=>notified.filter(p=>p.p_category==='all').length).toBe(activeReads+1)
  expect(calls.filter(c=>c.path==='/rest/v1/rpc/retail_platform_set_notification_read')).toHaveLength(0)
})

test('subscription watch totals apply to all retailers and search is server-side',async({page})=>{
  const calls=await loginAs(page,'ROOT')
  await page.goto('/platform-admin')
  const health=page.getByRole('region',{name:'Subscription health across all retailers'})
  await expect(health.getByText('Across all 56 retailers',{exact:false})).toBeVisible()
  await expect(health.getByText('Due in 7 days')).toBeVisible()
  await health.getByLabel('Filter status').selectOption('expiring')
  await expect.poll(()=>calls.filter(c=>c.path==='/rest/v1/rpc/retail_platform_subscription_watch')
    .some(c=>c.body.p_status==='expiring')).toBeTruthy()
  await health.getByLabel('Search all retailers').fill('boutique')
  await health.getByRole('button',{name:'Search'}).click()
  await expect.poll(()=>calls.filter(c=>c.path==='/rest/v1/rpc/retail_platform_subscription_watch')
    .some(c=>c.body.p_search==='boutique')).toBeTruthy()
})
test('non-root cannot open persistent inbox or reach privileged API',async ({ page })=>{
  const calls=await loginAs(page,'OWNER')
  await page.goto('/platform-alerts')
  await expect(page.getByRole('heading',{name:'Platform access denied'})).toBeVisible()
  await expect(page.getByRole('navigation',{name:'Main navigation'})
    .getByRole('link',{name:'Notifications'})).toHaveCount(0)
  for(const forbidden of ['retail_platform_notifications','retail_platform_subscription_watch',
    'retail_platform_set_notification_read']){
    expect(calls.filter(c=>c.path.endsWith('/rpc/'+forbidden))).toHaveLength(0)
  }
})
