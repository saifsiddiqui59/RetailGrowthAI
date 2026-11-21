import test from 'node:test'
import assert from 'node:assert/strict'
import { createRetailClient } from '../../frontend/src/lib/supabase.js'

const SHOP='11111111-1111-4111-8111-111111111111'
const CAMPAIGN='22222222-2222-4222-8222-222222222222'
const DAY='33333333-3333-4333-8333-333333333333'
const PLAN='44444444-4444-4444-8444-444444444444'
const SHA='a'.repeat(64)
const json=(item,status=200)=>new Response(JSON.stringify(item),
  {status,headers:{'content-type':'application/json'}})
const storage=()=>{const values=new Map();return{
  getItem:k=>values.get(k)||null,setItem:(k,v)=>values.set(k,v),
  removeItem:k=>values.delete(k)}}
function fixture(fetchImpl, feature4ApiOrigin='https://retailgrowth-function.example.com') {
  return createRetailClient({url:'https://retailgrowthai-test.supabase.co',
    key:'sb_publishable_fixture',fetchImpl,feature4ApiOrigin,
    storage:storage()})
}

test('only RLS-saved same-shop draft video day can issue server-side plan with exact JWT',async()=>{
  const calls=[]
  const api=fixture(async(url,options)=>{
    if(url.includes('/auth/v1/token'))return json({
      access_token:'jwt-actor',refresh_token:'refresh-f4',expires_in:3600})
    calls.push({url,options})
    if(url.includes('/rest/v1/campaigns')) return json([{
      id:CAMPAIGN,shop_id:SHOP,status:'DRAFT'}])
    if(url.includes('/rest/v1/campaign_days')) return json([{
      id:DAY,shop_id:SHOP,campaign_id:CAMPAIGN,review_status:'DRAFT',
      day_index:1,instagram:{reel:{duration_seconds:30,aspect_ratio:'9:16',
        music_asset_id:null,storyboard:[{start_seconds:0,duration_seconds:30,
          headline:'Demo'}]}}}])
    if(url.includes('/api/campaigns/'))return json({
      plan_id:PLAN,shop_id:SHOP,campaign_id:CAMPAIGN,
      status:'DRAFT',proposal_sha256:SHA},201)
    throw Error('unexpected '+url)
  })
  await api.signIn('owner@example.invalid','password123')
  const days=await api.listFeature4SourceDays(SHOP)
  assert.deepEqual(days,[{id:DAY,shop_id:SHOP,campaign_id:CAMPAIGN,day_index:1}])
  const result=await api.issueFeature4CreativePlan(SHOP,CAMPAIGN,DAY)
  assert.equal(result.plan_id,PLAN)
  assert.equal(calls.length,3)
  const q=new URL(calls[0].url).searchParams
  assert.equal(q.get('shop_id'),'eq.'+SHOP)
  assert.equal(q.get('status'),'eq.DRAFT')
  assert.equal(new URL(calls[1].url).searchParams.get('review_status'),'eq.DRAFT')
  const req=calls[2]
  assert.equal(req.url,'https://retailgrowth-function.example.com/api/campaigns/'+CAMPAIGN+'/feature4-plans')
  assert.equal(req.options.method,'POST')
  assert.deepEqual(JSON.parse(req.options.body),{day_id:DAY})
  assert.equal(req.options.headers.Authorization,'Bearer jwt-actor')
  assert.doesNotMatch(JSON.stringify(req),/service_role|sb_secret_|\/render-jobs\//)
})

test('foreign private source query and malformed campaign IDs stop before any POST',async()=>{
  let count=0
  const api=fixture(async(url)=>{
    if(url.includes('/auth/v1/token'))return json({
      access_token:'jwt-actor',refresh_token:'refresh-f4',expires_in:3600})
    count++
    if(url.includes('/rest/v1/campaigns'))return json([{id:CAMPAIGN,shop_id:SHOP,status:'DRAFT'}])
    if(url.includes('/rest/v1/campaign_days'))return json([{
      id:DAY,shop_id:'99999999-9999-4999-8999-999999999999',
      campaign_id:CAMPAIGN,review_status:'DRAFT',day_index:1,instagram:{}}])
    throw Error('Unexpected issue/network call')
  })
  await api.signIn('a@example.invalid','password123')
  await assert.rejects(()=>api.listFeature4SourceDays(SHOP),/Untrusted saved video/)
  assert.equal(count,2)
  await assert.rejects(()=>api.issueFeature4CreativePlan(SHOP,CAMPAIGN,'forged'),/Verified saved campaign/)
  assert.equal(count,2)
})

test('uncertain issue POST is not retried and cannot be promoted to an approved plan',async()=>{
  let posts=0
  const api=fixture(async(url)=>{
    if(url.includes('/auth/v1/token'))return json({
      access_token:'jwt-actor',refresh_token:'refresh-f4',expires_in:3600})
    if(url.includes('/api/campaigns/')) { posts++;return json({error:'temporary'},503)}
    throw Error('Unexpected endpoint')
  })
  await api.signIn('a@example.invalid','password123')
  await assert.rejects(()=>api.issueFeature4CreativePlan(SHOP,CAMPAIGN,DAY),/not confirmed/)
  assert.equal(posts,1)
})

test('invalid HTTPS endpoint never sends JWT/creative user data',async()=>{
  let calls=0
  const api=fixture(async(url)=>{
    if(url.includes('/auth/v1/token'))return json({
      access_token:'jwt-actor',refresh_token:'refresh-f4',expires_in:3600})
    calls++;throw Error('Unsafe remote')
  },'http://bad.example.com')
  await api.signIn('a@example.invalid','password123')
  await assert.rejects(()=>api.issueFeature4CreativePlan(SHOP,CAMPAIGN,DAY),/backend not configured/)
  assert.equal(calls,0)
})
