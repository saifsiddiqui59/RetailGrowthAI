import { test, expect } from '@playwright/test'

const SUPABASE = 'https://e2e.supabase.test'
const API = 'https://api.e2e.retailgrowth.test'
const SHOP = 'a1000000-0000-4000-8000-000000000001'
const ASSET = 'a1000000-0000-4000-8000-000000000002'
const USER = 'a9000000-0000-4000-8000-000000000001'
const DRAFT = 'd1000000-0000-4000-8000-000000000001'
const TREND = 'a'.repeat(32)
const tomorrow = () => {
  const d = new Date()
  // Test runner timezone is UTC; tomorrow according to India ensures the same
  // default as the actual browser field at test time.
  const iso = new Intl.DateTimeFormat('en-CA', {timeZone:'Asia/Kolkata',
    year:'numeric',month:'2-digit',day:'2-digit'}).format(d)
  return iso
}
function respond(route,data,status=200) {
  return route.fulfill({status,contentType:'application/json',
    headers:{'Access-Control-Allow-Origin':'*','Access-Control-Allow-Headers':'*'},
    body:JSON.stringify(data)})
}

async function signedInWithInterruptedPost(page,{persist=true}={}) {
  let attempted=0
  let submitted=null
  const calls=[]
  await page.addInitScript(()=>sessionStorage.setItem('retailgrowthai-auth-v1',
    JSON.stringify({access_token:'fixture-signed-token',refresh_token:'fixture-refresh',
      expires_at:2000000000})))
  await page.route(SUPABASE+'/**',route=>{
    const req=route.request(), path=new URL(req.url()).pathname
    if(req.method()==='OPTIONS') return respond(route,{})
    const mock={
      '/auth/v1/user':{id:USER,email:'sample@example.test'},
      '/rest/v1/rpc/retail_platform_me':false,
      '/rest/v1/rpc/retail_onboarding_status':{status:'APPROVED',approval_required:false},
      '/rest/v1/shop_memberships':[{shop_id:SHOP,active:true,role:'OWNER'}],
      '/rest/v1/shops':[{id:SHOP,name:'Example Boutique',slug:'example-boutique'}],
      '/rest/v1/media_assets':[{id:ASSET,shop_id:SHOP,license_name:'owned',mime_type:'image/png'}],
    }
    if (!(path in mock)) throw Error('Unexpected Supabase mock '+path)
    return respond(route,mock[path])
  })
  await page.route(API+'/**',route=>{
    const req=route.request(), path=new URL(req.url()).pathname, method=req.method()
    if(method==='OPTIONS') return respond(route,{})
    calls.push({path,method,auth:req.headers()['authorization']})
    if(path.endsWith('/content-drafts') && method==='GET') {
      return respond(route,{shop_id:SHOP,drafts:submitted && persist ? [{
        id:DRAFT,shop_id:SHOP,trend_id:TREND,review_state:'DRAFT',
        created_at:new Date().toISOString(),
        content:{submission_id:submitted.submission_id,
          campaign:{shop_id:SHOP,days:[{
            id:DRAFT,topic:'Verified styling idea',
            linkedin:{post_text:'A reviewable idea.'},
            instagram:{caption:'Style tip.'},
          }]},content_days:[],review:{status:'DRAFT',can_publish:false}},
      }] : []})
    }
    if(path.endsWith('/content-drafts') && method==='POST') {
      attempted++
      submitted=req.postDataJSON()
      return route.abort('failed') // Azure gateway lost ACK AFTER DB commit
    }
    if(path.endsWith('/trend-recommendations') && method==='GET') {
      const now=Date.now()
      return respond(route,{shop_id:SHOP,complete:false,sources:[
        {source:'google_rss',status:'ok',count:1}],
        recommendations:[{
          trend_id:TREND,source:'google_rss',title:'Saree styling',
          evidence_url:'https://trends.google.com/trending?geo=IN',
          observed_at:new Date(now-60000).toISOString(),
          expires_at:new Date(now+86400000).toISOString(),
          category:'clothing',language:'en-IN',city:'',score:60,
          why_relevant:'Relevant source evidence for retailer review',
        }]})
    }
    throw Error('Unexpected Feature2 request '+method+' '+path)
  })
  return {calls,attempted:()=>attempted}
}

test('lost POST acknowledgement is confirmed via signed GET, never retried',async({page})=>{
  const state=await signedInWithInterruptedPost(page)
  await page.goto('/trends')
  await expect(page.getByText('No saved drafts for this shop.')).toBeVisible()
  await page.getByRole('button',{name:'Draft content for Saree styling'}).click()
  await expect(page.getByText(/response, but this draft was confirmed/)).toBeVisible()
  await expect(page.getByText('Draft d1000000',{exact:false})).toBeVisible()
  expect(state.attempted()).toBe(1)
  expect(state.calls.filter(x=>x.path.endsWith('/content-drafts') && x.method==='POST')).toHaveLength(1)
  expect(state.calls.every(x=>x.auth==='Bearer fixture-signed-token')).toBe(true)
})

test('lost POST without authoritative readback is marked uncertain and not retried',async({page})=>{
  const state=await signedInWithInterruptedPost(page,{persist:false})
  await page.goto('/trends')
  await page.getByRole('button',{name:'Draft content for Saree styling'}).click()
  await expect(page.getByText(/save outcome is not confirmed/)).toBeVisible()
  expect(state.attempted()).toBe(1)
  await expect(page.getByText('No saved drafts for this shop.')).toBeVisible()
})
