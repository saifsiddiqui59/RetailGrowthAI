// Typed source-only display of a private, server-verified F7 original-WAV QA
// result. Browser validation is NOT proof of backend JWT/rights/HMAC or model
// accuracy. The trusted server must verify those before returning this record.
const SHA=/^[a-f0-9]{64}$/
const UUID=/^[a-f0-9]{8}-[a-f0-9]{4}-4[a-f0-9]{3}-[89ab][a-f0-9]{3}-[a-f0-9]{12}$/
const reject=()=>{throw Error('Trusted current narration quality review unavailable')}
const problems=new Set([
  'MISSING_OR_SUBSTITUTED_WORD','MISSING_WORD','UNEXPECTED_OR_SUBSTITUTED_WORD','UNEXPECTED_WORD',
  'REPLACED_WORD','INSERTED_WORD','DELETED_WORD'
])
const pcm=new Set(['audio_clipped','too_quiet','too_loud','excessive_silence'])
// The backend also filters ASR display control characters; fail closed in
// the browser to avoid bidi spoof, invisible edits or false reviewer matches.
// ZWJ/ZWNJ stay allowed for legitimate Hindi/Marathi conjuncts.
const UNSAFE_AUDIO_TEXT=/[<>\x00-\x1f\x7f-\x9f\u00ad\u061c\u180e\u200b\u200e\u200f\u2028-\u202e\u2060-\u206f\ufeff]/u
const safeWord=value=>{
  if(typeof value!=='string'||value.length===0||value.length>80||
     value.trim()!==value||/\s/u.test(value)||UNSAFE_AUDIO_TEXT.test(value))
    return false
  for(let i=0;i<value.length;i++){
    if(value[i]==='\u200c'||value[i]==='\u200d'){
      const next=value[i+1]||''
      // Match Python's verified-word display rule: only a Devanagari
      // virama + conjunct letter may contain a zero-width joiner.
      if(i===0||value[i-1]!=='\u094d'||
         !/[\u0900-\u097f]/u.test(next)||!/\p{L}/u.test(next))
        return false
    }
  }
  return true
}
export function verifyPrivateVoiceQualityReview({
  shopId,campaignId,planSha256,receipt,review
}={}) {
  if(!receipt||!review||typeof review!=='object'||Array.isArray(review)||
    review.schema!=='retailgrowth.feature2-verified-audio-qa.v1'||
    review.shop_id!==shopId||review.campaign_id!==campaignId||
    review.creative_plan_sha256!==planSha256||
    !SHA.test(planSha256||'')||
    review.audio_asset_id!==receipt.private_audio_asset_id||
    !UUID.test(receipt.private_audio_asset_id||'')||
    review.original_audio_sha256!==receipt.original_audio_sha256||
    !SHA.test(review.original_audio_sha256||'')||
    receipt.shop_id!==shopId||receipt.campaign_id!==campaignId||
    receipt.creative_plan_sha256!==planSha256||
    receipt.private!==true||receipt.can_publish!==false||
    review.source_rechecked!==true||
    review.review_state!=='PENDING_HUMAN_LISTEN_AND_RIGHTS'||
    review.can_publish!==false||review.approved_for_editing!==false||
    review.pronunciation_verified!==false||
    review.asr_word_confidence_available!==false||
    typeof review.asr_transcript_matched_script!=='boolean'||
    !Array.isArray(review.asr_issues)||review.asr_issues.length>200||
    !Array.isArray(review.pcm_quality_warnings)||
    review.pcm_quality_warnings.length>4||
    !Array.isArray(review.asr_word_timing)||
    !review.asr_word_timing.length||review.asr_word_timing.length>600||
    typeof review.audio_duration_seconds!=='number'||
    !Number.isFinite(review.audio_duration_seconds)||
    review.audio_duration_seconds<0.2||review.audio_duration_seconds>65||
    Math.abs(review.audio_duration_seconds-receipt.duration_seconds)>0.005
  )reject()
  let end=0
  const words=review.asr_word_timing.map(row=>{
    if(!row||typeof row!=='object'||Array.isArray(row)||
      Object.keys(row).sort().join('|')!=='endMs|startMs|word'||
      !safeWord(row.word)||
      !Number.isInteger(row.startMs)||!Number.isInteger(row.endMs)||
      row.startMs<end||row.endMs<=row.startMs||
      row.endMs>Math.round(review.audio_duration_seconds*1000)+1)reject()
    end=row.endMs
    return Object.freeze({word:row.word,start_seconds:row.startMs/1000,
      end_seconds:row.endMs/1000})
  })
  const issues=review.asr_issues.map(row=>{
    if(!row||typeof row!=='object'||Array.isArray(row)||
      !problems.has(row.problem)||!safeWord(row.word)||
      (row.confidence!==undefined && row.confidence!==null)||
      (row.audio_start_seconds!==null&&
        (typeof row.audio_start_seconds!=='number'||
         !Number.isFinite(row.audio_start_seconds)||
         row.audio_start_seconds<0||
         row.audio_start_seconds>review.audio_duration_seconds)))reject()
    return Object.freeze({problem:row.problem,word:row.word,
      at_seconds:row.audio_start_seconds??null,
      action:'CHECK_ORIGINAL_AUDIO_AND_PROPOSE_HUMAN_REVIEW'})
  })
  const warnings=review.pcm_quality_warnings.map(s=>{
    if(typeof s!=='string'||!pcm.has(s))reject()
    return s
  })
  return Object.freeze({
    asr_matched_script:review.asr_transcript_matched_script,
    words:Object.freeze(words),issues:Object.freeze(issues),
    pcm_warnings:Object.freeze(warnings),
    confidence_available:false,pronunciation_verified:false,
    human_listening_required:true,rights_review_required:true,
    edit_approved:false,can_publish:false,
    audio_asset_id:review.audio_asset_id
  })
}


// The server, NOT this browser, must validate F7 HMAC and the signed human
// transcript. Metrics from synthetic F7 fixtures are never a pronunciation or
// commercial-success claim. A WER over 100% is valid for many insertions.
export function verifySignedWordErrorReview({
  shopId,campaignId,planSha256,receipt,metrics
}={}){
  if(!metrics||typeof metrics!=='object'||Array.isArray(metrics)||
    !receipt||receipt.shop_id!==shopId||receipt.campaign_id!==campaignId||
    receipt.creative_plan_sha256!==planSha256||
    !SHA.test(planSha256||'')||
    !UUID.test(receipt.private_audio_asset_id||'')||
    !SHA.test(receipt.original_audio_sha256||'')||
    metrics.schema!=='retailgrowth.feature2-verified-word-error-review.v1'||
    metrics.shop_id!==shopId||metrics.campaign_id!==campaignId||
    metrics.creative_plan_sha256!==planSha256||
    metrics.audio_asset_id!==receipt.private_audio_asset_id||
    typeof metrics.source_job_id!=='string'||
    !/^[A-Za-z0-9_-]{1,120}$/.test(metrics.source_job_id)||
    metrics.original_audio_sha256!==receipt.original_audio_sha256||
    metrics.feature7_hmac_and_current_source_verified!==true||
    metrics.real_worker_execution_independently_observed!==false||
    metrics.source_only_metric_not_acoustic_certification!==true||
    metrics.human_accuracy_not_assumed!==true||
    metrics.pronunciation_verified!==false||
    metrics.can_publish!==false||
    typeof metrics.human_signed_transcript_available!=='boolean')reject()
  function checkCounts(score){
    if(!score||typeof score!=='object'||Array.isArray(score))reject()
    const keys=['substitutions','deletions','insertions','edit_distance',
      'reference_word_count','heard_word_count']
    if(keys.some(k=>!Number.isSafeInteger(score[k])||score[k]<0)||
      score.reference_word_count<1||score.reference_word_count>600||
      score.heard_word_count<1||score.heard_word_count>600||
      score.edit_distance!==score.substitutions+score.deletions+score.insertions||
      typeof score.word_error_rate!=='number'||
      !Number.isFinite(score.word_error_rate)||
      Math.abs(score.word_error_rate-
        Math.round(score.edit_distance/score.reference_word_count*100000)/100000)>0.000001||
      score.word_accuracy_is_not_pronunciation!==true)reject()
    return Object.freeze({reference_words:score.reference_word_count,
      recognized_words:score.heard_word_count,
      substitutions:score.substitutions,deletions:score.deletions,
      insertions:score.insertions,word_error_rate:score.word_error_rate})
  }
  const asr=checkCounts(metrics.feature7_asr_word_error)
  const reviewed=metrics.human_signed_transcript_available
  if(reviewed!==(metrics.human_transcript_vs_script_error!==null)||
     reviewed!==(metrics.feature7_asr_vs_human_error!==null))reject()
  const human=reviewed?checkCounts(metrics.human_transcript_vs_script_error):null
  const asrVsHuman=reviewed?checkCounts(metrics.feature7_asr_vs_human_error):null
  return Object.freeze({
    asr,manual_human_reference:human,asr_vs_human:asrVsHuman,
    signed_human_review_reported:reviewed,
    actual_inference_independently_observed:false,
    pronunciation_certified:false,can_publish:false,
    original_audio_sha256:receipt.original_audio_sha256
  })
}
