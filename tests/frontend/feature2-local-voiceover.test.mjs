import test from 'node:test'
import assert from 'node:assert/strict'
import {F2_LOCAL_VOICES, makeLocalVoiceAction} from '../../frontend/src/features/voiceover/voiceover-model.mjs'
const SHOP='11111111-1111-4111-8111-111111111111'
const CID='22222222-2222-4222-8222-222222222222'
const UUID='33333333-3333-4333-8333-333333333333'
const source={shopId:SHOP,campaignId:CID,planSha256:'a'.repeat(64),
 idempotencyKey:UUID,voiceId:'af_heart',lang:'en-us',speed:'normal',preview:false}
test('actual Kokoro ONNX v1 English voices only, no false Hindi Marathi',()=>{
 assert.equal(F2_LOCAL_VOICES.length,8)
 assert.deepEqual(new Set(F2_LOCAL_VOICES.map(x=>x.locale)),new Set(['en-us','en-gb']))
})
test('local voice source action is free only with operator validation pending',()=>{
 const packet=makeLocalVoiceAction(source)
 assert.equal(packet.estimated_paid_cost_usd,0)
 assert.equal(packet.provider,'kokoro-onnx')
 assert.equal(packet.needs_current_server_signed_grants,true)
 assert.equal(packet.may_auto_invoke_azure,false)
})
test('cross-language, forged voice, invalid speed and weak tenant denied',()=>{
 for(const changes of [{lang:'hi-in'},{lang:'mr-in'},
   {voiceId:'hi-IN-SwaraNeural'},{speed:'2.0'},
   {shopId:CID.replaceAll('2','z')}])
    assert.throws(()=>makeLocalVoiceAction({...source,...changes}))
})


import {makeReviewedDraftRequest,verifyReviewedDraftReceipt} from
 '../../frontend/src/features/voiceover/voiceover-model.mjs'
const PROPOSAL='44444444-4444-4444-8444-444444444444'
const REVIEW='55555555-5555-4555-8555-555555555555'
const SHA='a'.repeat(64)
const draftProposal=Object.freeze({
 shop_id:SHOP,campaign_id:CID,creative_plan_sha256:SHA,
 proposal_id:PROPOSAL,source_revision:7,
 original_prompt_sha256:'b'.repeat(64),improved_prompt_sha256:'c'.repeat(64),
 review_status:'NEEDS_REVIEW',can_publish:false,private:true
})
function request(overrides={}){
 return makeReviewedDraftRequest({
   shopId:SHOP,campaignId:CID,planSha256:SHA,proposal:draftProposal,
   reviewEventId:REVIEW,idempotencyKey:UUID,
   explicitComparisonAcknowledged:true,...overrides
 })
}
test('A/B source request can only ask backend to check signed review and CAS',()=>{
 const result=request()
 assert.equal(result.schema,'retailgrowth.feature2-reviewed-draft-request.v1')
 assert.equal(result.source_revision,7)
 assert.equal(result.requires_independently_signed_human_review,true)
 assert.equal(result.requires_backend_compare_and_swap,true)
 assert.equal(result.allow_publish,false)
 assert.equal(result.allow_paid_motion,false)
 assert.ok(Object.isFrozen(result))
})
test('A/B browser checkbox alone, foreign/shop-stale plan never authorizes',()=>{
 for(const overrides of [
  {explicitComparisonAcknowledged:false},{shopId:CID},
  {planSha256:'0'.repeat(64)},{proposal:{...draftProposal,private:false}},
  {proposal:{...draftProposal,can_publish:true}},
  {proposal:{...draftProposal,source_revision:3.5}},
  {proposal:{...draftProposal,creative_plan_sha256:'f'.repeat(64)}},
  {proposal:{...draftProposal,review_status:'APPROVED'}},
  {reviewEventId:'not-a-uuid'}
 ]) assert.throws(()=>request(overrides))
})
test('private reviewed draft response is still never publishing approval',()=>{
 const reply={schema:'retailgrowth.feature2-reviewed-prompt-draft.v1',
   shop_id:SHOP,campaign_id:CID,revision:8,
   proposal_id:PROPOSAL,source_revision:7,
   original_prompt_sha256:'b'.repeat(64),
   improved_prompt_sha256:'c'.repeat(64),review_status:'DRAFT',
   private:true,can_publish:false,can_dispatch_paid_motion:false,
   requires_fresh_media_rights:true,requires_new_copy_fact_review:true}
 const output=verifyReviewedDraftReceipt({
    shopId:SHOP,campaignId:CID,proposal:draftProposal,receipt:reply})
 assert.equal(output.revision,8)
 assert.equal(output.can_publish,false)
 for(const change of [
  {revision:9},{private:false},{can_publish:true},
  {proposal_id:REVIEW},{source_revision:6},
  {original_prompt_sha256:'f'.repeat(64)},
  {can_dispatch_paid_motion:true},{improved_prompt_sha256:'d'.repeat(64)},
  {review_status:'PUBLISHED'},{requires_fresh_media_rights:false}
 ]) assert.throws(()=>verifyReviewedDraftReceipt({
   shopId:SHOP,campaignId:CID,proposal:draftProposal,receipt:{...reply,...change}}))
})


import {makeLocalSentenceRetakeAction,verifyLocalSentenceRetakeReceipt} from
 '../../frontend/src/features/voiceover/voiceover-model.mjs'
function retake(overrides={}){
  return makeLocalSentenceRetakeAction({
    shopId:SHOP,campaignId:CID,planSha256:SHA,
    originalAudioSha256:'d'.repeat(64),sentenceIndex:1,
    jobKey:UUID,voiceId:'af_heart',lang:'en-us',speed:'normal',
    ...overrides,
  })
}
test('retake is one bounded original-audio proposal, never auto-merge or paid',()=>{
 const action=retake()
 assert.equal(action.sentence_index,1)
 assert.equal(action.requires_current_editor_and_dictionary,true)
 assert.equal(action.requires_one_durable_local_retake,true)
 assert.equal(action.auto_azure_fallback,false)
 assert.equal(action.can_publish,false)
 assert.ok(Object.isFrozen(action))
})
test('retake denies foreign voice, invalid scene and forged original SHA',()=>{
 for(const change of [
  {shopId:'invalid-foreign-id'},{campaignId:'not-a-uuid'},
  {originalAudioSha256:'not-a-sha'},
  {sentenceIndex:13},{sentenceIndex:-1},
  {sentenceIndex:0.2},{lang:'hi-IN'},
  {voiceId:'hi-IN-SwaraNeural'},
  {voiceId:'bm_george',lang:'en-us'},
  {jobKey:'bad-key'}
 ]) assert.throws(()=>retake(change))
})
test('retake receipt never certifies pronunciation or publishing',()=>{
 const action=retake()
 const receipt={
  schema:'retailgrowth.feature2-sentence-retake.v1',
  shop_id:SHOP,campaign_id:CID,creative_plan_sha256:SHA,
  prior_audio_sha256:'d'.repeat(64),
  sentence_index:1,new_audio_sha256:'e'.repeat(64),
  private_sentence_audio_asset_id:'44444444-4444-4444-8444-444444444444',
  review_status:'PENDING_NEW_STT_AND_HUMAN_LISTEN',private:true,
  can_publish:false,requires_feature4_scene_assembly:true,
  requires_new_feature7_transcription:true,
  actual_pronunciation_success_verified:false,azure_fallback_used:false
 }
 const good=verifyLocalSentenceRetakeReceipt({request:action,receipt})
 assert.equal(good.can_publish,false)
 assert.equal(good.requires_new_feature7_transcription,true)
 for(const change of [
  {shop_id:CID},{prior_audio_sha256:'f'.repeat(64)},
  {sentence_index:3},{review_status:'APPROVED'},
  {private:false},{can_publish:true},{azure_fallback_used:true},
  {actual_pronunciation_success_verified:true},
  {requires_feature4_scene_assembly:false}
 ]) assert.throws(()=>verifyLocalSentenceRetakeReceipt({
   request:action,receipt:{...receipt,...change}}))
})


import {
 makePrivateVoiceJobStatusRequest,verifyPrivateVoiceJobStatus
} from '../../frontend/src/features/voiceover/voiceover-model.mjs'

function privateQuery(overrides={}){
 return makePrivateVoiceJobStatusRequest({
   shopId:SHOP,campaignId:CID,planSha256:SHA,requestKey:UUID,...overrides})
}
function privateJob(status='RESERVED',overrides={}){
 const complete=status==='AWAITING_HUMAN_REVIEW'
 return {
  schema:'retailgrowth.feature2-private-voice-job-status.v1',
  shop_id:SHOP,campaign_id:CID,creative_plan_sha256:SHA,
  request_key:UUID,provider:'kokoro-onnx',status,
  private:true,can_publish:false,automatically_retried:false,
  azure_fallback_used:false,paid_api_calls:0,
  terminal:['AWAITING_HUMAN_REVIEW','FAILED','DENIED','BLOCKED'].includes(status),
  original_audio_sha256:complete?'c'.repeat(64):null,
  audio_asset_id:complete?PROPOSAL:null,
  review_status:complete?'PENDING_HUMAN_LISTEN_AND_RIGHTS':'NOT_READY',
  ...overrides,
 }
}
function status(s='RESERVED',overrides={}){
 return verifyPrivateVoiceJobStatus({
  shopId:SHOP,campaignId:CID,planSha256:SHA,requestKey:UUID,
  status:privateJob(s,overrides)})
}
test('uncertain local TTS may only query existing current request key read-only',()=>{
 const q=privateQuery()
 assert.equal(q.read_only,true)
 assert.equal(q.can_reissue_job,false)
 assert.equal(q.request_key,UUID)
 assert.equal(q.provider,'kokoro-onnx')
 assert.ok(Object.isFrozen(q))
 for(const change of [
  {shopId:'not-uuid'}, {campaignId:'not-uuid'},
  {requestKey:'new-random-key'},{planSha256:'fake'},
  {provider:'azure-speech'}
 ])assert.throws(()=>privateQuery(change))
})
test('private narration job status cannot imply a real model, rights or publish',()=>{
 for(const state of ['RESERVED','RUNNING','FAILED','BLOCKED','DENIED',
                       'AWAITING_HUMAN_REVIEW']){
  const r=status(state)
  assert.equal(r.state,state)
  assert.equal(r.terminal,!['RUNNING','RESERVED'].includes(state))
  assert.equal(r.can_publish,false)
  assert.equal(r.can_reissue_job,false)
  assert.equal(r.human_review_required,true)
  assert.equal(r.existing_private_audio,state==='AWAITING_HUMAN_REVIEW')
  assert.ok(Object.isFrozen(r))
 }
})
test('reject foreign, replayed, paid-fallback or fabricated voice job success',()=>{
 for(const changed of [
  {shop_id:CID},{campaign_id:SHOP},
  {creative_plan_sha256:'f'.repeat(64)},
  {request_key:REVIEW},{provider:'azure-speech'},
  {status:'PUBLISHED'},{status:'SUCCEEDED'},
  {can_publish:true},{automatically_retried:true},
  {azure_fallback_used:true},{paid_api_calls:1},
  {private:false},{terminal:true},{review_status:'APPROVED'},
  {original_audio_sha256:'e'.repeat(64)},
  {audio_asset_id:PROPOSAL},
 ]){
  assert.throws(()=>status('RESERVED',changed),undefined,JSON.stringify(changed))
 }
 for(const changed of [
  {original_audio_sha256:null},{audio_asset_id:null},{terminal:false},
  {review_status:'NOT_READY'}
 ]){
  assert.throws(()=>status('AWAITING_HUMAN_REVIEW',changed),
    undefined,JSON.stringify(changed))
 }
})


// feature2 F2-31 review-only UI receipt: a signed backend still owns durable
// review verification; the browser must deny forged optional grants on sight.
const f2ReviewDraftReply={
 schema:'retailgrowth.feature2-reviewed-prompt-draft.v1',
 shop_id:SHOP,campaign_id:CID,proposal_id:PROPOSAL,
 source_revision:7,revision:8,
 original_prompt_sha256:'b'.repeat(64),
 improved_prompt_sha256:'c'.repeat(64),
 review_status:'DRAFT',private:true,can_publish:false,
 can_dispatch_paid_motion:false,
 requires_fresh_media_rights:true,
 requires_new_copy_fact_review:true,
}
const suspiciousReviewFields=[
 {approved_to_publish:true},{approved_to_publish:'false'},
 {commercial_use_approved:null},{commercial_use_approved:1},
 {offer_facts_verified:true},{media_rights_verified:'no'},
 {paid_inference_authorized:0},{may_auto_invoke_azure:true},
 {provider_call_made:true},{paid_calls:false},
 {paid_calls:1},{paid_calls:'0'},
 {billing:'PAID'},
 {signed_url:'https://example.invalid/audio'},
 {private_download_url:'https://example.invalid/draft'},
]
test('F2-31 rejects forged optional grants in signed draft source preview',()=>{
 for(const wrong of suspiciousReviewFields){
   assert.throws(()=>request({proposal:{...draftProposal,...wrong}}),
     undefined,JSON.stringify(wrong))
 }
})
test('F2-31 rejects forged optional grants in reviewed draft receipt',()=>{
 for(const wrong of suspiciousReviewFields){
   assert.throws(()=>verifyReviewedDraftReceipt({
     shopId:SHOP,campaignId:CID,proposal:draftProposal,
     receipt:{...f2ReviewDraftReply,...wrong},
   }),undefined,JSON.stringify(wrong))
 }
})
test('F2-31 pending optional denial metadata remains only a private draft',()=>{
 const safe={
  approved_to_publish:false,
  commercial_use_approved:false,
  offer_facts_verified:false,
  media_rights_verified:false,
  paid_inference_authorized:false,
  may_auto_invoke_azure:false,
  provider_call_made:false,
  paid_calls:0,billing:'NONE',signed_url:null,private_download_url:null,
 }
 const proposed=request({proposal:{...draftProposal,...safe}})
 assert.equal(proposed.allow_publish,false)
 assert.equal(proposed.requires_independently_signed_human_review,true)
 const returned=verifyReviewedDraftReceipt({
   shopId:SHOP,campaignId:CID,proposal:draftProposal,
   receipt:{...f2ReviewDraftReply,...safe},
 })
 assert.equal(returned.can_publish,false)
 assert.equal(returned.review_status,'DRAFT')
 assert.ok(Object.isFrozen(returned))
})
