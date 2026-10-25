import test from 'node:test'
import assert from 'node:assert/strict'
import { createCampaignApi } from '../../frontend/src/features/campaigns/campaign-api.mjs'

const ORIGIN='https://pg.dev.supabase.co'
const API='https://fn.dev.azurewebsites.net'
const JID='11111111-1111-4111-8111-111111111111'
const CID='22222222-2222-4222-8222-222222222222'
const SID='33333333-3333-4333-8333-333333333333'
const AID='44444444-4444-4444-8444-444444444444'
const KEY='sb_publishable_offline_dev_only'
const ROW={id:JID,shop_id:SID,status:'SUCCEEDED',output_asset_id:AID,error_code:null}
const PATH=SID+'/renders/'+JID+'/55555555-5555-4555-8555-555555555555.mp4'
const ASSET={id:AID,shop_id:SID,storage_bucket:'retailgrowth-media',
  mime_type:'video/mp4',object_path:PATH}

function json(status,value) {
  return {status,ok:status>=200&&status<300,
    json:async()=>value}
}
function make(handler) {
  const seen=[]
  const api=createCampaignApi({
    baseUrl:API,
    tokenProvider:async()=>'signed-user-jwt',
    supabaseOrigin:ORIGIN,
    supabasePublishableKey:KEY,
    fetchImpl:async(url,opts)=>{
      seen.push({url,opts})
      return handler(url,opts)
    },
  })
  return {api,seen}
}
function service(url) {
  if (url.startsWith(API)) return json(503,{error:'upstream'})
  const u=new URL(url)
  if (u.pathname==='/rest/v1/render_jobs') return json(200,[ROW])
  if (u.pathname==='/rest/v1/media_assets') return json(200,[ASSET])
  if (u.pathname.startsWith('/storage/v1/object/sign/')) {
    return json(200,{signedURL:'/object/sign/retailgrowth-media/'+PATH+'?token=short-lived'})
  }
  throw new Error('unexpected mock URL')
}

test('Azure twice 503 falls back to RLS GET with same JWT, only for render status',async()=>{
  const {api,seen}=make(service)
  const status=await api.getRenderJob(JID)
  assert.deepEqual(status,{job_id:JID,status:'SUCCEEDED',output_asset_id:AID,error_code:null})
  assert.equal(seen.length,3)
  assert.equal(seen.filter(x=>x.url.startsWith(API)).length,2)
  assert.equal(new URL(seen[2].url).pathname,'/rest/v1/render_jobs')
  assert.equal(seen[2].opts.headers.apikey,KEY)
  assert.equal(seen[2].opts.headers.Authorization,'Bearer signed-user-jwt')
  assert.equal(seen[2].opts.method,'GET')
  assert.equal(seen[2].opts.cache,'no-store')
  assert.equal(seen[2].opts.redirect,'error')
  assert.ok(seen[2].opts.signal instanceof AbortSignal)
})

test('503 private download uses RLS job+asset then signs exact tenant object',async()=>{
  const {api,seen}=make(service)
  const response=await api.getDownload(JID)
  assert.equal(response.url,ORIGIN+'/storage/v1/object/sign/retailgrowth-media/'+PATH+'?token=short-lived')
  assert.deepEqual(seen.map(x=>new URL(x.url).pathname),[
    '/api/render-jobs/'+JID+'/download',
    '/api/render-jobs/'+JID+'/download',
    '/rest/v1/render_jobs','/rest/v1/media_assets',
    '/storage/v1/object/sign/retailgrowth-media/'+PATH,
  ])
  assert.deepEqual(JSON.parse(seen[4].opts.body),{expiresIn:60})
  assert.equal(seen[4].opts.headers.Authorization,'Bearer signed-user-jwt')
  assert.equal(seen[4].opts.headers.apikey,KEY)
  assert.equal(seen[4].opts.redirect,'error')
})

test('RLS empty list is a private not-found; never sign other tenant output',async()=>{
  let signer=0
  const {api}=make((url,opts)=>{
    if (url.startsWith(API)) return json(503,{error:'upstream'})
    if (url.includes('/rest/v1/render_jobs?')) return json(200,[])
    if (url.includes('/object/sign/')) signer++
    return json(500,{})
  })
  await assert.rejects(()=>api.getDownload(JID),e=>e.status===404)
  assert.equal(signer,0)
})

test('foreign asset and wrong bucket cannot be signed',async()=>{
  for (const modified of [
    {...ASSET,shop_id:CID},
    {...ASSET,storage_bucket:'public'},
    {...ASSET,object_path:CID+'/renders/'+JID+'/foreign.mp4'},
    {...ASSET,object_path:SID+'/renders/'+JID+'/../oops.mp4'},
    {...ASSET,mime_type:'image/png'},
  ]) {
    let signer=0
    const {api}=make(url=>{
      if (url.startsWith(API)) return json(503,{})
      if (url.includes('/rest/v1/render_jobs?')) return json(200,[ROW])
      if (url.includes('/rest/v1/media_assets?')) return json(200,[modified])
      if (url.includes('/object/sign/')) signer++
      return json(500,{})
    })
    await assert.rejects(()=>api.getDownload(JID),e=>e.status===503)
    assert.equal(signer,0)
  }
})

test('denied Azure 401, 403, 404 or user-invalid subscription never fall back',async()=>{
  for (const code of [401,403,404,402,429]) {
    const seen=[]
    const {api}=make(url=>{
      seen.push(url)
      if (!url.startsWith(API)) throw new Error('must not bypass customer denial')
      return json(code,{error:code===401?'UNAUTHORIZED':'FORBIDDEN'})
    })
    await assert.rejects(()=>api.getRenderJob(JID),e=>e.status===code)
    assert.equal(seen.length,1)
  }
})

test('no fallback may repeat billable POST or PATCH writes',async()=>{
  let calls=0
  const {api}=make(url=>{
    if (!url.startsWith(API)) throw new Error('server write bypass attempted')
    calls++
    return json(503,{error:'SERVICE_UNAVAILABLE'})
  })
  await assert.rejects(()=>api.createRender(CID,CID),e=>e.status===503)
  await assert.rejects(()=>api.saveDay(CID,CID,{
    topic:'a',linkedin:{},instagram:{},
  }),e=>e.status===503)
  assert.equal(calls,2)
})

test('foreign or malformed returned render job cannot be trusted',async()=>{
  const {api}=make(url=>{
    if (url.startsWith(API)) return json(503,{})
    return json(200,[{...ROW,id:CID}])
  })
  await assert.rejects(()=>api.getRenderJob(JID),e=>e.status===503)
})

test('signer response never accepts modified URL, forged tenant path or no token',async()=>{
  for (const signedURL of [
    'https://evil.example.com/storage/v1/object/sign/retailgrowth-media/'+PATH+'?token=spoof',
    '/object/sign/other-bucket/'+PATH+'?token=spoof',
    '/object/sign/retailgrowth-media/'+SID+'/renders/'+CID+'/other.mp4?token=spoof',
    '/object/sign/retailgrowth-media/'+PATH,
  ]) {
    const {api}=make(url=>{
      if (url.includes('/storage/v1/object/sign/'))return json(200,{signedURL})
      return service(url)
    })
    await assert.rejects(()=>api.getDownload(JID),e=>e.status===503)
  }
})

test('without optional publishable fallback, no Supabase request is attempted',async()=>{
  let count=0
  const api=createCampaignApi({baseUrl:API,tokenProvider:async()=>'jwt',
    fetchImpl:async()=>{count++;return json(503,{})}})
  await assert.rejects(()=>api.getRenderJob(JID),e=>e.status===503)
  assert.equal(count,2)
})

test('secrets and unsupported fallback origins rejected before request',()=>{
  assert.throws(()=>createCampaignApi({baseUrl:API,
    tokenProvider:async()=>'jwt',
    supabaseOrigin:'http://pg.dev.supabase.co',supabasePublishableKey:KEY}),/trusted HTTPS/)
  assert.throws(()=>createCampaignApi({baseUrl:API,
    tokenProvider:async()=>'jwt',
    supabaseOrigin:ORIGIN,supabasePublishableKey:'sb_secret_wrong'}),/Publishable/)
})
