import test from 'node:test'
import assert from 'node:assert/strict'
import { readFileSync } from 'node:fs'
import { createCampaignApi, P0249_NODE_PREVIEW_ORIGIN } from '../../frontend/src/features/campaigns/campaign-api.mjs'
import { createSecureHttpDispatcher } from '../../experiments/secure-node-http/src/secure-api-dispatch.mjs'

// All tests are offline. No real JWT, DNS, Azure, Supabase or test customer.
const SHOP = '11111111-1111-4111-8111-111111111111'
const DAY = '22222222-2222-4222-8222-222222222222'
const USER_TOKEN = 'example.signed.fixture'
const base = P0249_NODE_PREVIEW_ORIGIN
const make = (opts={}) => createCampaignApi({
  baseUrl: base, browserOrigin: base, transport: 'node-preview',
  tokenProvider: async () => USER_TOKEN, fetchImpl: async () => ({
    status: 200, ok: true, json: async () => ({ok: true}),
  }), ...opts,
})

test('Node gateway option rejects wrong site, forged preview and unsupported mode before obtaining a JWT', async () => {
  let tokens = 0, sent = 0
  const opts = {tokenProvider: async () => { tokens++; return USER_TOKEN },
    fetchImpl: async () => { sent++; throw Error('should never fetch') }}
  for (const browserOrigin of ['', 'https://purple-dune-06b5da200.2.azurestaticapps.net',
    'https://attacker.invalid', base + '/', 'http://'+new URL(base).host]) {
    assert.throws(() => make({...opts,browserOrigin}), /same-origin DEV preview/)
  }
  for (const badOrigin of ['https://some-other.azurestaticapps.net',
    'https://evil.invalid', base+'/', 'http://'+new URL(base).host]) {
    assert.throws(() => make({...opts,baseUrl:badOrigin}), /same-origin DEV preview|HTTPS origin/)
  }
  assert.throws(() => make({...opts,transport:'node'}), /Unsupported/)
  assert.equal(tokens,0)
  assert.equal(sent,0)
})

test('only this preview can use the custom Supabase header; never Authorization or cookies', async () => {
  const calls = []
  const api = make({fetchImpl: async (url, options) => {
    calls.push({url,options})
    return {status:200,ok:true,json:async()=>({ok:true})}
  }})
  await api.getCampaign(SHOP)
  await api.createCampaign({brief:'synthetic only'})
  await api.saveDay(SHOP,DAY,{topic:'t',linkedin:{},instagram:{}})
  await api.createRender(SHOP,DAY)
  await api.createPosterDraft(SHOP,{
    day_id:DAY,source_asset_id:DAY,template:'bold',format:'portrait',
    business_name:'Test',accent_color:'#FFFFFF',background_color:'#000000',
  })
  await api.getPosterDraft(DAY)
  await api.listPosterDrafts(SHOP,DAY)
  await api.createPosterRender(DAY)
  await api.getPosterJob(DAY)
  await api.getPosterDownload(DAY)
  await api.selectPosterBanner(DAY,{banner_asset_id:null})
  await api.getRenderJob(DAY)
  await api.getDownload(DAY)
  assert.equal(calls.length,13)
  for (const {url,options} of calls) {
    assert.equal(new URL(url).origin,base)
    assert.equal(options.headers['x-rgai-supabase-jwt'],USER_TOKEN)
    assert.equal(options.headers.Authorization,undefined)
    assert.equal(options.credentials,undefined)
    assert.equal(options.redirect,'error')
    assert.equal(options.cache,'no-store')
  }
  assert.equal(calls.filter(x=>x.options.method==='POST').length,5)
  assert.equal(calls.filter(x=>x.options.method==='PATCH').length,1)
})

test('same-origin browser JWT transport composes with actual Node dispatch and preserves original API contract', async () => {
  const seen=[]
  const gate=(kind)=>async(method,path,auth,body)=>{
    seen.push({kind,method,path,auth,body})
    return {status:200,jsonBody:{kind,status:'DRAFT'},headers:{}}
  }
  const dispatch=createSecureHttpDispatcher({
    readGateway:gate('read'),campaignGateway:gate('campaign'),
    posterGateway:gate('poster'),reelGateway:gate('reel'),
    writesEnabled:true,renderWritesEnabled:true,allowedOrigin:base,
  })
  const api=make({fetchImpl:async(url,opts)=>{
    const request={
      url,method:opts.method,text:async()=>opts.body || '',
      headers:new Headers({...opts.headers,
        origin:base,'sec-fetch-site':'same-origin'}),
    }
    const reply=await dispatch(request)
    return {status:reply.status,ok:reply.status>=200&&reply.status<300,
      json:async()=>reply.jsonBody}
  }})
  await api.getCampaign(SHOP)
  await api.createCampaign({brief:'test'})
  await api.createPosterRender(DAY)
  await api.createRender(SHOP,DAY)
  assert.deepEqual(seen.map(x=>x.kind),['read','campaign','poster','reel'])
  assert.deepEqual(seen.map(x=>x.auth),Array(4).fill('Bearer '+USER_TOKEN))
  assert.equal(seen[3].body.preset,'instagram_reel_30s')
  assert.equal(seen[3].body.day_id,DAY)
})

test('invalid or absent preview JWT is rejected before any network call', async () => {
  let calls=0
  for (const token of ['', 'short', 'spaces are rejected',
    'a'.repeat(8193),'valid,bad','valid\nother']) {
    const api=make({tokenProvider:async()=>token,fetchImpl:async()=>{calls++;return null}})
    await assert.rejects(()=>api.getCampaign(SHOP),/sign in again/)
  }
  assert.equal(calls,0)
})

test('preview 503 read retries remain bounded, never mask error with Python RLS fallback', async () => {
  let calls=0
  const api=make({
    supabaseOrigin:'https://jeearzffnjbvghwjjjrf.supabase.co',
    supabasePublishableKey:'sb_publishable_safe_public_example',
    fetchImpl:async()=>{
      calls++
      return {status:503,ok:false,json:async()=>({error:'SERVICE_UNAVAILABLE'})}
    },
  })
  await assert.rejects(()=>api.getRenderJob(DAY),e=>e.status===503)
  assert.equal(calls,2)
  await assert.rejects(()=>api.getDownload(DAY),e=>e.status===503)
  assert.equal(calls,4)
})

test('ambiguous preview POST/PATCH must not replay or fail over to legacy Python', async () => {
  const requested=[]
  const api=make({fetchImpl:async(url,opts)=>{
    requested.push({url,method:opts.method})
    return {status:503,ok:false,json:async()=>({error:'SERVICE_UNAVAILABLE'})}
  }})
  await assert.rejects(()=>api.createCampaign({brief:'test'}),e=>e.status===503)
  await assert.rejects(()=>api.createRender(SHOP,DAY),e=>e.status===503)
  await assert.rejects(()=>api.saveDay(SHOP,DAY,{topic:'t',linkedin:{},instagram:{}}),
    e=>e.status===503)
  assert.equal(requested.length,3)
  assert.deepEqual(requested.map(x=>x.method),['POST','POST','PATCH'])
  assert.ok(requested.every(x=>x.url.startsWith(base+'/api/')))
})

test('default customer transport is untouched and preview flag is source-only',async()=>{
  const calls=[]
  const api=createCampaignApi({baseUrl:'https://rgai-dev-functions-d4e5ddbd.azurewebsites.net',
    tokenProvider:async()=>USER_TOKEN,fetchImpl:async(url,options)=>{
      calls.push({url,options})
      return {ok:true,status:200,json:async()=>({ok:true})}
    }})
  await api.getCampaign(SHOP)
  assert.equal(calls[0].options.headers.Authorization,'Bearer '+USER_TOKEN)
  assert.equal(calls[0].options.headers['x-rgai-supabase-jwt'],undefined)
  const ui=readFileSync(new URL('../../frontend/src/features/campaigns/CampaignDashboard.jsx',import.meta.url),'utf8')
  const env=readFileSync(new URL('../../frontend/.env.production',import.meta.url),'utf8')
  assert.match(ui,/VITE_P0249_NODE_TRANSPORT_ENABLED === 'true'/)
  assert.doesNotMatch(env,/VITE_P0249_NODE_TRANSPORT_ENABLED\s*=\s*true/)
  assert.match(env,/VITE_CAMPAIGN_API_BASE_URL=https:\/\/rgai-dev-functions-d4e5ddbd[.]azurewebsites[.]net/)
})
