import { test, expect } from '@playwright/test'
const SUPABASE='https://e2e-fixture.supabase.co'
const API='https://api.e2e.retailgrowth.test'
const SHOP='11111111-1111-4111-8111-111111111111'
const CAMPAIGN='22222222-2222-4222-8222-222222222222'
const PLAN='33333333-3333-4333-8333-333333333333'
const JOB='44444444-4444-4444-8444-444444444444'
const LEASE='55555555-5555-4555-8555-555555555555'
const FOREIGN='66666666-6666-4666-8666-666666666666'
const HASH='a'.repeat(64), REVIEW='b'.repeat(64)
const signed=SUPABASE+'/storage/v1/object/sign/retailgrowth-media/'+SHOP+'/renders/'+JOB+'/'+LEASE+'.mp4?token=fixture'
const fixture={id:JOB,shop_id:SHOP,campaign_id:CAMPAIGN,plan_id:PLAN,approved_review_sha256:REVIEW,status:'SUCCEEDED'}
const receipt={job_id:JOB,shop_id:SHOP,status:'SUCCEEDED'}
function reply(route,data,status=200) {
  return route.fulfill({status,contentType:'application/json',
    headers:{'Access-Control-Allow-Origin':'*','Access-Control-Allow-Headers':'*','Access-Control-Allow-Methods':'GET, POST, OPTIONS'},
    body:JSON.stringify(data)})
}
async function mount(page,{role='OWNER',approved=false,existing=false,historyFails=false,foreign=false,ackLost=true}={}) {
  let committed=existing, posts=0, reads=0
  // No real network to either application origin: all fixture calls are intercepted.
  await page.route(SUPABASE+'/**',route=>{
    const request=route.request(), u=new URL(request.url())
    if(request.method()==='OPTIONS')return reply(route,{})
    if(u.pathname==='/rest/v1/feature4_cpu_render_jobs'){
      reads++
      expect(request.headers().authorization).toBe('Bearer fixture-signed-test-only')
      expect(u.searchParams.get('shop_id')).toBe('eq.'+SHOP)
      expect(u.searchParams.get('plan_id')).toBe('eq.'+PLAN)
      return historyFails?reply(route,{},503):reply(route,committed?[foreign?{...fixture,shop_id:FOREIGN}:fixture]:[])
    }
    if(u.pathname.startsWith('/storage/v1/object/sign/'))return route.abort()
    return reply(route,{},404)
  })
  await page.route(API+'/**',route=>{
    const request=route.request(),path=new URL(request.url()).pathname
    if(request.method()==='OPTIONS')return reply(route,{})
    expect(request.headers().authorization).toBe('Bearer fixture-signed-test-only')
    if(path==='/api/campaigns/'+CAMPAIGN+'/feature4-renders'&&request.method()==='POST'){
      expect(request.postDataJSON()).toEqual({plan_id:PLAN,expected_review_hash:REVIEW})
      posts++;committed=true
      return ackLost?route.abort('failed'):reply(route,{...receipt,status:'QUEUED'},202)
    }
    if(path==='/api/feature4-render-jobs/'+JOB&&request.method()==='GET')return reply(route,receipt)
    if(path==='/api/feature4-render-jobs/'+JOB+'/download'&&request.method()==='GET')return reply(route,{...receipt,url:signed})
    return reply(route,{},404)
  })
  await page.goto('/')
  await page.evaluate(async args=>{
    const h=await import('/e2e/fixtures/feature4-review-harness.jsx')
    h.mountReview(args)
  },{shop:SHOP,campaign:CAMPAIGN,plan:PLAN,hash:HASH,review:REVIEW,role,approved})
  await expect(page.getByRole('heading',{name:'Saved Creative Director reviews'})).toBeVisible()
  await expect(page.getByLabel('Saved creative plan')).toBeVisible()
  return {posts:()=>posts,reads:()=>reads}
}
test('explicit review, lost render ACK, exactly one POST then private recovery',async({page})=>{
  const s=await mount(page)
  const render=page.getByRole('button',{name:'Render approved Reel using owned media'})
  await expect(render).toHaveCount(0)
  await page.getByRole('button',{name:'Approve this exact creative revision'}).click()
  await expect(render).toBeEnabled()
  expect(await page.evaluate(()=>window.__f4ReviewCalls)).toEqual([[SHOP,PLAN,HASH]])
  await render.click()
  await expect(page.getByText(/Render not confirmed/)).toBeVisible()
  await expect(render).toBeDisabled()
  await page.getByRole('button',{name:'Check existing render (read only)'}).click()
  await expect(page.getByText(/Existing private CPU render recovered/)).toBeVisible()
  await expect(page.getByLabel('Private CPU render preview')).toHaveAttribute('src',signed)
  await expect(page.getByRole('button',{name:'Download private MP4'})).toBeVisible()
  expect(s.posts()).toBe(1)
  expect(s.reads()).toBe(2)
})
test('existing exact job cannot submit again and terminal polling renews preview',async({page})=>{
  const s=await mount(page,{approved:true,existing:true})
  await page.getByRole('button',{name:'Render approved Reel using owned media'}).click()
  await expect(page.getByText(/A private render already exists/)).toBeVisible()
  await expect(page.getByRole('button',{name:'Render approved Reel using owned media'})).toBeDisabled()
  expect(s.posts()).toBe(0)
})
test('queued render polling reaches terminal private preview',async({page})=>{
  const s=await mount(page,{approved:true,ackLost:false})
  await page.getByRole('button',{name:'Render approved Reel using owned media'}).click()
  await expect(page.getByLabel('Private CPU render preview')).toHaveAttribute('src',signed)
  expect(s.posts()).toBe(1)
})
test('unavailable or foreign history blocks POST; viewer has no render or review control',async({page})=>{
  for(const options of [{historyFails:true},{existing:true,foreign:true}]){
    const s=await mount(page,{approved:true,...options})
    await page.getByRole('button',{name:'Render approved Reel using owned media'}).click()
    await expect(page.getByText(/Render not confirmed/)).toBeVisible()
    expect(s.posts()).toBe(0)
    await page.unrouteAll({behavior:'wait'})
  }
  const s=await mount(page,{role:'VIEWER',approved:true})
  await expect(page.getByRole('button',{name:'Render approved Reel using owned media'})).toHaveCount(0)
  await expect(page.getByRole('button',{name:'Approve this exact creative revision'})).toHaveCount(0)
  expect(s.posts()).toBe(0)
})
