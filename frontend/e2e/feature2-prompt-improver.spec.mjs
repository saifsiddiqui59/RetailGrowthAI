import { test, expect } from '@playwright/test'

const SUPABASE = 'https://e2e.supabase.test'
const API = 'https://api.e2e.retailgrowth.test'
const SHOP = 'a1000000-0000-4000-8000-000000000001'
const USER = 'a9000000-0000-4000-8000-000000000001'
const ASSET = 'a1000000-0000-4000-8000-000000000002'
const TREND = 'a'.repeat(32)

function reply(route, data, status=200) {
  return route.fulfill({status,contentType:'application/json',
    headers:{'Access-Control-Allow-Origin':'*','Access-Control-Allow-Headers':'*'},
    body:JSON.stringify(data)})
}

async function setup(page, { role='OWNER', failImprovement=false, withTrend=false }={}) {
  const calls = []
  await page.addInitScript(() => sessionStorage.setItem('retailgrowthai-auth-v1',
    JSON.stringify({access_token:'signed-prompt-test-jwt',
      refresh_token:'mock-only-refresh',expires_at:2000000000})))
  await page.route(SUPABASE+'/**', route => {
    const req=route.request(), path=new URL(req.url()).pathname
    if(req.method()==='OPTIONS') return reply(route,{})
    const responses={
      '/auth/v1/user':{id:USER,email:'owner@example.test'},
      '/rest/v1/rpc/retail_platform_me':false,
      '/rest/v1/rpc/retail_onboarding_status':{status:'APPROVED',approval_required:false},
      '/rest/v1/shop_memberships':[{shop_id:SHOP,active:true,role}],
      '/rest/v1/shops':[{id:SHOP,name:'Thread & Loom Studio',slug:'test-boutique'}],
      '/rest/v1/media_assets':[{id:ASSET,shop_id:SHOP,license_name:'owned synthetic fixture',mime_type:'image/png'}],
    }
    if (!(path in responses)) throw Error('Unexpected Supabase request '+path)
    return reply(route,responses[path])
  })
  await page.route(API+'/**', route=>{
    const req=route.request(), path=new URL(req.url()).pathname
    if(req.method()==='OPTIONS') return reply(route,{})
    calls.push({path,method:req.method(),auth:req.headers().authorization,
      body:req.method()==='POST' ? req.postDataJSON() : null})
    if(path.endsWith('/content-drafts') && req.method()==='GET')
      return reply(route,{shop_id:SHOP,drafts:[]})
    if(path.endsWith('/trend-recommendations') && req.method()==='GET')
      return reply(route,{shop_id:SHOP,complete:false,sources:[],
        recommendations:withTrend?[{
          trend_id:TREND,source:'google_rss',title:'Saree styling',
          evidence_url:'https://trends.google.com/trending?geo=IN',
          observed_at:new Date(Date.now()-1000).toISOString(),
          expires_at:new Date(Date.now()+86400000).toISOString(),
          category:'clothing',language:'en-IN',score:80,
        }]:[]})
    if(path.endsWith('/improve-prompt') && req.method()==='POST') {
      if(failImprovement) return reply(route,{error:'PROVIDER_UNAVAILABLE'},503)
      const body=req.postDataJSON()
      return reply(route,{
        shop_id:SHOP,original_prompt:body.original_prompt,
        improved_prompt:'IMPROVED: '+body.original_prompt+' | safe profile styling guide',
        improvement_suggestions:['Only verified retailer context was used','Require human approval'],
        business_context_used:{business_name:'Thread & Loom Studio',city:'Nagpur'},
        output_formats:body.output_formats,language:body.language,
        review_status:'NEEDS_REVIEW',provider_mode:'deterministic',
        usage:{paid_inference_calls:0,estimated_paid_cost_usd:0},can_publish:false,
      })
    }
    if(path.endsWith('/content-drafts') && req.method()==='POST') {
      return reply(route,{shop_id:SHOP,status:'DRAFT',draft_id:'d1000000-0000-4000-8000-000000000001'},201)
    }
    throw Error('Unexpected API request '+req.method()+' '+path)
  })
  return calls
}

test('OFF by default; ON auto-previews side-by-side and edited prompts never auto-generate',async({page})=>{
  const calls=await setup(page)
  await page.goto('/trends')
  const toggle=page.getByRole('checkbox',{name:'Improve Prompt with AI'})
  await expect(toggle).not.toBeChecked()
  await expect(page.getByRole('button',{name:'Improve Prompt'})).toHaveCount(0)
  await toggle.check()
  await expect(page.getByLabel('Original prompt')).toBeVisible()
  await expect(page.getByText('Enhanced prompt ready for your review.')).toBeVisible()
  await expect(page.getByLabel('Improved prompt (editable)')).toBeVisible()
  await expect(page.getByText('Only verified retailer context was used')).toBeVisible()
  await page.getByLabel('Improved prompt (editable)').fill('My reviewed editorial draft')
  await page.getByRole('button',{name:'Use Improved Prompt'}).click()
  await expect(page.getByText('Improved prompt selected for the next draft.')).toBeVisible()
  await page.getByRole('button',{name:'Restore Original'}).click()
  await expect(page.getByText('Original request selected. Improvement never runs automatically.')).toBeVisible()
  await toggle.uncheck()
  await expect(page.getByLabel('Original prompt')).toHaveCount(0)
  expect(calls.filter(c=>c.path.endsWith('/improve-prompt'))).toHaveLength(1)
  expect(calls.filter(c=>c.path.endsWith('/content-drafts') && c.method==='POST')).toHaveLength(0)
  expect(calls.every(c=>c.auth==='Bearer signed-prompt-test-jwt')).toBe(true)
})

test('explicit Generate Content uses edited improved prompt once, never silently infers trend',async({page})=>{
  const calls=await setup(page,{withTrend:true})
  await page.goto('/trends')
  await page.getByRole('checkbox',{name:'Improve Prompt with AI'}).check()
  await page.getByLabel('Improved prompt (editable)').fill('Approved seven-day styling direction')
  await page.getByRole('button',{name:'Use Improved Prompt'}).click()
  await page.getByLabel('Verified trend for this draft').selectOption(TREND)
  await page.getByRole('button',{name:'Generate Content'}).click()
  await expect(page.getByText(/Content draft saved for retailer review/)).toBeVisible()
  const posts=calls.filter(c=>c.path.endsWith('/content-drafts') && c.method==='POST')
  expect(posts).toHaveLength(1)
  expect(posts[0].body.campaign.brief).toBe('Approved seven-day styling direction')
})

test('failed improvement retains original; viewer cannot call endpoint',async({page})=>{
  const calls=await setup(page,{failImprovement:true})
  await page.goto('/trends')
  const before=await page.getByLabel('Content brief').inputValue()
  await page.getByRole('checkbox',{name:'Improve Prompt with AI'}).check()
  await expect(page.getByText(/Your original request is preserved/)).toBeVisible()
  expect(await page.getByLabel('Content brief').inputValue()).toBe(before)
  expect(calls.filter(c=>c.path.endsWith('/content-drafts') && c.method==='POST')).toHaveLength(0)
})

test('320px mobile layout and viewer access remain fail-closed',async({page})=>{
  await page.setViewportSize({width:320,height:730})
  const calls=await setup(page,{role:'VIEWER'})
  await page.goto('/trends')
  await page.getByRole('checkbox',{name:'Improve Prompt with AI'}).check()
  await expect(page.getByRole('button',{name:'Improve Prompt',exact:true})).toBeDisabled()
  await expect(page.getByRole('button',{name:'Generate Content'})).toBeDisabled()
  await expect.poll(()=>page.evaluate(()=>
    document.documentElement.scrollWidth<=document.documentElement.clientWidth+1)).toBe(true)
  expect(calls.filter(c=>c.path.endsWith('/improve-prompt'))).toHaveLength(0)
})

test('paid Azure AI enhancement never runs merely because a checkbox was ticked',async({page})=>{
  const calls=await setup(page)
  await page.goto('/trends')
  await page.getByRole('checkbox',{name:'Use real Azure AI model (requires approved shop budget)'}).check()
  await page.getByRole('checkbox',{name:'Improve Prompt with AI'}).check()
  await expect(page.getByRole('button',{name:'Improve Prompt',exact:true})).toBeEnabled()
  await expect(page.getByLabel('Original prompt')).toHaveCount(0)
  expect(calls.filter(c=>c.path.endsWith('/improve-prompt') || c.path.endsWith('/improve-prompt-ai'))).toHaveLength(0)
  expect(calls.filter(c=>c.method==='POST')).toHaveLength(0)
})
