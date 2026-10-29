import test from 'node:test'
import assert from 'node:assert/strict'
import {createTraceStore} from '../../frontend/src/features/testing/trace-store.mjs'
const shop='11111111-1111-4111-8111-111111111111'
const other='22222222-2222-4222-8222-222222222222'
const job='33333333-3333-4333-8333-333333333333'
const row={id:'44444444-4444-4444-8444-444444444444',shop_id:shop,job_id:job,
  feature:'F4',operation:'render.complete',status:'SUCCEEDED',
  attempt:1,elapsed_ms:8200,metadata:{codec:'h264/aac',video_width:1080,video_height:1920,
    duration_seconds:30}}
function newStore(response) {
 const calls=[]
 const store=createTraceStore({supabaseUrl:'https://project.supabase.co',
  publishableKey:'public-publishable',tokenProvider:async()=> 'scoped-user-jwt',
  fetchImpl:async (url,opts)=>{
    calls.push({url,opts})
    return {ok:response.status===200,status:response.status,
      json:async()=>response.body}
  }})
 return {store,calls}
}
test('trusted worker table is queried read-only with signed user token',async()=>{
 const {store,calls}=newStore({status:200,body:[row]})
 assert.deepEqual(await store.listWorkerSpans(shop,[job]),[row])
 assert.equal(calls[0].opts.method,'GET')
 assert.equal(calls[0].opts.headers.Authorization,'Bearer scoped-user-jwt')
 assert.equal(calls[0].opts.headers.apikey,'public-publishable')
 assert.ok(calls[0].url.includes('/rest/v1/feature_test_worker_spans'))
 assert.ok(calls[0].url.includes('shop_id=eq.'))
 assert.ok(calls[0].url.includes('job_id=in.'))
 assert.ok(!JSON.stringify(calls).includes('service_role'))
})
test('cross-shop and unrelated job records are never shown',async()=>{
 for(const bad of [{...row,shop_id:other},{...row,job_id:other},
  {...row,feature:'F5'},{...row,attempt:0}]) {
   const {store}=newStore({status:200,body:[bad]})
   await assert.rejects(()=>store.listWorkerSpans(shop,[job]),/tenant\/job mismatch/)
 }
})
test('no schema or unauthorized access is not a synthetic worker failure',async()=>{
 const {store}=newStore({status:404,body:{error:'not installed'}})
 await assert.rejects(()=>store.listWorkerSpans(shop,[job]),/not deployed/)
})
test('invalid reference, duplicate or excessive unscoped requests are rejected before network',async()=>{
 const {store,calls}=newStore({status:200,body:[]})
 for(const ids of [[],[job,job],[other,'invalid'],
   Array.from({length:6},(_,i)=>'55555555-5555-4555-8555-'+String(i).padStart(12,'0'))]) {
   await assert.rejects(()=>store.listWorkerSpans(shop,ids))
 }
 assert.equal(calls.length,0)
})
