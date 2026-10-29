import test from 'node:test'
import assert from 'node:assert/strict'
import {collectHttpReceipt} from '../../frontend/src/lib/feature-http-receipt.mjs'
import {createCampaignApi} from '../../frontend/src/features/campaigns/campaign-api.mjs'
import {createTrendApi} from '../../frontend/src/features/trends/trend-api.mjs'
const shop='11111111-1111-4111-8111-111111111111'
const campaign='22222222-2222-4222-8222-222222222222'
const id='1234567890abcdef1234567890abcdef'
const response=(status,body,trace=id)=>({ok:status>=200&&status<300,status,
  headers:{get:k=>k.toLowerCase()==='x-request-id'?trace:null},
  json:async()=>body})
test('only safe fixed HTTP observation fields leave receipt collector',()=>{
 const events=[]
 collectHttpReceipt(x=>events.push(x),{source:'campaign',method:'POST',
   path:'/campaigns/'+campaign+'/renders',
   response:response(202,{authorization:'Bearer secret',url:'https://private.invalid'},id),
   startedAt:Date.now()-8})
 assert.equal(events.length,1)
 assert.equal(events[0].request_id,id)
 assert.equal(events[0].operation,'/campaigns/:id/renders')
 assert.equal(events[0].handler_marker_seen,true)
 assert.equal(events[0].status_code,202)
 const serialized=JSON.stringify(events)
 for(const value of [campaign,'Bearer','secret','private.invalid'])assert.ok(!serialized.includes(value))
})
test('invalid marker is recorded as absent and callback errors cannot break API caller',()=>{
 const events=[]
 collectHttpReceipt(x=>events.push(x),{source:'campaign',method:'GET',path:'/render-jobs/'+campaign,
   response:response(503,{error:'GATEWAY'},'not-an-app-marker'),startedAt:Date.now()})
 assert.equal(events[0].request_id,null)
 assert.equal(events[0].handler_marker_seen,false)
 assert.doesNotThrow(()=>collectHttpReceipt(()=>{throw new Error('UI crashed')},{
  source:'trend',method:'GET',path:'/shops/'+shop+'/trend-recommendations',
  response:response(200,{},id),startedAt:Date.now()}))
})
test('campaign client records real handler marker but never tokens or body',async()=>{
 const captured=[]
 const api=createCampaignApi({baseUrl:'https://api.example.invalid',
   tokenProvider:async()=> 'secret-bearer-value',
   onResponse:r=>captured.push(r),
   fetchImpl:async()=>response(202,{campaign_id:campaign,status:'PLANNING'},id)})
 const data=await api.createCampaign({shop_id:shop,brief:'Test some ideas'})
 assert.equal(data.campaign_id,campaign)
 assert.equal(captured.length,1)
 assert.equal(captured[0].operation,'/campaigns')
 assert.equal(captured[0].method,'POST')
 assert.ok(!JSON.stringify(captured).includes('secret'))
})
test('trend client observes private shop-scoped output and redacts UUID',async()=>{
 const captured=[]
 const api=createTrendApi({baseUrl:'https://api.example.invalid',
   tokenProvider:async()=> 'token',
   onResponse:r=>captured.push(r),
   fetchImpl:async()=>response(200,{shop_id:shop,improved_prompt:'Clearer copy'},id)})
 await api.improvePrompt(shop,'Write some clothing ideas', ['instagram_caption'])
 assert.equal(captured[0].operation,'/shops/:id/improve-prompt')
 assert.equal(captured[0].request_id,id)
 assert.ok(!JSON.stringify(captured).includes(shop))
})
test('GET retry records separate response attempts; mutations never retry',async()=>{
 let count=0
 const captured=[]
 const api=createCampaignApi({baseUrl:'https://api.example.invalid',
   tokenProvider:async()=> 'test-user-jwt',
   onResponse:r=>captured.push(r),
   fetchImpl:async()=>{count++;return count===1?response(503,{error:'TEMP'},null)
     :response(200,{id:campaign,shop_id:shop,status:'DRAFT'},id)}})
 await api.getCampaign(campaign)
 assert.equal(count,2)
 assert.deepEqual(captured.map(x=>x.attempt),[1,2])
 assert.deepEqual(captured.map(x=>x.handler_marker_seen),[false,true])
})
