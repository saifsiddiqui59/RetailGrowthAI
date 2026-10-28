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
      '/rest/v1/business_profiles': [],
      '/rest/v1/rpc/retail_retailer_inbox': {
        shop_id:SHOP,matching_total:0,unread_total:0,items:[],
        checked_at:'2026-10-28T11:00:00Z'
      },
      '/rest/v1/media_assets': [
        {id: 'a1000000-0000-4000-8000-000000000010', shop_id: SHOP, source:'UPLOAD', license_name: 'owned', mime_type:'image/png',created_at:'2026-10-28T12:00:00Z'}
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
  await expect(page.getByRole('region', { name: 'Authorized media records' }).getByText('Image a1000000',{exact:true})).toBeVisible()
  await expect(page.getByText('image/jpeg')).toHaveCount(0)
  expect(calls.some(path => path.includes('/retail_platform_notifications'))).toBe(false)
  expect(calls.some(path => path.includes('/social_accounts'))).toBe(false)
})

test('calendar panels stay full width after Campaign Studio CSS loads, on desktop and mobile', async ({ page }) => {
  await page.setViewportSize({ width: 1440, height: 900 })
  await signedIn(page)
  // React.lazy CSS remains loaded when the user navigates from Campaign Studio.
  // Its .rg-calendar seven-column picker must NOT style this page container.
  await page.goto('/campaigns')
  await expect(page.locator('.rg-calendar[aria-label="Choose a campaign day"]')).toBeVisible()
  await page.getByRole('navigation', { name: 'Main navigation' })
    .getByRole('link', { name: 'Campaign calendar' }).click()
  await expect(page).toHaveURL(/calendar$/)
  const root = page.locator('.rg-campaign-calendar-page')
  await expect(root.getByRole('heading', { name: 'Campaign calendar' })).toBeVisible()
  await expect(root.getByRole('region', { name: 'All campaigns planning calendar' })).toBeVisible()
  const measures = await root.evaluate(element => {
    const heading = element.querySelector('.page-heading').getBoundingClientRect()
    const recent = element.querySelector('.panel').getBoundingClientRect()
    const month = element.querySelector('.rg-shop-month').getBoundingClientRect()
    return {display: getComputedStyle(element).display,
      width: element.getBoundingClientRect().width,
      headingBottom: heading.bottom, recentTop: recent.top, recentBottom: recent.bottom,
      recentWidth: recent.width, monthTop: month.top, monthWidth: month.width}
  })
  expect(measures.display).toBe('block')
  expect(measures.width).toBeGreaterThan(680)
  expect(measures.recentWidth).toBeGreaterThan(680)
  expect(measures.monthWidth).toBeGreaterThan(680)
  expect(measures.recentTop).toBeGreaterThanOrEqual(measures.headingBottom - 2)
  expect(measures.monthTop).toBeGreaterThanOrEqual(measures.recentBottom - 2)
  await page.getByRole('button', { name: 'Switch to dark mode' }).click()
  await expect(page.locator('html')).toHaveAttribute('data-rg-theme', 'dark')
  await page.setViewportSize({ width: 390, height: 844 })
  await expect.poll(() => page.evaluate(() =>
    document.documentElement.scrollWidth <= document.documentElement.clientWidth)).toBe(true)
  const mobile = await root.evaluate(element => {
    const recent = element.querySelector('.panel').getBoundingClientRect()
    const month = element.querySelector('.rg-shop-month').getBoundingClientRect()
    return { recentWidth: recent.width, monthWidth: month.width,
      recentBottom: recent.bottom, monthTop: month.top }
  })
  expect(mobile.recentWidth).toBeLessThanOrEqual(390)
  expect(mobile.monthWidth).toBeLessThanOrEqual(390)
  expect(mobile.monthTop).toBeGreaterThanOrEqual(mobile.recentBottom - 2)
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

test('mobile Overview uses existing UI primitives and only refreshes metrics on demand', async ({ page }) => {
  await page.setViewportSize({ width: 320, height: 740 })
  const calls = await signedIn(page)
  await page.goto('/')
  await expect(page.getByRole('heading', { name: 'Campaign workspace' })).toBeVisible()
  const metrics = page.getByRole('region', { name: 'Live business metrics' })
  await expect(metrics.locator('[data-slot="card"]')).toHaveCount(4)
  await expect(page.getByRole('link', { name: 'Open campaign studio' })).toBeVisible()
  await expect(page.getByRole('button', { name: 'Refresh business metrics' })).toBeEnabled()
  await expect.poll(() => page.evaluate(() =>
    document.documentElement.scrollWidth <= document.documentElement.clientWidth)).toBe(true)
  const firstReads = calls.filter(path=>path==='/rest/v1/campaigns' || path==='/rest/v1/render_jobs').length
  await page.getByRole('button',{name:'Refresh business metrics'}).click()
  await expect(page.getByRole('button', { name:'Refresh business metrics' })).toBeEnabled()
  await expect.poll(() => calls.filter(path=>path==='/rest/v1/campaigns' ||
    path==='/rest/v1/render_jobs').length).toBeGreaterThan(firstReads)
})

test('retailer media, calendar and settings share responsive cards and preserve private routes', async ({ page }) => {
  await page.setViewportSize({ width: 320, height: 740 })
  const calls = await signedIn(page)
  await page.goto('/media-library')
  await expect(page.getByRole('heading', {name:'Media library'})).toBeVisible()
  await expect(page.getByRole('link', {name:'Upload an image'})).toBeVisible()
  await expect(page.getByRole('button', {name:'Refresh assets'})).toBeEnabled()
  await expect(page.getByRole('region', {name:'Authorized media records'}).locator('[data-slot="card"]')).toHaveCount(1)
  for (const route of ['/media-library','/calendar','/settings']) {
    await page.goto(route)
    await expect.poll(() => page.evaluate(() =>
      document.documentElement.scrollWidth <= document.documentElement.clientWidth)).toBe(true)
  }
  await expect(page.getByRole('link',{name:'Account & security'})).toBeVisible()
  await page.setViewportSize({width:768,height:900})
  await page.goto('/calendar')
  await expect(page.getByRole('button',{name:'Load recent campaign'})).toBeVisible()
  await expect(page.getByRole('link',{name:'Open campaign studio'})).toBeVisible()
  expect(calls.some(path=>path.includes('/retail_platform_notifications'))).toBe(false)
  expect(calls.some(path=>path.includes('/social_accounts'))).toBe(false)
})

test('shop-wide month reads two campaigns only after click with user JWT and one scoped GET',async({page})=>{
  const calls=await signedIn(page)
  let calendarCalls=0
  await page.route(HOST+'/rest/v1/campaign_days**',route=>{
    calendarCalls++
    const u=new URL(route.request().url())
    expect(u.searchParams.get('shop_id')).toBe('eq.'+SHOP)
    expect(route.request().headers().authorization).toBe('Bearer offline-test-JWT')
    return route.fulfill({status:200,contentType:'application/json',
      headers:{'Access-Control-Allow-Origin':'*'},
      body:JSON.stringify([
        {id:'d1000000-0000-4000-8000-000000000001',shop_id:SHOP,
          campaign_id:'c1000000-0000-4000-8000-000000000001',
          scheduled_date:'2026-10-20',topic:'Autumn collection',review_status:'DRAFT'},
        {id:'d1000000-0000-4000-8000-000000000002',shop_id:SHOP,
          campaign_id:'c1000000-0000-4000-8000-000000000002',
          scheduled_date:'2026-10-21',topic:'Product care',review_status:'APPROVED'}
      ])})
  })
  await page.setViewportSize({width:320,height:740})
  await page.goto('/calendar')
  await expect(page.getByRole('region',{name:'All campaigns planning calendar'})).toBeVisible()
  expect(calendarCalls).toBe(0)
  await page.getByLabel('Business calendar month').fill('2026-10')
  await page.getByRole('button',{name:'Load business month'}).click()
  await expect(page.getByText('2 verified planned days in 2026-10. No delivery confirmation.')).toBeVisible()
  await expect(page.getByText('Autumn collection')).toBeVisible()
  await expect(page.getByText('Product care')).toBeVisible()
  await expect(page.getByText('APPROVED · not published')).toBeVisible()
  expect(calendarCalls).toBe(1)
  await expect.poll(()=>page.evaluate(()=>document.documentElement.scrollWidth<=
    document.documentElement.clientWidth)).toBe(true)
  expect(calls.some(url=>url.includes('retail_platform_notifications'))).toBe(false)
})

test('new month loads while previous JWT read is pending and stale response cannot overwrite', async ({page}) => {
  await signedIn(page)
  let releaseOld
  let oldStarted
  const oldGate = new Promise(resolve => { releaseOld = resolve })
  const oldSeen = new Promise(resolve => { oldStarted = resolve })
  const requested = []
  await page.route(HOST + '/rest/v1/campaign_days**', async route => {
    const request = route.request()
    const url = new URL(request.url())
    expect(url.searchParams.get('shop_id')).toBe('eq.' + SHOP)
    expect(request.headers().authorization).toBe('Bearer offline-test-JWT')
    const month = url.searchParams.get('and')
    requested.push(month)
    const october = month?.includes('2026-10-01')
    if (october) {
      oldStarted()
      await oldGate
    }
    const row = {
      id: october ? 'd1000000-0000-4000-8000-000000000001' : 'd1000000-0000-4000-8000-000000000002',
      campaign_id: 'c1000000-0000-4000-8000-000000000001',
      shop_id: SHOP,
      scheduled_date: october ? '2026-10-15' : '2026-11-15',
      topic: october ? 'Old October draft' : 'Fresh November draft',
      review_status: 'DRAFT',
    }
    await route.fulfill({status:200,contentType:'application/json',
      headers:{'Access-Control-Allow-Origin':'*'},body:JSON.stringify([row])})
  })
  try {
    await page.goto('/calendar')
    await page.getByLabel('Business calendar month').fill('2026-10')
    await page.getByRole('button',{name:'Load business month'}).click()
    await oldSeen
    await page.getByLabel('Business calendar month').fill('2026-11')
    await page.getByRole('button',{name:'Load business month'}).click()
    await expect(page.getByText('Fresh November draft')).toBeVisible()
    await expect(page.getByText('1 verified planned day in 2026-11. No delivery confirmation.')).toBeVisible()
    releaseOld()
    await expect(page.getByText('Old October draft')).toHaveCount(0)
    expect(requested.filter(m => m?.startsWith('(scheduled_date.gte.2026-10-01,'))).toHaveLength(1)
    expect(requested.filter(m => m?.startsWith('(scheduled_date.gte.2026-11-01,'))).toHaveLength(1)
  } finally {
    releaseOld()
  }
})

test('private registered media is read only on preview through user JWT, never public Storage links',async({page})=>{
  await signedIn(page)
  const image='a1000000-0000-4000-8000-000000000010'
  const upload='a1000000-0000-4000-8000-000000000020'
  let privateReads=0
  await page.route(HOST+'/rest/v1/media_assets**',route=>{
    const u=new URL(route.request().url())
    const registered={id:image,shop_id:SHOP,storage_bucket:'retailgrowth-media',
      object_path:SHOP+'/uploads/'+upload+'.png',mime_type:'image/png',
      source:'UPLOAD',license_name:'owned',created_at:'2026-10-28T12:00:00Z'}
    return route.fulfill({status:200,contentType:'application/json',
      headers:{'Access-Control-Allow-Origin':'*','Access-Control-Allow-Headers':'*'},
      body:JSON.stringify(u.searchParams.has('id')?[registered]:[registered])})
  })
  await page.route(HOST+'/storage/v1/object/authenticated/**',route=>{
    privateReads++
    expect(route.request().headers().authorization).toBe('Bearer offline-test-JWT')
    const png=Buffer.alloc(256)
    Buffer.from([137,80,78,71,13,10,26,10]).copy(png)
    return route.fulfill({status:200,body:png,
      headers:{'Access-Control-Allow-Origin':'*','Content-Type':'image/png','Content-Length':'256'}})
  })
  await page.goto('/media-library')
  expect(privateReads).toBe(0)
  await page.getByRole('button',{name:'Preview Image a1000000'}).click()
  await expect(page.getByRole('img',{name:'Authorized private image Image a1000000'}))
    .toHaveAttribute('src',/^blob:/)
  await expect(page.getByRole('link',{name:'Save private image'}))
    .toHaveAttribute('href',/^blob:/)
  expect(privateReads).toBe(1)
  await expect(page.locator('a[href*="/storage/v1/object/"]')).toHaveCount(0)
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

test('Media Library rejects mixed-tenant media responses rather than silently filtering',async({page})=>{
  await signedIn(page)
  let privateReads=0
  await page.route(HOST+'/rest/v1/media_assets**',route=>{
    expect(route.request().headers().authorization).toBe('Bearer offline-test-JWT')
    const own={id:'a1000000-0000-4000-8000-000000000010',shop_id:SHOP,
      source:'UPLOAD',license_name:'owned',mime_type:'image/png',
      created_at:'2026-10-28T12:00:00Z'}
    return route.fulfill({status:200,contentType:'application/json',
      headers:{'Access-Control-Allow-Origin':'*','Access-Control-Allow-Headers':'*'},
      body:JSON.stringify([own,{...own,id:'a1000000-0000-4000-8000-000000000011',
        shop_id:'a1000000-0000-4000-8000-000000000002',
        created_at:'2026-10-28T11:59:00Z'}])})
  })
  await page.route(HOST+'/storage/v1/object/authenticated/**',route=>{
    privateReads++;return route.abort()
  })
  await page.setViewportSize({width:320,height:740})
  await page.goto('/media-library')
  await expect(page.getByRole('alert').filter({hasText:'Private media metadata could not be verified'})).toBeVisible()
  await expect(page.getByRole('region',{name:'Authorized media records'})).toHaveCount(0)
  await expect(page.getByRole('button',{name:/Preview Image/})).toHaveCount(0)
  expect(privateReads).toBe(0)
  await expect.poll(()=>page.evaluate(()=>
    document.documentElement.scrollWidth<=document.documentElement.clientWidth)).toBe(true)
})

test('Media Library pages 27 RLS-verified records locally and resets on filters without more calls', async ({page})=>{
  await signedIn(page)
  let mediaReads=0
  const rows=Array.from({length:27},(_,i)=>({
    id:'a1000000-0000-4000-8000-'+String(i+100).padStart(12,'0'),
    shop_id:SHOP,source:'UPLOAD',license_name:i===26?'owned-special':'owned',mime_type:i===26?'image/webp':'image/png',
    created_at:new Date(Date.UTC(2026,9,28,12,0)-i*1000).toISOString()
  }))
  await page.route(HOST+'/rest/v1/media_assets**',route=>{
    mediaReads+=1
    return route.fulfill({
    status:200,contentType:'application/json',
    headers:{'Access-Control-Allow-Origin':'*','Access-Control-Allow-Headers':'*'},
    body:JSON.stringify(rows)
  })
  })
  await page.setViewportSize({width:320,height:740})
  await page.goto('/media-library')
  const list=page.getByRole('region',{name:'Authorized media records'})
  await expect(list.locator('[data-slot="card"]')).toHaveCount(12)
  await expect(page.getByRole('status',{name:''}).filter({hasText:'Page 1 of 3'})).toBeVisible()
  await page.getByRole('button',{name:'Next images'}).click()
  await expect(list.locator('[data-slot="card"]')).toHaveCount(12)
  await expect(page.getByText('Page 2 of 3')).toBeVisible()
  await page.getByRole('button',{name:'Next images'}).click()
  await expect(list.locator('[data-slot="card"]')).toHaveCount(3)
  await expect(page.getByText('Page 3 of 3')).toBeVisible()
  await page.getByLabel('Search media').fill('owned-special')
  await expect(page.getByText('1 matching registered images')).toBeVisible()
  await expect(list.locator('[data-slot="card"]')).toHaveCount(1)
  await expect(page.getByRole('button',{name:'Next images'})).toHaveCount(0)
  await page.getByLabel('Search media').fill('')
  await expect(page.getByText('Page 1 of 3')).toBeVisible()
  await expect(list.locator('[data-slot="card"]')).toHaveCount(12)
  await expect.poll(()=>page.evaluate(()=>document.documentElement.scrollWidth<=document.documentElement.clientWidth)).toBe(true)
  expect(mediaReads).toBe(1)
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
  await expect(page.getByText('Day 1 · Not published',{exact:true})).toBeVisible()
  expect(apiCalls.filter(x=>x.method==='GET')).toHaveLength(1)
  expect(apiCalls.some(x=>x.method==='GET' && x.auth==='Bearer offline-test-JWT')).toBe(true)
  foreign = true
  await page.getByRole('button', { name: 'Load recent campaign' }).click()
  await expect(page.getByRole('alert')).toContainText('No dates or posts are assumed')
  await expect(page.getByText('Approved draft example')).toHaveCount(0)
})

test('recent draft month view navigates verified November/December without extra network requests',async({page})=>{
  await signedIn(page)
  const CAMPAIGN='c1000000-0000-4000-8000-000000000001'
  let reads=0
  const makeDay=(n,date,topic)=>({id:'d1000000-0000-4000-8000-'+String(n).padStart(12,'0'),
    campaign_id:CAMPAIGN,shop_id:SHOP,day_index:n,scheduled_date:date,
    topic,review_status:'DRAFT'})
  await page.route('https://api.e2e.retailgrowth.test/**',route=>{
    const headers={'Access-Control-Allow-Origin':'*','Access-Control-Allow-Headers':'authorization,content-type'}
    if(route.request().method()==='OPTIONS')return route.fulfill({status:204,headers,body:''})
    reads+=1
    return route.fulfill({status:200,contentType:'application/json',headers,
      body:JSON.stringify({id:CAMPAIGN,shop_id:SHOP,status:'DRAFT',days:[
        makeDay(1,'2026-11-30','Winter sale brief'),
        makeDay(2,'2026-12-01','December gift edits')]})})
  })
  await page.addInitScript(({user,shop,campaign})=>sessionStorage.setItem(
    'retailgrowthai-last-campaign:'+user+':'+shop,campaign
  ),{user:USER,shop:SHOP,campaign:CAMPAIGN})
  await page.setViewportSize({width:320,height:740})
  await page.goto('/calendar')
  await page.getByRole('button',{name:'Load recent campaign'}).click()
  await expect(page.getByRole('table',{name:'Verified draft month grid'})).toBeVisible()
  await expect(page.getByRole('combobox',{name:'Draft month',exact:true})).toHaveValue('2026-11')
  await expect(page.getByText('Winter sale brief')).toBeVisible()
  await expect(page.getByText('December gift edits')).toHaveCount(0)
  await page.getByRole('combobox',{name:'Draft month',exact:true}).selectOption('2026-12')
  await expect(page.getByText('December gift edits')).toBeVisible()
  await expect(page.getByText('Winter sale brief')).toHaveCount(0)
  await expect(page.getByRole('table',{name:'Verified draft month grid'})
    .locator('td[aria-label="2026-12-01: 1 unpublished drafts"]')).toBeVisible()
  expect(reads).toBe(1)
  await expect.poll(()=>page.evaluate(()=>document.documentElement.scrollWidth<=
    document.documentElement.clientWidth)).toBe(true)
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
  await page.goto('/creative-studio')
  await expect(page.getByLabel('Creative Studio business')).toHaveValue(SECOND)
  await page.goto('/calendar')
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

test('Creative Studio shows only real shop-scoped marketing context and links to existing tools', async ({page})=>{
  await signedIn(page)
  const requests=[]
  await page.route(HOST + '/rest/v1/business_profiles**',route=>{
    requests.push({method:route.request().method(),url:route.request().url()})
    return route.fulfill({status:200,contentType:'application/json',
      headers:{'Access-Control-Allow-Origin':'*','Access-Control-Allow-Headers':'*'},
      body:JSON.stringify([{shop_id:SHOP,business_name:'Example Boutique',category:'Clothing',
        city:'Nagpur',description:'Local ethnic clothing for families',brand_voice:''}])})
  })
  await page.goto('/creative-studio')
  await expect(page.getByRole('heading',{name:'Creative Studio'})).toBeVisible()
  await expect(page.getByText('4 of 5')).toBeVisible()
  await expect(page.getByRole('list',{name:'Business content checklist'}).getByText('Brand voice')).toBeVisible()
  for (const label of ['Open Trend Intelligence','View Media Library',
    'Open Campaign Studio','Open Draft Calendar','Edit profile']) {
    await expect(page.getByRole('link',{name:label})).toBeVisible()
  }
  expect(requests).toHaveLength(1)
  expect(requests[0].method).toBe('GET')
  expect(new URL(requests[0].url).searchParams.get('shop_id')).toBe('eq.'+SHOP)
  await expect(page.getByText('No fabricated live data')).toBeVisible()
})

test('Creative Studio rejects foreign profile response without showing its content', async ({page})=>{
  await signedIn(page)
  await page.route(HOST + '/rest/v1/business_profiles**',route=>route.fulfill({
    status:200,contentType:'application/json',
    headers:{'Access-Control-Allow-Origin':'*','Access-Control-Allow-Headers':'*'},
    body:JSON.stringify([{shop_id:'a1000000-0000-4000-8000-000000000002',
      business_name:'Foreign competitor',category:'Retail',city:'Other city'}])
  }))
  await page.goto('/creative-studio')
  await expect(page.getByRole('alert')).toContainText('could not be verified')
  await expect(page.getByText('Foreign competitor')).toHaveCount(0)
  await expect(page.getByText('of 5')).toHaveCount(0)
})

test('external integration pages show explicit requirements, not fictional account or delivery state', async ({page})=>{
  const calls=await signedIn(page)
  await page.setViewportSize({width:320,height:740})
  const pages=[
    ['/connections','Connected accounts'],
    ['/publishing','Publishing calendar & history'],
    ['/notifications','Notifications'],
  ]
  for(const [route,heading] of pages) {
    await page.goto(route)
    await expect(page.getByRole('heading',{name:heading,exact:true})).toBeVisible()
    const requirements=page.getByRole('region',{name:heading+' integration requirements'})
    await expect(requirements.getByRole('listitem')).toHaveCount(3)
    await expect(page.getByText('No fabricated live data')).toBeVisible()
    await expect(requirements.getByText('No connection, message, post, payment or scheduled delivery is created by viewing this guide.')).toBeVisible()
    await expect.poll(()=>page.evaluate(()=>document.documentElement.scrollWidth <=
      document.documentElement.clientWidth)).toBe(true)
  }
  expect(calls.some(path=>path.includes('/social_accounts') ||
    path.includes('/retail_platform_notifications') || path.includes('/publishing'))).toBe(false)
})

test('unverified guest cannot deep-link to dashboard subroutes', async ({ page }) => {
  await page.goto('/connections')
  await expect(page).toHaveURL(/\/account$/)
  await expect(page.getByRole('heading', { name: 'Connected accounts' })).toHaveCount(0)
})


test('Media Library keyset loads 101 records without repeating a row after new uploads',async({page})=>{
  await signedIn(page)
  const rows=Array.from({length:101},(_,i)=>({
    id:'a1000000-0000-4000-8000-'+String(i+100).padStart(12,'0'),
    shop_id:SHOP,source:'UPLOAD',license_name:'owned',mime_type:'image/png',
    created_at:new Date(Date.UTC(2026,9,28,12,0)-i*1000).toISOString()
  }))
  const cursors=[]
  await page.route(HOST+'/rest/v1/media_assets**',route=>{
    const req=route.request(),u=new URL(req.url())
    expect(req.headers().authorization).toBe('Bearer offline-test-JWT')
    expect(u.searchParams.get('shop_id')).toBe('eq.'+SHOP)
    expect(u.searchParams.get('order')).toBe('created_at.desc,id.desc')
    expect(u.searchParams.get('limit')).toBe('101')
    expect(u.searchParams.has('offset')).toBe(false)
    cursors.push(u.searchParams.get('or'))
    // A freshly added row before the original first row must never shift the
    // second page: backend keyset returns the 101st original record only.
    const body=cursors.length===1 ? rows : [rows[100]]
    if(cursors.length===2){
      expect(cursors[1]).toContain('created_at.lt.'+rows[99].created_at)
      expect(cursors[1]).toContain('id.lt.'+rows[99].id)
    }
    return route.fulfill({status:200,contentType:'application/json',
      headers:{'Access-Control-Allow-Origin':'*','Access-Control-Allow-Headers':'*'},
      body:JSON.stringify(body)})
  })
  await page.setViewportSize({width:320,height:740})
  await page.goto('/media-library')
  await expect(page.getByText('100 matching registered images')).toBeVisible()
  expect(cursors).toEqual([null])
  await page.getByRole('button',{name:'Load 100 older records'}).click()
  await expect(page.getByText('101 matching registered images')).toBeVisible()
  expect(cursors).toHaveLength(2)
  await expect(page.getByRole('button',{name:'Load 100 older records'})).toHaveCount(0)
  await expect(page.locator('a[href*="/storage/v1/object/"]')).toHaveCount(0)
  await expect.poll(()=>page.evaluate(()=>
    document.documentElement.scrollWidth<=document.documentElement.clientWidth)).toBe(true)
})

test('retailer inbox uses signed JWT, scoped paging, genuine server states and per-user read update',async({page})=>{
  await signedIn(page)
  const requests=[]
  let read=false
  const messages=Array.from({length:21},(_,i)=>({
    id:i+1,shop_id:SHOP,category:'video',severity:'info',
    title:'Verified render '+(i+1),detail:'A persisted job event.',
    created_at:'2026-10-28T11:00:00Z',read_at:i===0&&read?'2026-10-28T11:01:00Z':null
  }))
  await page.route(HOST+'/rest/v1/rpc/retail_retailer_inbox',route=>{
    const req=route.request(),body=req.postDataJSON()
    expect(req.headers().authorization).toBe('Bearer offline-test-JWT')
    expect(body.p_shop_id).toBe(SHOP)
    expect(body.p_limit).toBe(20)
    requests.push({path:'list',offset:body.p_offset})
    return route.fulfill({status:200,contentType:'application/json',
      headers:{'Access-Control-Allow-Origin':'*','Access-Control-Allow-Headers':'*'},
      body:JSON.stringify({shop_id:SHOP,matching_total:21,
        unread_total:read?20:21,checked_at:'2026-10-28T11:01:00Z',
        items:messages.slice(body.p_offset,body.p_offset+body.p_limit).map((m,i)=>
          m.id===1?{...m,read_at:read?'2026-10-28T11:01:00Z':null}:m)})})
  })
  await page.route(HOST+'/rest/v1/rpc/retail_retailer_set_inbox_read',route=>{
    const req=route.request(),body=req.postDataJSON()
    expect(req.headers().authorization).toBe('Bearer offline-test-JWT')
    expect(body).toEqual({p_shop_id:SHOP,p_event_id:1,p_read:true})
    read=true
    requests.push({path:'mark'})
    return route.fulfill({status:200,contentType:'application/json',
      headers:{'Access-Control-Allow-Origin':'*','Access-Control-Allow-Headers':'*'},
      body:JSON.stringify({shop_id:SHOP,id:1,read:true})})
  })
  await page.setViewportSize({width:320,height:740})
  await page.goto('/notifications')
  await expect(page.getByRole('heading',{name:'Notifications',exact:true})).toBeVisible()
  await expect(page.getByText('21 unread')).toBeVisible()
  expect(requests.filter(r=>r.path==='list')).toHaveLength(1)
  expect(requests[0].offset).toBe(0)
  await page.getByRole('button',{name:'Mark read'}).first().click()
  await expect(page.getByText('20 unread')).toBeVisible()
  expect(requests.some(r=>r.path==='mark')).toBe(true)
  await page.getByRole('button',{name:'Next'}).click()
  await expect(page.getByText('Verified render 21')).toBeVisible()
  expect(requests.some(r=>r.path==='list'&&r.offset===20)).toBe(true)
  await expect(page.locator('a[href*="/storage/v1/object"]')).toHaveCount(0)
  await expect.poll(()=>page.evaluate(()=>
    document.documentElement.scrollWidth<=document.documentElement.clientWidth)).toBe(true)
})


test('opt-in offline Feature1 social and publishing showroom is labelled, responsive and never calls provider APIs',async({page})=>{
  const calls=await signedIn(page)
  await page.setViewportSize({width:320,height:740})
  await page.goto('/connections')
  await expect(page.getByRole('heading',{name:'Connected accounts',exact:true})).toBeVisible()
  await expect(page.getByText('@aarohi.style')).toHaveCount(0)
  await expect(page.getByText('No fabricated live data')).toBeVisible()
  await page.getByRole('button',{name:'Open offline test preview'}).click()
  await expect(page.getByText('OFFLINE TEST ONLY — NOT LIVE DATA')).toBeVisible()
  await expect(page.getByText('@aarohi.style')).toBeVisible()
  await expect(page.getByText('Aarohi Fashion Page')).toBeVisible()
  await expect(page.getByText('Aarohi Fashion Shorts')).toBeVisible()
  await expect(page.getByRole('button',{name:'Connect / disconnect unavailable'}).first()).toBeDisabled()
  await page.getByLabel('Social account status filter').selectOption('REVOKED')
  await expect(page.getByText('Aarohi Retail')).toBeVisible()
  await expect(page.getByText('@aarohi.style')).toHaveCount(0)
  await page.getByLabel('Fictional business scenario').selectOption('f2222222-2222-4222-8222-222222222222')
  await expect(page.getByText('Green Basket Grocery Page')).toBeVisible()
  await expect(page.getByText('Aarohi Retail')).toHaveCount(0)
  await page.goto('/publishing')
  await expect(page.getByText('OFFLINE TEST ONLY — NOT LIVE DATA')).toHaveCount(0)
  await page.getByRole('button',{name:'Open offline test preview'}).click()
  await expect(page.getByText('OFFLINE TEST ONLY — NOT LIVE DATA')).toBeVisible()
  await expect(page.getByText('26 example events matching')).toBeVisible()
  await expect(page.getByRole('button',{name:'Next sample page'})).toBeEnabled()
  await page.getByRole('button',{name:'Next sample page'}).click()
  await expect(page.getByText('Page 2 of 4')).toBeVisible()
  await page.getByLabel('Publishing status filter').selectOption('PUBLISHED')
  await expect(page.getByText('Example provider receipt:',{exact:false}).first()).toBeVisible()
  await expect(page.getByText('Page 1 of 1')).toBeVisible()
  await expect(page.getByRole('button',{name:'Next sample page'})).toBeDisabled()
  await page.getByLabel('Fictional business scenario').selectOption('f2222222-2222-4222-8222-222222222222')
  await expect(page.getByText('Green Basket fictional channel').first()).toBeVisible()
  await expect(page.getByText('Aarohi fictional channel')).toHaveCount(0)
  await expect.poll(()=>page.evaluate(()=>
    document.documentElement.scrollWidth<=document.documentElement.clientWidth)).toBe(true)
  expect(calls.some(path=>path.includes('/social')||path.includes('/oauth')||
    path.includes('/publishing')||path.includes('/retail_platform_notifications'))).toBe(false)
})


test('third fictional restaurant exercises disconnected identity and publishing-in-progress without live calls',async({page})=>{
 const calls=await signedIn(page)
 await page.setViewportSize({width:320,height:740})
 await page.goto('/connections')
 await page.getByRole('button',{name:'Open offline test preview'}).click()
 await page.getByLabel('Fictional business scenario')
   .selectOption('f3333333-3333-4333-8333-333333333333')
 await expect(page.getByText('OFFLINE TEST ONLY — NOT LIVE DATA')).toBeVisible()
 await page.getByLabel('Social account status filter').selectOption('DISCONNECTED')
 await expect(page.getByText('Marigold Bistro disconnected sample')).toBeVisible()
 await expect(page.getByText('@aarohi.style')).toHaveCount(0)
 await expect(page.getByRole('button',{name:'Connect / disconnect unavailable'})).toBeDisabled()
 await page.goto('/publishing')
 await page.getByRole('button',{name:'Open offline test preview'}).click()
 await page.getByLabel('Fictional business scenario')
   .selectOption('f3333333-3333-4333-8333-333333333333')
 await page.getByLabel('Publishing status filter').selectOption('PUBLISHING')
 await expect(page.locator('.rg-f1-read-card').getByText('PUBLISHING',{exact:true}).first()).toBeVisible()
 await expect(page.getByText('Example provider receipt:',{exact:false})).toHaveCount(0)
 await expect.poll(()=>page.evaluate(()=>
   document.documentElement.scrollWidth<=document.documentElement.clientWidth)).toBe(true)
 expect(calls.some(path=>path.includes('/social')||path.includes('/oauth')||
   path.includes('/publishing'))).toBe(false)
})


test('private image close revokes blob and a late Storage response cannot reopen the preview',async({page})=>{
  await signedIn(page)
  const image='a1000000-0000-4000-8000-000000000010'
  const upload='a1000000-0000-4000-8000-000000000020'
  await page.route(HOST+'/rest/v1/media_assets**',route=>{
    const row={id:image,shop_id:SHOP,storage_bucket:'retailgrowth-media',
      object_path:SHOP+'/uploads/'+upload+'.png',mime_type:'image/png',
      source:'UPLOAD',license_name:'owned',created_at:'2026-10-28T12:00:00Z'}
    return route.fulfill({status:200,contentType:'application/json',
      headers:{'Access-Control-Allow-Origin':'*','Access-Control-Allow-Headers':'*'},
      body:JSON.stringify([row])})
  })
  const png=Buffer.alloc(256)
  Buffer.from([137,80,78,71,13,10,26,10]).copy(png)
  let hold=false,releaseRead,readStarted
  const started=new Promise(resolve=>{readStarted=resolve})
  const gate=new Promise(resolve=>{releaseRead=resolve})
  let privateReads=0
  await page.route(HOST+'/storage/v1/object/authenticated/**',async route=>{
    privateReads++
    expect(route.request().headers().authorization).toBe('Bearer offline-test-JWT')
    if(hold){readStarted();await gate}
    await route.fulfill({status:200,body:png,
      headers:{'Access-Control-Allow-Origin':'*',
        'Content-Type':'image/png','Content-Length':'256'}})
  })
  await page.setViewportSize({width:320,height:740})
  await page.goto('/media-library')
  expect(privateReads).toBe(0)
  await page.getByRole('button',{name:'Preview Image a1000000'}).click()
  const img=page.getByRole('img',{name:'Authorized private image Image a1000000'})
  await expect(img).toHaveAttribute('src',/^blob:/)
  const oldUrl=await img.getAttribute('src')
  await page.getByRole('button',{name:'Close private preview'}).click()
  await expect(img).toHaveCount(0)
  await expect(page.getByRole('link',{name:'Save private image'})).toHaveCount(0)
  expect(await page.evaluate(async url=>{
    try {return (await fetch(url)).ok} catch{return false}
  },oldUrl)).toBe(false)

  hold=true
  try{
    await page.getByRole('button',{name:'Preview Image a1000000'}).click()
    await started
    await expect(page.getByText('Reading private image with your current session…')).toBeVisible()
    await page.getByRole('button',{name:'Close private preview'}).click()
    const delayedResponse=page.waitForResponse(response=>
      response.url().includes('/storage/v1/object/authenticated/'))
    releaseRead()
    await delayedResponse
    await expect(img).toHaveCount(0)
    await expect(page.getByRole('button',{name:'Close private preview'})).toHaveCount(0)
    await expect(page.locator('a[href^="blob:"]')).toHaveCount(0)
    expect(privateReads).toBe(2)
  }finally{releaseRead()}
})


test('private preview is revoked if refreshed rights change from UPLOAD to GENERATED',async({page})=>{
  await signedIn(page)
  await page.setViewportSize({width:320,height:740})
  const image='a1000000-0000-4000-8000-000000000010'
  const upload='a1000000-0000-4000-8000-000000000020'
  let generated=false,mediaReads=0,privateReads=0
  await page.route(HOST+'/rest/v1/media_assets**',route=>{
    const lookup=new URL(route.request().url()).searchParams.has('id')
    if(!lookup)mediaReads++
    const registered={id:image,shop_id:SHOP,storage_bucket:'retailgrowth-media',
      object_path:SHOP+'/uploads/'+upload+'.png',mime_type:'image/png',
      source:generated&&!lookup?'GENERATED':'UPLOAD',license_name:'owned',
      created_at:'2026-10-28T12:00:00Z'}
    return route.fulfill({status:200,contentType:'application/json',
      headers:{'Access-Control-Allow-Origin':'*','Access-Control-Allow-Headers':'*'},
      body:JSON.stringify([registered])})
  })
  const png=Buffer.alloc(256)
  Buffer.from([137,80,78,71,13,10,26,10]).copy(png)
  await page.route(HOST+'/storage/v1/object/authenticated/**',route=>{
    privateReads++
    expect(route.request().headers().authorization).toBe('Bearer offline-test-JWT')
    return route.fulfill({status:200,body:png,headers:{
      'Access-Control-Allow-Origin':'*','Content-Type':'image/png','Content-Length':'256'}})
  })
  await page.goto('/media-library')
  await expect(page.getByText('1 matching registered images')).toBeVisible()
  await page.getByRole('button',{name:'Preview Image a1000000'}).click()
  const img=page.getByRole('img',{name:'Authorized private image Image a1000000'})
  await expect(img).toHaveAttribute('src',/^blob:/)
  const oldUrl=await img.getAttribute('src')
  expect(privateReads).toBe(1)
  generated=true
  await page.getByRole('button',{name:'Refresh assets'}).click()
  await expect.poll(()=>mediaReads).toBeGreaterThanOrEqual(2)
  await expect(page.getByText('Private preview unavailable until ownership, rights and private access are verified')).toBeVisible()
  await expect(img).toHaveCount(0)
  await expect(page.getByRole('link',{name:'Save private image'})).toHaveCount(0)
  await expect(page.getByRole('button',{name:'Preview Image a1000000'})).toHaveCount(0)
  await expect.poll(async()=>page.evaluate(async url=>{
    try{return (await fetch(url)).ok}catch{return false}
  },oldUrl)).toBe(false)
  expect(privateReads).toBe(1)
  await expect.poll(()=>page.evaluate(()=>
    document.documentElement.scrollWidth<=document.documentElement.clientWidth)).toBe(true)
})


test('private preview revokes its Blob when the current UPLOAD licence changes',async({page})=>{
  await signedIn(page)
  await page.setViewportSize({width:320,height:740})
  const image='a1000000-0000-4000-8000-000000000010'
  const upload='a1000000-0000-4000-8000-000000000020'
  let changed=false,reads=0,metadataReads=0
  await page.route(HOST+'/rest/v1/media_assets**',route=>{
    const request=route.request()
    const lookup=new URL(request.url()).searchParams.has('id')
    if(!lookup) metadataReads++
    const row={id:image,shop_id:SHOP,source:'UPLOAD',
      storage_bucket:'retailgrowth-media',object_path:SHOP+'/uploads/'+upload+'.png',
      mime_type:'image/png',license_name:changed&&!lookup?'royalty_free':'owned',
      created_at:'2026-10-28T12:00:00Z'}
    return route.fulfill({status:200,contentType:'application/json',
      headers:{'Access-Control-Allow-Origin':'*','Access-Control-Allow-Headers':'*'},
      body:JSON.stringify([row])})
  })
  const png=Buffer.alloc(256)
  Buffer.from([137,80,78,71,13,10,26,10]).copy(png)
  await page.route(HOST+'/storage/v1/object/authenticated/**',route=>{
    reads++
    expect(route.request().headers().authorization).toBe('Bearer offline-test-JWT')
    return route.fulfill({status:200,body:png,headers:{
      'Access-Control-Allow-Origin':'*','Content-Type':'image/png','Content-Length':'256'}})
  })
  await page.goto('/media-library')
  await expect(page.getByText('1 matching registered images')).toBeVisible()
  await page.getByRole('button',{name:'Preview Image a1000000'}).click()
  const preview=page.getByRole('img',{name:'Authorized private image Image a1000000'})
  await expect(preview).toHaveAttribute('src',/^blob:/)
  const oldUrl=await preview.getAttribute('src')
  expect(reads).toBe(1)

  // Still a private original UPLOAD with a nonempty licence: the earlier
  // source-only revocation guard would have retained the old Blob.
  changed=true
  await page.getByRole('button',{name:'Refresh assets'}).click()
  await expect.poll(()=>metadataReads).toBeGreaterThanOrEqual(2)
  await expect(page.getByText('Licence: royalty_free')).toBeVisible()
  await expect(preview).toHaveCount(0)
  await expect(page.getByRole('link',{name:'Save private image'})).toHaveCount(0)
  await expect.poll(async()=>page.evaluate(async url=>{
    try{return (await fetch(url)).ok}catch{return false}
  },oldUrl)).toBe(false)
  expect(reads).toBe(1)
  await expect.poll(()=>page.evaluate(()=>
    document.documentElement.scrollWidth<=document.documentElement.clientWidth)).toBe(true)
})
