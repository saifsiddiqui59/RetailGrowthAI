/**
 * Feature7 trust fence: accepts only signed ASR evidence for every source scene.
 *
 * User-facing callers MUST NOT call preparePrivateReview directly. These pure
 * functions are internal to the coordinator-authorized private worker.
 * HMAC binding is NOT a substitute for live current membership/media checks.
 */
import {normalizeWhisperx} from './transcript_adapter.mjs';
import {verifyTranscriptEvidence} from './transcript_evidence.mjs';
import {preparePrivateReview} from './private_review_pipeline.mjs';
import {EditValidationError} from './autobroll_semantics.mjs';

export function prepareEvidenceBoundReview({shop_id,campaign_id,draft,root,
  media,broll_grants=[],job_id,asr_key,expected_asr_model_id,now_ms=Date.now()}={}) {
  if(!Array.isArray(media) || media.length===0 || media.length>12 ||
     typeof job_id!=='string' || job_id.length===0)
    throw new EditValidationError('Private evidence-bound review required');
  const verifiedMedia=[];
  for(const item of media) {
    if(!item || !item.grant || item.grant.shop_id!==shop_id ||
      !item.grant.active || item.grant.rights_status!=='APPROVED' ||
      !item.whisperx_json || !item.asr_evidence)
      throw new EditValidationError('Missing currently approved video and ASR');
    // Revalidate raw transcript before making assertions about the HMAC.
    const normalized=normalizeWhisperx({
      asset_id:item.asset_id,shop_id,
      source_sha256:item.expected_sha256,
      source_duration_seconds:item.source_duration_seconds,
      transcript:item.whisperx_json
    });
    verifyTranscriptEvidence({evidence:item.asr_evidence,key:asr_key,now_ms,
      expect:{shop_id,asset_id:item.asset_id,job_id,
        source_sha256:item.expected_sha256,
        transcript_sha256:normalized.transcript_sha256,
        ...(expected_asr_model_id===undefined ? {} :
          {model_id:expected_asr_model_id})}});
    verifiedMedia.push(item);
  }
  const proposal=preparePrivateReview({
    shop_id,campaign_id,draft,root,media:verifiedMedia,broll_grants
  });
  if(proposal.media_evidence.some((e,i)=>
    e.transcript_sha256 !== verifiedMedia[i].asr_evidence.transcript_sha256 ||
    e.source_sha256 !== verifiedMedia[i].asr_evidence.source_sha256))
    throw new EditValidationError('Verified media changed after ASR');
  return {...proposal,transcript_evidence_verified:true,
    asr_job_id:job_id,review_status:'NEEDS_REVIEW',approved:false,
    renderable:false};
}
