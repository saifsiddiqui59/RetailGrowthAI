import {test,expect} from '@playwright/test'

const SUPABASE='https://e2e.supabase.test'
const SHOP='a1000000-0000-4000-8000-000000000001'
const USER='a9000000-0000-4000-8000-000000000001'
const RUN='b1000000-0000-4000-8000-000000000001'
const CAMPAIGN='c1000000-0000-4000-8000-000000000001'
const RENDER='d1000000-0000-4000-8000-000000000001'
const history=[{id:RUN,shop_id:SHOP,created_by:USER,
  prompt:'Create seven-day garment promotion and thirty-second studio Reel',
  mode:'campaign_reel',created_at:'2026-10-29T00:00:00Z'}]
const browserEvents=[
  {run_id:RUN,shop_id:SHOP,actor_user_id:USER,event_seq:1,
   feature:'F2',action:'campaign-submission',status:'PASS',
   summary:'Campaign acknowledged',duration_ms:70,
   details:{campaign_id:CAMPAIGN}},
  {run_id:RUN,shop_id:SHOP,actor_user_id:USER,event_seq:2,
   feature:'F4',action:'ffmpeg-result',status:'PASS',
   summary:'Private FFmpeg job reported success',duration_ms:110,
   details:{render_job_id:RENDER}},
  {run_id:RUN,shop_id:SHOP,actor_user_id:USER,event_seq:3,
   feature:'F3',action:'poster-model',status:'NOT_RUN',
   summary:'Poster studio not invoked',duration_ms:null,details:{}},
]
const workerFor=(id)=>({
  shop_id:SHOP,job_id:id,source:'trusted_backend_persisted',
  events:[{id:'e1000000-0000-4000-8000-000000000001',shop_id:SHOP,
    job_id:id,feature:id===RENDER?'F4':'F2',
    operation:id===RENDER?'render.complete':'planning.complete',
    status:'SUCCEEDED',attempt:1,elapsed_ms:3100,
    metadata:id===RENDER
      ?{codec:'h264/aac',video_width:1080,video_height:1920,duration_seconds:30}
      :{generated_days:7,planner_mode:'dev_mock'},
    recorded_at:'2026-10-29T00:00:00Z'}],
})
function reply(route,body,status=200){return route.fulfill({
  status,contentType:'application/json',
  headers:{'Access-Control-Allow-Origin':'*',
    'Access-Control-Allow-Methods':'GET,POST,OPTIONS',
    'Access-Control-Allow-Headers':'apikey,authorization,content-type,prefer'},
  body:JSON.stringify(body),
})}
async function setup(page,{role='OWNER',rpcMissing=false,events=browserEvents}={}){
 const requests=[]
 await page.addInitScript(()=>sessionStorage.setItem('retailgrowthai-auth-v1',
  JSON.stringify({access_token:'signed-testing-jwt',
    refresh_token:'offline-only',expires_at:2000000000})))
 await page.route(SUPABASE+'/**',route=>{
  const req=route.request(),path=new URL(req.url()).pathname
  if(req.method()==='OPTIONS')return reply(route,{})
  if(path==='/auth/v1/user')return reply(route,{id:USER,email:'owner@example.test'})
  if(path==='/rest/v1/rpc/retail_platform_me')return reply(route,false)
  if(path==='/rest/v1/rpc/retail_onboarding_status')return reply(route,{status:'APPROVED'})
  if(path==='/rest/v1/shop_memberships')return reply(route,[{shop_id:SHOP,active:true,role}])
  if(path==='/rest/v1/shops')return reply(route,[{id:SHOP,name:'Boutique Studio',slug:'boutique-test'}])
  if(path==='/rest/v1/media_assets')return reply(route,[])
  if(path==='/rest/v1/feature_test_runs')return reply(route,history)
  if(path==='/rest/v1/feature_test_events')return reply(route,events)
  if(path==='/rest/v1/rpc/retail_feature_worker_spans'){
    const input=req.postDataJSON()
    requests.push({path,body:input,auth:req.headers().authorization})
    if(rpcMissing)return reply(route,{message:'RPC not released'},404)
    return reply(route,workerFor(input.p_job_id))
  }
  throw Error('Unexpected Supabase request '+req.method()+' '+path)
 })
 await page.route('https://api.e2e.retailgrowth.test/**',route=>
   reply(route,{error:'NO_MUTATION_IN_THIS_TEST'},403))
 return requests
}
test('saved trace renders every feature card without runtime error, then reads trusted worker RPC',async({page})=>{
 const errors=[]
 page.on('pageerror',e=>errors.push(e.message))
 const calls=await setup(page)
 await page.goto('/testing-chat')
 await expect(page.getByRole('heading',{name:'Testing Chat & Feature Trace'})).toBeVisible()
 await page.getByRole('button',{name:/Create seven-day garment promotion/}).click()
 await expect(page.getByRole('heading',{name:'Server-authored worker receipts'})).toBeVisible()
 await expect(page.getByRole('heading',{name:'What to improve next'})).toBeVisible()
 await page.getByText('Review all feature assessments').click()
 await expect(page.getByText(/F3 · Poster \/ model/)).toBeVisible()
 await expect(page.getByText('Poster studio not invoked')).toBeVisible()
 await page.getByRole('button',{name:'Check server worker receipts'}).click()
 await expect(page.getByText(/F4 · render.complete · SUCCEEDED/)).toBeVisible()
 await expect(page.getByText(/F2 · planning.complete · SUCCEEDED/)).toBeVisible()
 expect(calls).toHaveLength(2)
 expect(calls.map(x=>x.body.p_job_id).sort()).toEqual([CAMPAIGN,RENDER].sort())
 expect(calls.every(x=>x.auth==='Bearer signed-testing-jwt')).toBe(true)
 expect(errors).toEqual([])
})
test('unreleased backend RPC displays unverified state, never fabricated job failure',async({page})=>{
 const calls=await setup(page,{rpcMissing:true})
 await page.goto('/testing-chat')
 await page.getByRole('button',{name:/Create seven-day garment promotion/}).click()
 await page.getByRole('button',{name:'Check server worker receipts'}).click()
 await expect(page.getByText(/Trusted span table is not released/)).toBeVisible()
 expect(calls).toHaveLength(1)
 await expect(page.getByText(/Private FFmpeg job reported success/)).toBeVisible()
})
test('VIEWER cannot enter private trace history or request trusted worker data',async({page})=>{
 const calls=await setup(page,{role:'VIEWER'})
 await page.goto('/testing-chat')
 await expect(page.getByText('No active OWNER/EDITOR business is available.')).toBeVisible()
 await expect(page.getByRole('button',{name:'Check server worker receipts'})).toHaveCount(0)
 expect(calls).toHaveLength(0)
})

test('poor-quality F4 output is a quality improvement priority, not an execution failure',async({page})=>{
 const rated=[
  ...browserEvents,
  {run_id:RUN,shop_id:SHOP,actor_user_id:USER,event_seq:4,
   feature:'F4',action:'human-quality-review',status:'QUALITY_REVIEW',
   summary:'Reviewer judged production quality below the target',
   duration_ms:null,details:{score:1,note:'Pacing and subtitles are poor'}},
 ]
 await setup(page,{events:rated})
 await page.goto('/testing-chat')
 await page.getByRole('button',{name:/Create seven-day garment promotion/}).click()
 const section=page.getByRole('region',{name:'What to improve next'})
 await expect(section.getByText(/Output quality: 1\/5 \(human rating\)/)).toBeVisible()
 await expect(section.getByText(/Review scene pacing, 1080x1920 frame/)).toBeVisible()
 await expect(section.getByText(/a reviewer rated its quality 1\/5/)).toBeVisible()
 await expect(section.getByText(/observed execution failure/i)).toHaveCount(0)
})
