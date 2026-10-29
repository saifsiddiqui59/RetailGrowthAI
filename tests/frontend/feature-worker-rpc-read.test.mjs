import test from 'node:test'
import assert from 'node:assert/strict'
import {createTraceStore} from '../../frontend/src/features/testing/trace-store.mjs'
const shop='11111111-1111-4111-8111-111111111111'
const foreign='22222222-2222-4222-8222-222222222222'
const job='33333333-3333-4333-8333-333333333333'
const row={id:'44444444-4444-4444-8444-444444444444',
  shop_id:shop,job_id:job,feature:'F4',operation:'render.complete',
  status:'SUCCEEDED',attempt:1,elapsed_ms:8200,
  metadata:{codec:'h264/aac',video_width:1080,video_height:1920,duration_seconds:30}}
function setup(response) {
 const calls=[]
 const store=createTraceStore({
  supabaseUrl:'https://test.supabase.co',publishableKey:'sb_publishable_demo',
  tokenProvider:async()=> 'actual-user-JWT',
  fetchImpl:async (url,init)=>{calls.push({url,init});return {
    ok:response.ok??true,status:response.status??200,
    json:async()=>response.body
  }},
 })
 return {calls,store}
}
const body={shop_id:shop,job_id:job,source:'trusted_backend_persisted',events:[row]}
test('signed private worker RPC returns service-authored rows; no direct table read',async()=>{
 const {store,calls}=setup({body})
 assert.deepEqual(await store.listWorkerSpans(shop,[job]),[row])
 assert.equal(calls.length,1)
 assert.ok(calls[0].url.includes('/rest/v1/rpc/retail_feature_worker_spans'))
 assert.ok(!calls[0].url.includes('/feature_test_worker_spans'))
 assert.equal(calls[0].init.method,'POST')
 assert.equal(calls[0].init.headers.Authorization,'Bearer actual-user-JWT')
 assert.equal(calls[0].init.headers.apikey,'sb_publishable_demo')
 assert.deepEqual(JSON.parse(calls[0].init.body),{
   p_shop_id:shop,p_job_id:job,p_limit:10
 })
 assert.ok(!JSON.stringify(calls).includes('service_role'))
})
test('unexpected shop, job, source and nontrustworthy feature are rejected',async()=>{
 for(const bad of [
  {...body,shop_id:foreign},{...body,job_id:foreign},
  {...body,source:'browser_observed'},
  {...body,events:[{...row,shop_id:foreign}]},
  {...body,events:[{...row,job_id:foreign}]},
  {...body,events:[{...row,feature:'F5'}]},
  {...body,events:[{...row,attempt:0}]},
  {...body,events:[{...row,status:'UNKNOWN'}]},
 ]) {
  const {store}=setup({body:bad})
  await assert.rejects(()=>store.listWorkerSpans(shop,[job]),/inconsistent tenant or source/)
 }
})
test('missing RPC is not presented as worker failure',async()=>{
 const {store}=setup({status:404,ok:false,body:{message:'not yet released'}})
 await assert.rejects(()=>store.listWorkerSpans(shop,[job]),/not deployed/)
})
test('invalid or excessive job IDs cannot trigger API',async()=>{
 const {store,calls}=setup({body})
 for(const refs of [[],[job,job],['bad-id'],Array.from({length:6},(_,i)=>
   '55555555-5555-4555-8555-'+String(i).padStart(12,'0'))]) {
  await assert.rejects(()=>store.listWorkerSpans(shop,refs))
 }
 assert.equal(calls.length,0)
})
test('private backend RPC never retries an uncertain read transport POST',async()=>{
 let count=0
 const store=createTraceStore({
   supabaseUrl:'https://test.supabase.co',publishableKey:'publishable',
   tokenProvider:async()=> 'token',
   fetchImpl:async()=>{count++;throw new Error('network gateway 503')},
 })
 await assert.rejects(()=>store.listWorkerSpans(shop,[job]),/network gateway/)
 assert.equal(count,1)
})
