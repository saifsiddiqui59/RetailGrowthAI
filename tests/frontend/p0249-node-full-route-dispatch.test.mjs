import test from 'node:test'
import assert from 'node:assert/strict'
import { createCampaignApi, P0249_NODE_PREVIEW_ORIGIN } from '../../frontend/src/features/campaigns/campaign-api.mjs'
import { createSecureHttpDispatcher } from '../../experiments/secure-node-http/src/secure-api-dispatch.mjs'

// Pure source-to-source route compatibility, not a signed-in or hosted E2E.
const ORIGIN = P0249_NODE_PREVIEW_ORIGIN
const CAMPAIGN = '11111111-1111-4111-8111-111111111111'
const DAY = '22222222-2222-4222-8222-222222222222'
const POSTER = '33333333-3333-4333-8333-333333333333'
const JOB = '44444444-4444-4444-8444-444444444444'
const TOKEN = 'synthetic.test.token'
const item = (method, path, kind, invoke, payload = undefined) =>
  ({ method, path: '/api' + path, kind, invoke, payload })
const actions = [
  item('GET', '/campaigns/' + CAMPAIGN, 'read', api => api.getCampaign(CAMPAIGN)),
  item('GET', '/render-jobs/' + JOB, 'read', api => api.getRenderJob(JOB)),
  item('GET', '/render-jobs/' + JOB + '/download', 'read', api => api.getDownload(JOB)),
  item('GET', '/poster-drafts/' + POSTER, 'read', api => api.getPosterDraft(POSTER)),
  item('GET', '/campaigns/' + CAMPAIGN + '/days/' + DAY + '/posters', 'read',
    api => api.listPosterDrafts(CAMPAIGN, DAY)),
  item('GET', '/poster-jobs/' + JOB, 'read', api => api.getPosterJob(JOB)),
  item('GET', '/poster-jobs/' + JOB + '/download', 'read', api => api.getPosterDownload(JOB)),
  item('POST', '/campaigns', 'campaign',
    api => api.createCampaign({ brief: 'synthetic fixture' }), { brief: 'synthetic fixture' }),
  item('PATCH', '/campaigns/' + CAMPAIGN + '/days/' + DAY, 'campaign',
    api => api.saveDay(CAMPAIGN, DAY, {topic:'Topic',linkedin:{post_text:'Text'},instagram:{caption:'Caption'}}),
    {topic:'Topic',linkedin:{post_text:'Text'},instagram:{caption:'Caption'}}),
  item('POST', '/campaigns/' + CAMPAIGN + '/posters', 'poster',
    api => api.createPosterDraft(CAMPAIGN, {
      day_id:DAY,source_asset_id:POSTER,template:'minimal',format:'portrait',
      business_name:'Fixture',accent_color:'#FFFFFF',background_color:'#000000',
    }),
    {day_id:DAY,source_asset_id:POSTER,logo_asset_id:null,template:'minimal',format:'portrait',
      business_name:'Fixture',accent_color:'#FFFFFF',background_color:'#000000',offer_text:null}),
  item('POST', '/poster-drafts/' + POSTER + '/renders', 'poster',
    api => api.createPosterRender(POSTER), {}),
  item('POST', '/poster-drafts/' + POSTER + '/select', 'poster',
    api => api.selectPosterBanner(POSTER,{banner_asset_id:null}),
    {expected_instagram:{banner_asset_id:null}}),
  item('POST', '/campaigns/' + CAMPAIGN + '/renders', 'reel',
    api => api.createRender(CAMPAIGN,DAY),{day_id:DAY,preset:'instagram_reel_30s'}),
]

test('all 13 browser API methods arrive at the existing Node dispatcher with exactly the original paths and JSON',async()=>{
  let index=0, jwtRequests=0
  const seen=[]
  const dispatch=createSecureHttpDispatcher({
    allowedOrigin:ORIGIN,writesEnabled:true,renderWritesEnabled:true,
    readGateway:downstream('read'),campaignGateway:downstream('campaign'),
    posterGateway:downstream('poster'),reelGateway:downstream('reel'),
  })
  function downstream(kind) {
    return async(method,path,bearer,body)=>{
      seen.push({kind,method,path,bearer,body})
      return {status:200,jsonBody:{accepted:true},headers:{}}
    }
  }
  const api=createCampaignApi({
    baseUrl:ORIGIN,browserOrigin:ORIGIN,transport:'node-preview',
    tokenProvider:async()=>{jwtRequests++;return TOKEN},
    fetchImpl:async(url,options)=>{
      const entry=actions[index++]
      assert.ok(entry,'Unexpected extra request')
      assert.equal(url,ORIGIN+entry.path)
      assert.equal(options.method,entry.method)
      assert.equal(options.credentials,undefined)
      assert.equal(options.headers.Authorization,undefined)
      assert.equal(options.headers['x-rgai-supabase-jwt'],TOKEN)
      assert.equal(options.headers['Content-Type'],entry.method==='GET'?undefined:'application/json')
      const request={url,method:options.method,
        headers:new Headers({...options.headers,origin:ORIGIN,'sec-fetch-site':'same-origin'}),
        text:async()=>options.body||''}
      const response=await dispatch(request)
      return {ok:response.status>=200&&response.status<300,status:response.status,
        json:async()=>response.jsonBody}
    },
  })
  for(const entry of actions) await entry.invoke(api)
  assert.equal(index,13)
  assert.equal(jwtRequests,13)
  assert.equal(seen.length,13)
  for(let i=0;i<actions.length;i++) {
    const wanted=actions[i],actual=seen[i]
    assert.equal(actual.kind,wanted.kind)
    assert.equal(actual.method,wanted.method)
    assert.equal(actual.path,wanted.path)
    assert.equal(actual.bearer,'Bearer '+TOKEN)
    assert.deepEqual(actual.body,wanted.payload)
  }
})

test('a verified transport with denied or missing tenant cannot silently become a successful client operation',async()=>{
  for(const status of [401,403,404,409,402,429]){
    let calls=0
    const api=createCampaignApi({
      baseUrl:ORIGIN,browserOrigin:ORIGIN,transport:'node-preview',
      tokenProvider:async()=>TOKEN,
      fetchImpl:async()=>{calls++;return {status,ok:false,json:async()=>({error:'DENIED'})}},
    })
    await assert.rejects(()=>api.createCampaign({brief:'fixture'}),error=>error.status===status)
    assert.equal(calls,1)
  }
})

test('Node mode cannot turn a missing or hostile browser token into a cross-origin fallback request',async()=>{
  for(const browserOrigin of [
    'https://purple-dune-06b5da200.2.azurestaticapps.net',
    'https://evil.example.invalid',ORIGIN+'/', '']){
    let tokenReads=0,network=0
    assert.throws(()=>createCampaignApi({
      baseUrl:ORIGIN,browserOrigin,transport:'node-preview',
      tokenProvider:async()=>{tokenReads++;return TOKEN},
      fetchImpl:async()=>{network++;return {status:200,ok:true,json:async()=>({})}},
    }),/same-origin DEV preview/)
    assert.equal(tokenReads,0)
    assert.equal(network,0)
  }
})
