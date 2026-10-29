import test from 'node:test'
import assert from 'node:assert/strict'
import {verifyPrivateVoiceQualityReview} from '../../frontend/src/features/voiceover/voiceover-quality-review.mjs'
const shopId='11111111-1111-4111-8111-111111111111'
const campaignId='22222222-2222-4222-8222-222222222222'
const planSha256='a'.repeat(64)
const audioSha='b'.repeat(64)
const receipt={
  shop_id:shopId,campaign_id:campaignId,creative_plan_sha256:planSha256,
  private_audio_asset_id:'33333333-3333-4333-8333-333333333333',
  original_audio_sha256:audioSha,duration_seconds:2,
  provider:'kokoro-onnx',private:true,can_publish:false
}
function review(){
 return {
  schema:'retailgrowth.feature2-verified-audio-qa.v1',
  shop_id:shopId,campaign_id:campaignId,creative_plan_sha256:planSha256,
  audio_asset_id:receipt.private_audio_asset_id,original_audio_sha256:audioSha,
  audio_duration_seconds:2,
  source_rechecked:true,review_state:'PENDING_HUMAN_LISTEN_AND_RIGHTS',
  can_publish:false,approved_for_editing:false,pronunciation_verified:false,
  asr_word_confidence_available:false,asr_transcript_matched_script:false,
  asr_word_timing:[
   {word:'सुंदर',startMs:100,endMs:500},
   {word:'kurti',startMs:550,endMs:900}],
  pcm_quality_warnings:['too_quiet'],
  asr_issues:[{problem:'MISSING_OR_SUBSTITUTED_WORD',
   word:'कुर्ती',audio_start_seconds:0.55,confidence:null,
   manual_review_required:true}],
 }
}
test('actual signed F7 source review shape remains human only',()=>{
 const out=verifyPrivateVoiceQualityReview({shopId,campaignId,planSha256,receipt,review:review()})
 assert.equal(out.asr_matched_script,false)
 assert.equal(out.issues[0].word,'कुर्ती')
 assert.equal(out.issues[0].at_seconds,0.55)
 assert.equal(out.words.length,2)
 assert.equal(out.words[1].start_seconds,0.55)
 assert.deepEqual(out.pcm_warnings,['too_quiet'])
 assert.equal(out.confidence_available,false)
 assert.equal(out.pronunciation_verified,false)
 assert.equal(out.human_listening_required,true)
 assert.equal(out.can_publish,false)
 assert.equal(out.edit_approved,false)
 assert.ok(Object.isFrozen(out))
})
test('clean text/PCM cannot auto-approve spoken language',()=>{
 const clean=review()
 clean.asr_issues=[]
 clean.pcm_quality_warnings=[]
 clean.asr_transcript_matched_script=true
 const out=verifyPrivateVoiceQualityReview({shopId,campaignId,planSha256,receipt,review:clean})
 assert.deepEqual(out.issues,[])
 assert.equal(out.asr_matched_script,true)
 assert.equal(out.edit_approved,false)
 assert.equal(out.pronunciation_verified,false)
})
test('real F7 substitution code remains visible only as a review hint',()=>{
 const changed=review()
 changed.asr_issues=[{problem:'UNEXPECTED_OR_SUBSTITUTED_WORD',
  word:'kurti',audio_start_seconds:0.55,confidence:null}]
 const out=verifyPrivateVoiceQualityReview({shopId,campaignId,planSha256,receipt,review:changed})
 assert.equal(out.issues[0].problem,'UNEXPECTED_OR_SUBSTITUTED_WORD')
})
test('never trust foreign, stale, published or invented confidence',()=>{
 for(const [field,value] of [
  ['shop_id',campaignId],['campaign_id',shopId],['original_audio_sha256','f'.repeat(64)],
  ['creative_plan_sha256','e'.repeat(64)],['audio_asset_id',shopId],
  ['review_state','APPROVED_FOR_EDITING'],['can_publish',true],
  ['approved_for_editing',true],['pronunciation_verified',true],
  ['asr_word_confidence_available',true],['source_rechecked',false],
  ['audio_duration_seconds',9]
 ]){
  const altered={...review(),[field]:value}
  assert.throws(()=>verifyPrivateVoiceQualityReview({
    shopId,campaignId,planSha256,receipt,review:altered}),undefined,field)
 }
 const altered=review()
 altered.asr_issues[0].confidence=0.99
 assert.throws(()=>verifyPrivateVoiceQualityReview({shopId,campaignId,planSha256,receipt,review:altered}))
})
test('reject timestamps out of audio bounds and arbitrary data problems',()=>{
 for(const changed of [
  [{word:'new',startMs:50,endMs:90}, {word:'oops',startMs:60,endMs:900}],
  [{word:'new',startMs:50,endMs:2300}],
  [{word:'<script>',startMs:20,endMs:300}]
 ]){
  const altered=review()
  altered.asr_word_timing=changed
  assert.throws(()=>verifyPrivateVoiceQualityReview({shopId,campaignId,planSha256,receipt,review:altered}))
 }
 const altered=review();altered.asr_issues[0].problem='GO_AHEAD_AND_PUBLISH'
 assert.throws(()=>verifyPrivateVoiceQualityReview({shopId,campaignId,planSha256,receipt,review:altered}))
})
