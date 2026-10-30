import test from 'node:test'
import assert from 'node:assert/strict'
import {verifyPrivateVoiceQualityReview,verifySignedWordErrorReview} from '../../frontend/src/features/voiceover/voiceover-quality-review.mjs'
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


function score(ref,heard,subs,deletions,insertions){
  const edits=subs+deletions+insertions
  return {substitutions:subs,deletions,insertions,edit_distance:edits,
    reference_word_count:ref,heard_word_count:heard,
    word_error_rate:Math.round(edits/ref*100000)/100000,
    word_accuracy_is_not_pronunciation:true}
}
function werReceipt(){
 return {schema:'retailgrowth.feature2-verified-word-error-review.v1',
  shop_id:shopId,campaign_id:campaignId,
  audio_asset_id:receipt.private_audio_asset_id,
  creative_plan_sha256:planSha256,
  original_audio_sha256:audioSha,source_job_id:'job_test',
  feature7_hmac_and_current_source_verified:true,
  feature7_asr_word_error:score(3,2,0,1,0),
  human_signed_transcript_available:false,
  human_transcript_vs_script_error:null,
  feature7_asr_vs_human_error:null,
  human_accuracy_not_assumed:true,
  real_worker_execution_independently_observed:false,
  source_only_metric_not_acoustic_certification:true,
  pronunciation_verified:false,can_publish:false}
}
function verifyWer(metrics=werReceipt()){
 return verifySignedWordErrorReview({
   shopId,campaignId,planSha256,receipt,metrics})
}
test('actual signed WER summary remains separate from acoustic and publish approval',()=>{
 const x=verifyWer()
 assert.equal(x.asr.word_error_rate,0.33333)
 assert.equal(x.asr.deletions,1)
 assert.equal(x.signed_human_review_reported,false)
 assert.equal(x.manual_human_reference,null)
 assert.equal(x.actual_inference_independently_observed,false)
 assert.equal(x.pronunciation_certified,false)
 assert.equal(x.can_publish,false)
 assert.ok(Object.isFrozen(x))
 assert.ok(Object.isFrozen(x.asr))
})
test('independently signed human transcript comparison can display aggregate-only counts',()=>{
 const x=werReceipt()
 x.human_signed_transcript_available=true
 x.human_transcript_vs_script_error=score(3,2,0,1,0)
 x.feature7_asr_vs_human_error=score(2,2,0,0,0)
 const result=verifyWer(x)
 assert.equal(result.signed_human_review_reported,true)
 assert.equal(result.asr_vs_human.word_error_rate,0)
 assert.equal(result.manual_human_reference.deletions,1)
 assert.equal(result.pronunciation_certified,false)
})
test('reject forged signed WER, invented percentage or changed asset identity',()=>{
 for(const [key,value] of [
   ['shop_id',campaignId],['campaign_id',shopId],
   ['original_audio_sha256','a'.repeat(64)],
   ['creative_plan_sha256','c'.repeat(64)],
   ['audio_asset_id',shopId],
   ['feature7_hmac_and_current_source_verified',false],
   ['human_accuracy_not_assumed',false],
   ['real_worker_execution_independently_observed',true],
   ['source_only_metric_not_acoustic_certification',false],
   ['pronunciation_verified',true],['can_publish',true],
   ['human_signed_transcript_available',true],
 ])assert.throws(()=>verifyWer({...werReceipt(),[key]:value}),undefined,key)
 const forged=werReceipt()
 forged.feature7_asr_word_error={...forged.feature7_asr_word_error,
   word_error_rate:0}
 assert.throws(()=>verifyWer(forged))
 const edited=werReceipt()
 edited.feature7_asr_word_error={...edited.feature7_asr_word_error,
   edit_distance:0}
 assert.throws(()=>verifyWer(edited))
 const unexpected=werReceipt()
 unexpected.feature7_asr_word_error={...unexpected.feature7_asr_word_error,
   word_accuracy_is_not_pronunciation:false}
 assert.throws(()=>verifyWer(unexpected))
})
test('WER higher than 100 percent is allowed when there are extra spoken words',()=>{
 const p=werReceipt()
 p.feature7_asr_word_error=score(1,4,0,0,3)
 const x=verifyWer(p)
 assert.equal(x.asr.word_error_rate,3)
})


// Browser rendering must independently reject Unicode spoofing even if a
// mocked server claims a matching private ASR source; this is not worker proof.
test('review UI denies invisible/bidi spoof and whitespace inside signed word hints',()=>{
 const words=[
   'kurti\u202e','kurti\u200b','कुर्ती\u2066','kurti\u2028',
   'kurti\u00ad','two words',' trailing','trailing ','<svg>'
 ]
 for(const word of words){
   const altered=review()
   altered.asr_word_timing[0].word=word
   assert.throws(()=>verifyPrivateVoiceQualityReview({
     shopId,campaignId,planSha256,receipt,review:altered}),undefined,JSON.stringify(word))
   const issue=review()
   issue.asr_issues[0].word=word
   assert.throws(()=>verifyPrivateVoiceQualityReview({
     shopId,campaignId,planSha256,receipt,review:issue}),undefined,JSON.stringify(word))
 }
})

test('legitimate Indian conjunct and punctuation-free single tokens survive',()=>{
 const original=review()
 original.asr_word_timing[0].word='क्\u200dष'
 original.asr_issues[0].word='कुर्ती'
 const out=verifyPrivateVoiceQualityReview({
   shopId,campaignId,planSha256,receipt,review:original})
 assert.equal(out.words[0].word,'क्\u200dष')
 assert.equal(out.issues[0].word,'कुर्ती')
 assert.ok(Object.isFrozen(out.words[0]))
 assert.ok(Object.isFrozen(out.issues[0]))
})

test('quality review and aggregate WER reject forged audio identity or job ID',()=>{
 const wrongReceipt={...receipt,private_audio_asset_id:'unscoped-job'}
 const wrongReview={...review(),audio_asset_id:'unscoped-job'}
 assert.throws(()=>verifyPrivateVoiceQualityReview({
   shopId,campaignId,planSha256,receipt:wrongReceipt,review:wrongReview}))
 const forged=werReceipt()
 forged.source_job_id='../another-job'
 assert.throws(()=>verifyWer(forged))
 assert.throws(()=>verifySignedWordErrorReview({
   shopId,campaignId,planSha256:'invalid-plan',
   receipt:{...receipt,creative_plan_sha256:'invalid-plan'},
   metrics:{...werReceipt(),creative_plan_sha256:'invalid-plan'}}))
})
