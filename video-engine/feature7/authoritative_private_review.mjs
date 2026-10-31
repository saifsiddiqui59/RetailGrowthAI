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

const BROLL_ID=/^[A-Za-z0-9_-]{1,100}$/;
const BROLL_REV=/^[A-Za-z0-9_-]{1,120}$/;
const BROLL_SHA=/^[a-f0-9]{64}$/;

// The submitted B-roll object is an asset reference, NOT a grant. Only the
// injected trusted registry lookup can create a grant for the review worker.
function currentBrollGrant({shop_id,request,current}) {
  check(request && typeof request.asset_id==='string' &&
    BROLL_ID.test(request.asset_id) &&
    typeof request.expected_sha256==='string' &&
    BROLL_SHA.test(request.expected_sha256) &&
    typeof request.rights_revision==='string' &&
    BROLL_REV.test(request.rights_revision),
  'Bounded B-roll asset reference and rights generation required');
  check(current && current.shop_id===shop_id &&
    current.asset_id===request.asset_id &&
    current.source==='retailer_upload' &&
    current.rights_status==='APPROVED' && current.active===true &&
    ['video','image'].includes(current.media_type) &&
    (current.media_type==='video' ? current.mime_type==='video/mp4' :
      ['image/jpeg','image/png','image/webp'].includes(current.mime_type)) &&
    current.sha256===request.expected_sha256 &&
    current.rights_revision===request.rights_revision &&
    Array.isArray(current.keywords) && current.keywords.length<=12 &&
    current.keywords.every(k=>typeof k==='string' && k.length<=50),
  'B-roll rights revoked, foreign, or source generation changed');
  // Whitelist server-derived fields. Never forward caller-supplied keywords,
  // issued_by, rights_status or active flags into the low-level suggestion API.
  return Object.freeze({
    shop_id,asset_id:request.asset_id,source:'retailer_upload',
    issued_by:'trusted_server',rights_status:'APPROVED',active:true,
    media_type:current.media_type,mime_type:current.mime_type,
    sha256:current.sha256,rights_revision:current.rights_revision,
    keywords:Object.freeze([...current.keywords])
  });
}

export function prepareAuthoritativePrivateReview({
  shop_id,campaign_id,draft,root,media,
  broll_grants=[],job_id,asr_key,rights_key,
  getCurrentApprovedVideo,getCurrentApprovedBroll,now_ms=Date.now()
}={}){
  check(typeof getCurrentApprovedVideo==='function' &&
    typeof shop_id==='string' && typeof campaign_id==='string' &&
    Array.isArray(media)&&media.length>0&&media.length<=12&&
    typeof job_id==='string'&&job_id.length>0,
    'Trusted current private rights loader required');
  check(Array.isArray(broll_grants) && broll_grants.length<=24 &&
    (broll_grants.length===0 || typeof getCurrentApprovedBroll==='function'),
  'Trusted current B-roll rights loader required');
  const seenBroll=new Set();
  const verifiedBroll=broll_grants.map(request=>{
    check(request && typeof request.asset_id==='string' &&
      !seenBroll.has(request.asset_id) &&
      !media.some(item=>item?.asset_id===request.asset_id),
    'Duplicate or ambiguous B-roll asset');
    seenBroll.add(request.asset_id);
    const current=getCurrentApprovedBroll({
      shop_id,asset_id:request.asset_id
    });
    return currentBrollGrant({shop_id,request,current});
  });
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
        broll_grants:verifiedBroll,job_id,asr_key,now_ms
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
  // B-roll is advisory-only, but still must not reference rights that changed
  // while the source was analyzed. A hosted approval/render needs its own
  // transactional current-rights/lease check beyond this synchronous helper.
  for(const grant of verifiedBroll){
    const current=getCurrentApprovedBroll({
      shop_id,asset_id:grant.asset_id
    });
    const fresh=currentBrollGrant({
      shop_id,request:{
        asset_id:grant.asset_id,expected_sha256:grant.sha256,
        rights_revision:grant.rights_revision
      },current
    });
    check(fresh.media_type===grant.media_type &&
      fresh.mime_type===grant.mime_type &&
      JSON.stringify(fresh.keywords)===JSON.stringify(grant.keywords),
    'B-roll metadata changed during source review');
  }
  return {...result,media_rights_evidence_verified:true,
    rights_rechecked_against_authoritative_registry:true,
    frozen_media_snapshot_verified:true,
    approved:false,renderable:false};
}
