import test from 'node:test'
import assert from 'node:assert/strict'
import {verifyPrivateFeature2Trace,verifyCurrentPrivateTraceRead} from '../../frontend/src/features/voiceover/voiceover-trace-model.mjs'
const shopId='11111111-1111-4111-8111-111111111111'
const campaignId='22222222-2222-4222-8222-222222222222'
const workflowId='33333333-3333-4333-8333-333333333333'
const sourceSha256='a'.repeat(64)
function fixture(){
 return {schema:'retailgrowth.feature2-private-trace-history.v1',
   shop_id:shopId,campaign_id:campaignId,workflow_id:workflowId,
   source_sha256:sourceSha256,private:true,all_steps_verified:true,
   actual_model_inference_verified:false,can_publish:false,
   last_event_sha256:'c'.repeat(64),
   events:[
     {sequence:1,stage:'TREND',status:'SUCCEEDED',
      evidence_class:'SOURCE_ONLY',failure_code:null,
      event_sha256:'b'.repeat(64),can_publish:false},
     {sequence:2,stage:'KOKORO_TTS',status:'BLOCKED',
      evidence_class:'SYNTHETIC_TEST_ONLY',failure_code:'MODEL_UNAVAILABLE',
      event_sha256:'c'.repeat(64),can_publish:false}]
 }
}
function check(receipt=fixture(),overrides={}){
 return verifyPrivateFeature2Trace({
   shopId,campaignId,workflowId,sourceSha256,receipt,...overrides})
}
test('trusted private trace is shown as source-only, not model completion',()=>{
 const result=check()
 assert.equal(result.status,'PRIVATE_BACKEND_STATUS_ONLY')
 assert.deepEqual(result.steps.map(x=>x.stage),['TREND','KOKORO_TTS'])
 assert.deepEqual(result.steps.map(x=>x.status),['SUCCEEDED','BLOCKED'])
 assert.equal(result.steps[1].failure_code,'MODEL_UNAVAILABLE')
 assert.equal(result.all_model_inference_verified,false)
 assert.equal(result.human_approval_verified,false)
 assert.equal(result.source_only_or_synthetic,true)
 assert.equal(result.can_publish,false)
 assert.ok(Object.isFrozen(result))
 assert.ok(Object.isFrozen(result.steps))
 assert.ok(result.steps.every(x=>Object.isFrozen(x)))
 assert.equal(JSON.stringify(result).includes('server_mac'),false)
})
test('foreign shop, changed source SHA or fabricated publish proof is rejected',()=>{
 for(const [field,v] of [
  ['shop_id',campaignId],['campaign_id',shopId],
  ['workflow_id',campaignId],['source_sha256','d'.repeat(64)],
  ['private',false],['all_steps_verified',false],
  ['actual_model_inference_verified',true],['can_publish',true],
  ['last_event_sha256','e'.repeat(64)]
 ])assert.throws(()=>check({...fixture(),[field]:v}),undefined,field)
})
test('chain gaps, swapped order and forged status/evidence are not displayed',()=>{
 for(const changed of [
   {sequence:3},{event_sha256:'not-a-hash'},
   {can_publish:true},{status:'PUBLISHED'},
   {stage:'SEND_REAL_SOCIAL_POST'},
   {evidence_class:'REAL_UNVERIFIED'},
   {failure_code:null},{failure_code:'ALLOW_PRODUCTION'}
 ]){
   const source=fixture()
   source.events[1]={...source.events[1],...changed}
   assert.throws(()=>check(source),undefined,JSON.stringify(changed))
 }
 const withRaw=fixture()
 withRaw.events[0]={...withRaw.events[0],raw_jwt:'unsafe'}
 assert.throws(()=>check(withRaw))
})
test('client refuses a trace request with stale selected workflow',()=>{
 assert.throws(()=>check(fixture(),{workflowId:campaignId}))
 assert.throws(()=>check(fixture(),{shopId:'invalid'}))
 const source=fixture()
 source.events=[]
 assert.throws(()=>check(source))
})


// This is a deterministic React scope-identity contract: the JSX panel
// compares the request's scope against the latest ref before state updates.
// It is NOT proof of a real authenticated UI session or hosted JWT/RLS.
test('private trace request cannot return success after shop or workflow switch',()=>{
 const fetcher=()=>Promise.resolve(fixture())
 const original=Object.freeze({shopId,campaignId,workflowId,sourceSha256,
   enabled:true,onFetchPrivateTrace:fetcher})
 const out=verifyCurrentPrivateTraceRead({
   currentScope:original,requestScope:original,receipt:fixture()})
 assert.equal(out.status,'PRIVATE_BACKEND_STATUS_ONLY')
 const changes=[
   {shopId:campaignId},{campaignId:shopId},{workflowId:campaignId},
   {sourceSha256:'d'.repeat(64)},{enabled:false},
   {onFetchPrivateTrace:()=>Promise.resolve(fixture())},
 ]
 for(const changed of changes){
   const next=Object.freeze({...original,...changed})
   assert.throws(()=>verifyCurrentPrivateTraceRead({
     currentScope:next,requestScope:original,receipt:fixture()}),
     undefined,JSON.stringify(Object.keys(changed)))
 }
})

test('disabled trace reader is never a valid authorization source',()=>{
 const scope={shopId,campaignId,workflowId,sourceSha256,
   enabled:false,onFetchPrivateTrace:()=>fixture()}
 assert.throws(()=>verifyCurrentPrivateTraceRead({
   currentScope:scope,requestScope:scope,receipt:fixture()}))
 const noReader={...scope,enabled:true,onFetchPrivateTrace:null}
 assert.throws(()=>verifyCurrentPrivateTraceRead({
   currentScope:noReader,requestScope:noReader,receipt:fixture()}))
 const active={...scope,enabled:true}
 assert.throws(()=>verifyCurrentPrivateTraceRead({
   currentScope:active,requestScope:active,
   receipt:{...fixture(),source_sha256:'b'.repeat(64)}}))
})
