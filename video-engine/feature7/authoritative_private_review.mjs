/**
 * Feature7 stricter private-worker entry point:
 * signed rights + CURRENT server media-rights lookup + signed ASR,
 * then real local private MP4 bytes/ffprobe and reviewer suggestion engine.
 *
 * Every call must be made behind a trusted authenticated JWT/RLS backend.
 * The callback MUST query the current authoritative media registry; it
 * must never deserialize rights directly from the requesting browser.
 */
import {verifyMediaRightsEvidence} from './media_rights_evidence.mjs';
import {verifyPrivateVideo} from './media_preflight.mjs';
import {withVerifiedPrivateVideoSnapshots} from './private_media_snapshot.mjs';
import {prepareEvidenceBoundReview} from './evidence_bound_review.mjs';
import {EditValidationError} from './autobroll_semantics.mjs';

const check=(ok,msg)=>{if(!ok)throw new EditValidationError(msg);};

export function prepareAuthoritativePrivateReview({
  shop_id,campaign_id,draft,root,media,
  broll_grants=[],job_id,asr_key,rights_key,
  getCurrentApprovedVideo,now_ms=Date.now()
}={}){
  check(typeof getCurrentApprovedVideo==='function' &&
    typeof shop_id==='string' && typeof campaign_id==='string' &&
    Array.isArray(media)&&media.length>0&&media.length<=12&&
    typeof job_id==='string'&&job_id.length>0,
    'Trusted current private rights loader required');
  const verified=media.map(item=>{
    check(item&&item.asset_id&&item.rights_evidence &&
      typeof item.expected_sha256==='string',
      'Missing signed source-video rights');
    // getCurrentApprovedVideo is an internal RLS-verified database lookup.
    // This function is synchronous deliberately: no time-of-check/use window
    // inside a single pending authorized transaction is hidden by awaits.
    const current=getCurrentApprovedVideo({shop_id,asset_id:item.asset_id});
    check(current&&current.shop_id===shop_id&&
      current.asset_id===item.asset_id&&
      current.source==='retailer_upload'&&
      current.rights_status==='APPROVED'&&current.active===true&&
      current.media_type==='video'&&current.mime_type==='video/mp4'&&
      typeof current.rights_revision==='string'&&
      current.sha256===item.expected_sha256&&
      current.relative_path===item.relative_path,
      'Video rights revoked or source has changed');
    verifyMediaRightsEvidence({
      evidence:item.rights_evidence,key:rights_key,now_ms,
      expect:{shop_id,asset_id:item.asset_id,job_id,
        source_sha256:item.expected_sha256,
        relative_path:item.relative_path,
        rights_revision:current.rights_revision}
    });
    // The trusted registry is authoritative; never forward a submitted
    // browser grant object into private_review_pipeline.
    const grant={...current,issued_by:'trusted_server'};
    const checked=verifyPrivateVideo({shop_id,asset_id:item.asset_id,
      grant,root,relative_path:item.relative_path,
      expected_sha256:item.expected_sha256});
    // Actual ffprobe duration is authoritative, never browser metadata.
    return {...item,grant,source_duration_seconds:checked.duration_seconds};
  });
  const result=withVerifiedPrivateVideoSnapshots({
    shop_id,root,media:verified,analyze:(frozenRoot)=>
      prepareEvidenceBoundReview({
        shop_id,campaign_id,draft,root:frozenRoot,media:verified,
        broll_grants,job_id,asr_key,now_ms
      })
  });
  // No transaction is held across this synchronous source-level function.
  // Check again immediately before returning, while rejecting any revoked
  // or changed registry snapshot. The hosted coordinator must enforce an
  // actual DB lock/lease for the final approval/render boundary.
  for(const item of verified){
    const current=getCurrentApprovedVideo({shop_id,asset_id:item.asset_id});
    check(current && current.shop_id===shop_id &&
      current.asset_id===item.asset_id &&
      current.active===true && current.rights_status==='APPROVED' &&
      current.rights_revision===item.grant.rights_revision &&
      current.sha256===item.expected_sha256 &&
      current.relative_path===item.relative_path &&
      current.has_audio===item.grant.has_audio,
    'Private video rights changed during source review');
  }
  return {...result,media_rights_evidence_verified:true,
    rights_rechecked_against_authoritative_registry:true,
    frozen_media_snapshot_verified:true,
    approved:false,renderable:false};
}
