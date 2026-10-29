// Typed source-only display of a private, server-verified F7 original-WAV QA
// result. Browser validation is NOT proof of backend JWT/rights/HMAC or model
// accuracy. The trusted server must verify those before returning this record.
const SHA=/^[a-f0-9]{64}$/
const reject=()=>{throw Error('Trusted current narration quality review unavailable')}
const problems=new Set([
  'MISSING_OR_SUBSTITUTED_WORD','MISSING_WORD','UNEXPECTED_WORD',
  'REPLACED_WORD','INSERTED_WORD','DELETED_WORD'
])
const pcm=new Set(['audio_clipped','too_quiet','too_loud','excessive_silence'])
const safeWord=value=>typeof value==='string'&&value.trim().length>0&&
  value.length<=80&&!/[<>\x00-\x1f]/.test(value)
export function verifyPrivateVoiceQualityReview({
  shopId,campaignId,planSha256,receipt,review
}={}) {
  if(!receipt||!review||typeof review!=='object'||Array.isArray(review)||
    review.schema!=='retailgrowth.feature2-verified-audio-qa.v1'||
    review.shop_id!==shopId||review.campaign_id!==campaignId||
    review.creative_plan_sha256!==planSha256||
    !SHA.test(planSha256||'')||
    review.audio_asset_id!==receipt.private_audio_asset_id||
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
    return {word:row.word,start_seconds:row.startMs/1000,
      end_seconds:row.endMs/1000}
  })
  const issues=review.asr_issues.map(row=>{
    if(!row||typeof row!=='object'||Array.isArray(row)||
      !problems.has(row.problem)||!safeWord(row.word)||
      (row.audio_start_seconds!==null&&
        (typeof row.audio_start_seconds!=='number'||
         !Number.isFinite(row.audio_start_seconds)||
         row.audio_start_seconds<0||
         row.audio_start_seconds>review.audio_duration_seconds)))reject()
    return {problem:row.problem,word:row.word,
      at_seconds:row.audio_start_seconds??null,
      action:'CHECK_ORIGINAL_AUDIO_AND_PROPOSE_HUMAN_REVIEW'}
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
