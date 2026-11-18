import test from 'node:test'
import assert from 'node:assert/strict'
import { executeFeatureTrace } from '../../frontend/src/features/testing/trace-runner.mjs'
import { createTraceStore } from '../../frontend/src/features/testing/trace-store.mjs'

const shopId = '11111111-1111-4111-8111-111111111111'
const userId = '22222222-2222-4222-8222-222222222222'
const id = '33333333-3333-4333-8333-333333333333'
const assetId = '44444444-4444-4444-8444-444444444444'
const campaignId = '55555555-5555-4555-8555-555555555555'
const dayId = '66666666-6666-4666-8666-666666666666'
const jobId = '77777777-7777-4777-8777-777777777777'
const prompt = 'Make an engaging seven-day boutique Instagram campaign.'
function mockStore() {
  const events = []
  return { events, createRun: async args => args,
    append: async args => {
      const event = { ...args, event_seq: args.seq, details: args.details || {} }
      events.push(event)
      return event
    } }
}
const client = { listShops: async () => [{
  id: shopId, name: 'Demo boutique', membership: { active: true, role: 'OWNER' },
}], listMediaAssets: async () => [
  { shop_id: shopId, id: assetId, license_name: 'owned' },
] }
const trendApi = { improvePrompt: async (shop, brief) => ({
  shop_id: shop, original_prompt: brief, improved_prompt: brief + ' More clear.',
  provider_mode: 'deterministic', review_status: 'NEEDS_REVIEW',
  can_publish: false, usage: { paid_inference_calls: 0 },
}) }
const options = { id, shopId, userId, prompt, mode: 'prompt',
  assetId, startDate: '2026-11-01', client, trendApi,
  sleep: async () => {} }
test('prompt-only makes real intended F2 call and marks nonexecuted stages NOT_RUN', async () => {
  const store = mockStore()
  const result = await executeFeatureTrace({ ...options, store,
    campaignApi: { createCampaign: async () => { throw new Error('Unexpected POST') } } })
  assert.equal(result.status, 'PASS')
  assert.deepEqual(store.events.map(e => e.status),
    ['PASS','PASS','NOT_RUN','NOT_RUN','NOT_RUN','NOT_RUN','NOT_RUN'])
  assert.equal(store.events[1].details.paid_inference_calls, 0)
  assert.ok(store.events.some(e => e.feature === 'F5' && e.status === 'NOT_RUN'))
})
test('campaign+reel observes actual IDs, but never fabricates F3/F5/F7', async () => {
  const store = mockStore()
  let posts = 0
  const campaignApi = {
    createCampaign: async () => { posts++; return { campaign_id: campaignId, status: 'PLANNING' } },
    getCampaign: async () => ({ id: campaignId, shop_id: shopId, status: 'DRAFT', duration_days: 7,
      days: Array.from({length:7}, (_,i) => ({
        id: i === 0 ? dayId : '66666666-6666-4666-8666-' + String(i+1).padStart(12, '0'),
        shop_id: shopId, campaign_id: campaignId, day_index:i+1,
        scheduled_date:'2026-11-0'+(i+1),topic:'Daily outfits '+(i+1),
        linkedin: {post_text:'Wear with confidence '+(i+1)},
        instagram: {caption:'Shop your wardrobe '+(i+1), reel: {storyboard:[]}},
      })) }),
    createRender: async () => ({ job_id: jobId, status: 'QUEUED' }),
    getRenderJob: async () => ({ shop_id: shopId, job_id: jobId, status: 'SUCCEEDED' }),
  }
  const result = await executeFeatureTrace({ ...options, mode: 'campaign_reel',
    store, campaignApi })
  assert.equal(result.status, 'PASS')
  assert.equal(posts, 1)
  assert.equal(store.events.find(e => e.action === 'campaign-planning').details.campaign_id, campaignId)
  assert.equal(store.events.find(e => e.action === 'ffmpeg-result').status, 'PASS')
  assert.equal(store.events.filter(e => /^campaign-day-/.test(e.action)).length, 7)
  assert.equal(store.events.find(e => e.action === 'campaign-day-7').details.linkedin_post, 'Wear with confidence 7')
  for (const f of ['F3','F5','F7']) assert.ok(store.events.some(e => e.feature === f && e.status === 'NOT_RUN'))
})
test('lost campaign POST acknowledgement stays UNKNOWN and is never replayed', async () => {
  const store = mockStore()
  let posts = 0
  const result = await executeFeatureTrace({ ...options, mode: 'campaign', store,
    campaignApi: { createCampaign: async () => { posts++; throw new Error('gateway closed') } } })
  assert.equal(result.status, 'UNKNOWN')
  assert.equal(posts, 1)
  assert.equal(store.events.at(-1).status, 'UNKNOWN')
  assert.equal(store.events.at(-1).details.automatic_retry, false)
})
test('a VIEWER or foreign shop cannot pass the signed-in membership check', async () => {
  const store = mockStore()
  const result = await executeFeatureTrace({ ...options, store,
    client: { ...client, listShops: async () => [{
      id: shopId, membership: { active: true, role: 'VIEWER' },
    }] } })
  assert.equal(result.status, 'FAIL')
  assert.deepEqual(store.events.map(e => e.feature), ['F1'])
})
test('PostgREST trace client rejects cross-tenant history and sends user JWT only', async () => {
  const calls = []
  const store = createTraceStore({
    supabaseUrl: 'https://example.supabase.co',
    publishableKey: 'publishable',
    tokenProvider: async () => 'signed-in-user-token',
    fetchImpl: async (url, init) => {
      calls.push({ url, init })
      return { ok: true, status: 200, json: async () => [
        { id, shop_id: userId }, // deliberately wrong shop
      ] }
    },
  })
  await assert.rejects(() => store.listRuns(shopId), /tenant mismatch/)
  assert.equal(calls[0].init.headers.Authorization, 'Bearer signed-in-user-token')
  assert.equal(calls[0].init.headers.apikey, 'publishable')
  assert.ok(calls[0].url.includes('shop_id=eq.'))
})

test('incomplete or cross-campaign draft cannot be credited as seven-day output', async () => {
  for (const broken of ['short', 'foreign']) {
    const store=mockStore()
    const campaignApi={
      createCampaign:async()=>({campaign_id:campaignId,status:'PLANNING'}),
      getCampaign:async()=>({
        id:campaignId,shop_id:shopId,status:'DRAFT',
        days:Array.from({length:broken==='short'?1:7}, (_,i)=>({
          id:i===0?dayId:'66666666-6666-4666-8666-'+String(i+1).padStart(12,'0'),
          shop_id:shopId,campaign_id:broken==='foreign'?'aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa':campaignId,
          day_index:i+1,topic:'Copy',linkedin:{post_text:'Sample'},
          instagram:{caption:'Copy',reel:{storyboard:[]}},
        })),
      }),
      createRender:async()=>{ throw new Error('Render must never be submitted') },
    }
    const outcome=await executeFeatureTrace({...options,mode:'campaign_reel',store,campaignApi})
    assert.equal(outcome.status,'UNKNOWN')
    assert.ok(store.events.some(e=>e.action==='campaign-planning'&&e.status==='UNKNOWN'))
    assert.equal(store.events.filter(e=>e.action.startsWith('campaign-day-')).length,0)
  }
})

test('API correlation receipts attach to the matching F2 step without leaking secret fields', async()=>{
 const store=mockStore()
 const receipt={source:'trend',operation:'/shops/:id/improve-prompt',method:'POST',
  status_code:200,request_id:'1234567890abcdef1234567890abcdef',elapsed_ms:90,
  attempt:1,handler_marker_seen:true}
 // Correlation only appears after Feature #2's authenticated response.
  const received=[]
  const observedTrend={improvePrompt:async(...args)=>{
    const reply=await trendApi.improvePrompt(...args)
    received.push(receipt)
    return reply
  }}
  const result=await executeFeatureTrace({...options,store,trendApi:observedTrend,
    getNetworkEvidence:()=>received})
 assert.equal(result.status,'PASS')
 const feature2=store.events.find(e=>e.action==='prompt-improvement')
 assert.equal(feature2.details.http_receipts.length,1)
 assert.equal(feature2.details.http_receipts[0].request_id,receipt.request_id)
 assert.equal(feature2.details.http_receipts[0].operation,'/shops/:id/improve-prompt')
 assert.ok(!JSON.stringify(feature2.details.http_receipts).includes(shopId))
})
