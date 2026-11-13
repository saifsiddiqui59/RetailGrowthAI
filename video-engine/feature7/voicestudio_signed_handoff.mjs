/** Trusted-worker bridge from VoiceStudio review-only words to existing F7 evidence.
 * Not an HTTP boundary or approval. Caller MUST verify current JWT/RLS, private
 * video bytes, extracted WAV provenance, model license and active job lease.
 */
import {normalizeWhisperx} from './transcript_adapter.mjs';
import {sealTranscriptEvidence,verifyTranscriptEvidence} from './transcript_evidence.mjs';
import {buildCaptions,EditValidationError} from './autobroll_semantics.mjs';

const SHA=/^[a-f0-9]{64}$/;
const ID=/^[A-Za-z0-9_-]{1,120}$/;
const deny=(condition,message)=>{if(!condition)throw new EditValidationError(message);};

// Reject accessor-backed and inherited metadata before reading untrusted review or
// lease fields. These objects are worker handoff inputs, never authorization.
function requireOwnDataFields(value,fields) {
  deny(value!==null && typeof value==='object' && !Array.isArray(value),
    'Invalid VoiceStudio handoff record');
  for (const field of fields) {
    const descriptor=Object.getOwnPropertyDescriptor(value,field);
    deny(descriptor && Object.hasOwn(descriptor,'value'),
      'Unsafe VoiceStudio handoff field');
  }
}

export function bindVoiceStudioReview({
  review,shop_id,asset_id,job_id,original_video_sha256,
  original_audio_sha256,source_duration_seconds,lease,
  model_id,key,now_ms=Date.now()
}={}) {
  requireOwnDataFields(review,['schema','approved','renderable',
    'requires_feature7_signed_evidence','word_timings_present',
    'model_revision_verified_by_worker','language','audio_sha256','words','text']);
  requireOwnDataFields(lease,['shop_id','asset_id','job_id','source_sha256',
    'audio_sha256','model_id','active','expires_at_ms']);
  // Only a trusted worker may supply the lease and independently checked hashes.
  deny(review?.schema==='retailgrowth.feature7-voicestudio-asr-review.v1' &&
    review.approved===false && review.renderable===false &&
    review.requires_feature7_signed_evidence===true &&
    review.word_timings_present===true &&
    review.model_revision_verified_by_worker===false &&
    ['en','hi','mr'].includes(review.language) &&
    SHA.test(original_video_sha256??'') &&
    SHA.test(original_audio_sha256??'') &&
    review.audio_sha256===original_audio_sha256 &&
    [shop_id,asset_id,job_id,model_id].every(v=>typeof v==='string'&&ID.test(v)) &&
    Number.isFinite(source_duration_seconds) &&
    source_duration_seconds>0 && source_duration_seconds<=180 &&
    Number.isSafeInteger(now_ms) && now_ms>=0 &&
    Number.isSafeInteger(now_ms+600000),
    'Untrusted VoiceStudio review or source');
  deny(lease && lease.shop_id===shop_id && lease.asset_id===asset_id &&
    lease.job_id===job_id && lease.source_sha256===original_video_sha256 &&
    lease.audio_sha256===original_audio_sha256 &&
    lease.model_id===model_id && lease.active===true &&
    Number.isSafeInteger(lease.expires_at_ms) &&
    lease.expires_at_ms>now_ms && lease.expires_at_ms<=now_ms+600000,
    'Missing active exact-source ASR lease');
  deny(Array.isArray(review.words) && review.words.length>=1 &&
    review.words.length<=2000 && typeof review.text==='string' &&
    review.text.trim().length>0,'Missing real word timings');
  // Normalize through the existing transcript hash contract; never sign the
  // audio digest in place of the original VIDEO digest.
  const normalized=normalizeWhisperx({
    shop_id,asset_id,source_sha256:original_video_sha256,
    source_duration_seconds,
    transcript:{segments:[{words:review.words}]}
  });
  const expires_at_ms=Math.min(lease.expires_at_ms,now_ms+600000);
  const evidence=sealTranscriptEvidence({key,now_ms,data:{
    shop_id,asset_id,job_id,source_sha256:original_video_sha256,
    transcript_sha256:normalized.transcript_sha256,model_id,
    issued_at_ms:now_ms,expires_at_ms
  }});
  verifyTranscriptEvidence({evidence,key,now_ms,expect:{
    shop_id,asset_id,job_id,source_sha256:original_video_sha256,
    transcript_sha256:normalized.transcript_sha256,model_id
  }});
  const captions=buildCaptions(normalized.words,asset_id);
  return Object.freeze({
    schema:'retailgrowth.feature7-voicestudio-signed-review.v1',
    shop_id,asset_id,job_id,original_video_sha256,original_audio_sha256,
    language:review.language,transcript:normalized,evidence,
    // Export only canonical, validated words; never re-emit arbitrary ASR object
    // properties (including attacker-supplied metadata) as trusted evidence.
    whisperx_json:{segments:[{words:normalized.words.map(w=>({
      word:w.word,start:w.startMs/1000,end:w.endMs/1000
    }))}]},
    captions,feature4_edit_advice:Object.freeze({
      source_asset_id:asset_id,source_sha256:original_video_sha256,
      caption_cues_review_only:true,original_audio_preserved:true,
      requires_separately_persisted_human_approval:true,
      executable:false
    }),
    review_status:'NEEDS_REVIEW',approved:false,renderable:false
  });
}
