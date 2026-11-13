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
  const reviewFields=['schema','approved','renderable',
    'requires_feature7_signed_evidence','word_timings_present',
    'model_revision_verified_by_worker','language','audio_sha256','words','text'];
  const reviewSnapshot=Object.fromEntries(reviewFields.map(field=>[field,
    Object.getOwnPropertyDescriptor(review,field).value]));
  requireOwnDataFields(lease,['shop_id','asset_id','job_id','source_sha256',
    'audio_sha256','model_id','active','expires_at_ms']);
  // Snapshot authoritative lease fields once: later word normalization may invoke
  // other code, so never re-read a mutable lease after initial validation.
  const leaseSnapshot=Object.fromEntries(
    ['shop_id','asset_id','job_id','source_sha256','audio_sha256',
      'model_id','active','expires_at_ms'].map(field=>[field,
      Object.getOwnPropertyDescriptor(lease,field).value]));
  // Only a trusted worker may supply the lease and independently checked hashes.
  deny(reviewSnapshot.schema==='retailgrowth.feature7-voicestudio-asr-review.v1' &&
    reviewSnapshot.approved===false && reviewSnapshot.renderable===false &&
    reviewSnapshot.requires_feature7_signed_evidence===true &&
    reviewSnapshot.word_timings_present===true &&
    reviewSnapshot.model_revision_verified_by_worker===false &&
    ['en','hi','mr'].includes(reviewSnapshot.language) &&
    SHA.test(original_video_sha256??'') &&
    SHA.test(original_audio_sha256??'') &&
    reviewSnapshot.audio_sha256===original_audio_sha256 &&
    [shop_id,asset_id,job_id,model_id].every(v=>typeof v==='string'&&ID.test(v)) &&
    Number.isFinite(source_duration_seconds) &&
    source_duration_seconds>0 && source_duration_seconds<=180 &&
    Number.isSafeInteger(now_ms) && now_ms>=0 &&
    Number.isSafeInteger(now_ms+600000),
    'Untrusted VoiceStudio review or source');
  deny(leaseSnapshot.shop_id===shop_id && leaseSnapshot.asset_id===asset_id &&
    leaseSnapshot.job_id===job_id && leaseSnapshot.source_sha256===original_video_sha256 &&
    leaseSnapshot.audio_sha256===original_audio_sha256 &&
    leaseSnapshot.model_id===model_id && leaseSnapshot.active===true &&
    Number.isSafeInteger(leaseSnapshot.expires_at_ms) &&
    leaseSnapshot.expires_at_ms>now_ms && leaseSnapshot.expires_at_ms<=now_ms+600000,
    'Missing active exact-source ASR lease');
  deny(Array.isArray(reviewSnapshot.words) && reviewSnapshot.words.length>=1 &&
    reviewSnapshot.words.length<=2000 && typeof reviewSnapshot.text==='string' &&
    reviewSnapshot.text.length<=20000 && reviewSnapshot.text.trim().length>0,'Missing real word timings');
  // Validate each word's own data descriptors before the normalizer reads it.
  // Accessor-backed timestamps or text must not execute inside a signing path.
  for (let i=0;i<reviewSnapshot.words.length;i++) {
    deny(Object.hasOwn(reviewSnapshot.words,i),'Sparse VoiceStudio word list');
    requireOwnDataFields(reviewSnapshot.words[i],['word','start','end']);
  }
  // Normalize through the existing transcript hash contract; never sign the
  // audio digest in place of the original VIDEO digest.
  const normalized=normalizeWhisperx({
    shop_id,asset_id,source_sha256:original_video_sha256,
    source_duration_seconds,
    transcript:{segments:[{words:reviewSnapshot.words}]}
  });
  // Reject a review whose identity, word-list reference or approval flags were
  // changed while untrusted word objects were being normalized.
  requireOwnDataFields(review,reviewFields);
  deny(Object.entries(reviewSnapshot).every(([field,value])=>
    Object.is(Object.getOwnPropertyDescriptor(review,field).value,value)),
    'VoiceStudio review changed during transcript normalization');
  // Recheck after normalization: a mutable lease revoked mid-operation must
  // never yield a signed transcript, even when the adapter reuses one object.
  requireOwnDataFields(lease,Object.keys(leaseSnapshot));
  deny(Object.entries(leaseSnapshot).every(([field,value])=>
    Object.is(Object.getOwnPropertyDescriptor(lease,field).value,value)),
    'ASR lease changed during transcript normalization');
  const expires_at_ms=Math.min(leaseSnapshot.expires_at_ms,now_ms+600000);
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
    language:reviewSnapshot.language,transcript:normalized,evidence,
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
