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
   improved_prompt_sha256:'c'.repeat(64),review_status:'DRAFT',
   private:true,can_publish:false,can_dispatch_paid_motion:false,
   requires_fresh_media_rights:true,requires_new_copy_fact_review:true}
 const output=verifyReviewedDraftReceipt({
    shopId:SHOP,campaignId:CID,proposal:draftProposal,receipt:reply})
 assert.equal(output.revision,8)
 assert.equal(output.can_publish,false)
 for(const change of [
  {revision:9},{private:false},{can_publish:true},
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
  {shopId:CID},{originalAudioSha256:'not-a-sha'},
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
