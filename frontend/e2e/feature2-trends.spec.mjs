import { test, expect } from '@playwright/test'

const SUPABASE = 'https://e2e.supabase.test'
const API = 'https://api.e2e.retailgrowth.test'
const SHOP = 'a1000000-0000-4000-8000-000000000001'
const OTHER = 'a1000000-0000-4000-8000-000000000002'
const USER = 'a9000000-0000-4000-8000-000000000001'
const DRAFT = 'd1000000-0000-4000-8000-000000000001'
const TREND = 'a'.repeat(32)

function respond(route, data, status=200) {
  return route.fulfill({ status, contentType: 'application/json',
    headers: { 'Access-Control-Allow-Origin': '*',
      'Access-Control-Allow-Headers': 'apikey,authorization,content-type' },
    body: JSON.stringify(data) })
}

async function setup(page, { role='OWNER', failTrends=false, foreignDraft=false }={}) {
  const requests=[]
  await page.addInitScript(() => sessionStorage.setItem('retailgrowthai-auth-v1', JSON.stringify({
    access_token: 'signed-offline-mock-only', refresh_token: 'no-network-refresh', expires_at: 2000000000,
  })))
  await page.route(SUPABASE + '/**', route => {
    const req=route.request(), u=new URL(req.url())
    if (req.method()==='OPTIONS') return respond(route,{})
    const responses={
      '/auth/v1/user': { id: USER, email: 'test-owner@example.test' },
      '/rest/v1/rpc/retail_platform_me': false,
      '/rest/v1/rpc/retail_onboarding_status': {status:'APPROVED',approval_required:false},
      '/rest/v1/shop_memberships': [{shop_id: SHOP, active:true, role}],
      '/rest/v1/shops': [{id:SHOP,slug:'example',name:'Example Boutique'}],
      '/rest/v1/media_assets': [{id:OTHER,shop_id:SHOP,license_name:'owned',mime_type:'image/png'}],
    }
    if (!(u.pathname in responses)) throw Error('Unexpected Supabase mock '+u.pathname)
    return respond(route,responses[u.pathname])
  })
  await page.route(API+'/**', route => {
    const req=route.request(), u=new URL(req.url())
    if(req.method()==='OPTIONS') return respond(route,{})
    requests.push({method:req.method(),path:u.pathname,auth:req.headers().authorization})
    const day={
      id:DRAFT, topic:'A safe fashion idea',
      linkedin:{post_text:'Boutique shares a fashion tip.'},
      instagram:{caption:'Fashion styling idea for today.'},
    }
    if(u.pathname=== '/api/shops/'+SHOP+'/content-drafts' && req.method()==='GET') return respond(route,{
      shop_id: SHOP, drafts:[{id:DRAFT,shop_id:foreignDraft?OTHER:SHOP,
        trend_id:TREND, review_state:'DRAFT',created_at:'2026-10-26T09:00:00Z',
        content:{campaign:{shop_id:SHOP,days:[day]},content_days:[],
          review:{status:'DRAFT',can_publish:false}}}],
    })
    if(u.pathname=== '/api/shops/'+SHOP+'/trend-recommendations' && req.method()==='GET') return failTrends
      ? respond(route,{error:'TREND_SOURCES_UNAVAILABLE'},503)
      : respond(route,{shop_id:SHOP,recommendations:[],sources:[
          {source:'google_rss',status:'ok',count:1,observed_at:new Date().toISOString(),message:'Public RSS observed'}],
        complete:false,observed_at:new Date().toISOString()})
    throw Error('Unexpected Feature2 call '+req.method()+' '+u.pathname)
  })
  return requests
}

test('saved retailer draft is visible, read-only, signed, and source failure independent',async({page})=>{
  const calls=await setup(page,{failTrends:true})
  await page.goto('/trends')
  await expect(page.getByRole('heading',{name:'Saved drafts for review'})).toBeVisible()
  await expect(page.getByText('Draft d1000000',{exact:false})).toBeVisible()
  await page.getByText('Draft d1000000',{exact:false}).click()
  await expect(page.getByText('Boutique shares a fashion tip.')).toBeVisible()
  await expect(page.getByText('Trend data or authorized media are unavailable.')).toBeVisible()
  expect(calls.filter(x=>x.path.endsWith('/content-drafts'))).toHaveLength(1)
  expect(calls.every(x=>x.auth==='Bearer signed-offline-mock-only')).toBe(true)
  expect(calls.some(x=>x.method==='POST')).toBe(false)
})

test('foreign tenant draft never renders, viewer cannot create',async({page})=>{
  const calls=await setup(page,{role:'VIEWER',foreignDraft:true})
  await page.goto('/trends')
  await expect(page.getByText('Viewer access: you can read trends but cannot create drafts.')).toBeVisible()
  await expect(page.getByText('No saved drafts for this shop.')).toBeVisible()
  expect(calls.some(x=>x.path.endsWith('/content-drafts'))).toBe(true)
})

test('320px mobile authenticated Trends navigation and saved content review fit viewport',async({page})=>{
  await page.setViewportSize({width:320,height:740})
  await setup(page)
  await page.goto('/trends')
  await page.getByRole('button',{name:'Toggle navigation'}).click()
  await page.getByRole('navigation',{name:'Main navigation'}).getByRole('link',{name:'Trend Intelligence'}).click()
  await expect(page.getByRole('heading',{name:'Saved drafts for review'})).toBeVisible()
  await expect.poll(()=>page.evaluate(()=>
    document.documentElement.scrollWidth <= document.documentElement.clientWidth+1)).toBe(true)
})
