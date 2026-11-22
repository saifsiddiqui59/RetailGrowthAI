import test from 'node:test'
import assert from 'node:assert/strict'
import { createRetailClient } from '../../frontend/src/lib/supabase.js'

const SHOP = '11111111-1111-4111-8111-111111111111'
const OTHER = '22222222-2222-4222-8222-222222222222'
const PLAN = '33333333-3333-4333-8333-333333333333'
const CAMPAIGN = '44444444-4444-4444-8444-444444444444'
const SHA = 'a'.repeat(64)
const REVIEW = 'b'.repeat(64)
const proposal = { version:'creative_direction_v1', source_feature:'feature2',
  shop_id: SHOP, campaign_id: CAMPAIGN, approved:false,
  scenes: [{duration: 30, headline:'Approved shop photo'}] }
const row = { id:PLAN, shop_id: SHOP, campaign_id:CAMPAIGN,
  proposal, proposal_sha256: SHA, state:'DRAFT', review_sha256:null,
  approved_direction:null }

function storage() {
  const data = new Map()
  return { getItem: k => data.get(k) || null,
    setItem: (k, v) => data.set(k, v),
    removeItem: k => data.delete(k) }
}
const json = (body, status=200) => new Response(JSON.stringify(body),
  { status, headers: { 'content-type':'application/json' } })

function client(fetcher) {
  return createRetailClient({ url:'https://retailgrowth-dev.example.supabase.co',
    key:'sb_publishable_test_only', storage:storage(), fetchImpl: fetcher })
}

test('verified shop sees only private RLS plans; explicit review/revoke sends exact JWT RPC', async () => {
  const requests = []
  const api = client(async (url, options) => {
    if (url.includes('/auth/v1/token')) return json({
      access_token:'signed-user-access',refresh_token:'refresh-f4',expires_in:3600 })
    requests.push({url, options})
    if (url.includes('/rest/v1/feature4_creative_plans')) return json([row])
    if (url.includes('/rest/v1/rpc/feature4_review_cpu_plan')) return json({
      shop_id:SHOP,approval_id:PLAN,campaign_id:CAMPAIGN,
      review_hash:REVIEW,status:'APPROVED',
    })
    if (url.includes('/rest/v1/rpc/feature4_revoke_cpu_plan')) return json(true)
    throw Error('unexpected endpoint '+url)
  })
  await api.signIn('owner@example.invalid','secret-password')
  const plans = await api.listFeature4CreativePlans(SHOP)
  assert.equal(plans.length,1)
  assert.deepEqual(plans[0],row)
  const receipt = await api.reviewFeature4CreativePlan(SHOP, PLAN, SHA)
  assert.equal(receipt.review_hash,REVIEW)
  assert.equal((await api.revokeFeature4CreativePlan(SHOP,PLAN)).status,'REVOKED')
  assert.equal(requests.length,3)
  const read = new URL(requests[0].url)
  assert.equal(read.searchParams.get('shop_id'),'eq.'+SHOP)
  assert.equal(read.searchParams.get('limit'),'21')
  assert.equal(requests[0].options.method,'GET')
  assert.deepEqual(JSON.parse(requests[1].options.body),{
    p_plan_id:PLAN,p_expected_source_sha256:SHA,
  })
  assert.equal(requests[1].options.method,'POST')
  assert.deepEqual(JSON.parse(requests[2].options.body),{p_plan_id:PLAN})
  assert.equal(requests[2].options.method,'POST')
  for (const item of requests) {
    assert.equal(item.options.headers.Authorization,'Bearer signed-user-access')
    assert.equal(item.options.headers.apikey,'sb_publishable_test_only')
    assert.doesNotMatch(JSON.stringify(item),/service_role|sb_secret_|[?&]token=/)
  }
})

test('invalid tenant, hash, partial and foreign SQL responses cannot approve creative', async () => {
  const calls = []
  let response = [row]
  const api = client(async (url, options) => {
    if (url.includes('/auth/v1/token')) return json({
      access_token:'signed-user-access',refresh_token:'refresh-f4',expires_in:3600})
    calls.push(url)
    if (url.includes('/rest/v1/feature4_creative_plans')) return json(response)
    if (url.includes('/rest/v1/rpc/feature4_review_cpu_plan')) return json({
      shop_id:OTHER,approval_id:PLAN,campaign_id:CAMPAIGN,
      review_hash:REVIEW,status:'APPROVED',
    })
    if (url.includes('/rest/v1/rpc/feature4_revoke_cpu_plan')) return json(false)
    throw Error('unrecognized request')
  })
  await api.signIn('test@example.invalid','secret-password')
  await assert.rejects(() => api.listFeature4CreativePlans('invalid'),
    /Verified business/)
  response = [{...row,shop_id:OTHER}]
  await assert.rejects(() => api.listFeature4CreativePlans(SHOP),
    /RLS response failed/)
  response = [row]
  await assert.rejects(() => api.reviewFeature4CreativePlan(SHOP, PLAN, 'bad'),
    /revision required/)
  await assert.rejects(() => api.reviewFeature4CreativePlan(OTHER, 'unsafe', SHA),
    /revision required/)
  await assert.rejects(() => api.reviewFeature4CreativePlan(SHOP, PLAN, SHA),
    /not acknowledged/)
  await assert.rejects(() => api.revokeFeature4CreativePlan(SHOP, PLAN),
    /not acknowledged/)
  assert.equal(calls.filter(x => x.includes('/rpc/feature4_review_cpu_plan')).length,1)
  assert.equal(calls.filter(x => x.includes('/rpc/feature4_revoke_cpu_plan')).length,1)
})

test('uncertain HTTP review is never auto-retried or promoted to approved state', async () => {
  let posts=0
  const api = client(async (url) => {
    if (url.includes('/auth/v1/token')) return json({
      access_token:'signed-user-access',refresh_token:'refresh-f4',expires_in:3600})
    if (url.includes('/rest/v1/rpc/feature4_review_cpu_plan')) {
      posts++
      return json({code:'CLOUD_UNAVAILABLE'},503)
    }
    throw Error('unexpected request')
  })
  await api.signIn('test@example.invalid','secret-password')
  await assert.rejects(() => api.reviewFeature4CreativePlan(SHOP, PLAN, SHA))
  assert.equal(posts,1)
})
