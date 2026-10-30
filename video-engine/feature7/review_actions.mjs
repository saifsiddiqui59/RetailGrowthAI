/**
 * Feature7 human review editing state; independent of the Feature4 timeline UI.
 * Reviewers may adjust ONLY the selected contiguous source trim offset.
 * All other effects (captions, B-roll, sparse cuts) remain advisory.
 * This never approves, edits video, publishes or fetches a signed media URL.
 */
import {draftHashHint, EditValidationError} from './autobroll_semantics.mjs';

const check=(v,msg)=>{if(!v)throw new EditValidationError(msg);};
const isFiniteWithin=(v,min,max)=>typeof v==='number'&&Number.isFinite(v)&&v>=min&&v<=max;
const clone=x=>JSON.parse(JSON.stringify(x));
const ID=/^[A-Za-z0-9_-]{1,120}$/;

export function createReviewSession({draft,proposal,media_evidence,reviewer_view}={}){
  check(draft && proposal && typeof draft==='object'&&typeof proposal==='object' &&
    draft.shop_id===proposal.shop_id && draft.campaign_id===proposal.campaign_id &&
    ID.test(draft.shop_id??'')&&ID.test(draft.campaign_id??'') &&
    proposal.source_feature==='feature7' &&
    proposal.timeline_version==='creative_reel_v1' &&
    proposal.review_status==='NEEDS_REVIEW'&&proposal.approved===false&&
    proposal.renderable===false&&proposal.draft_sha256_hint===draftHashHint(draft)&&
    Array.isArray(draft.scenes)&&Array.isArray(proposal.scenes)&&
    Array.isArray(media_evidence)&&
    draft.scenes.length>=1&&draft.scenes.length<=12&&
    proposal.scenes.length===draft.scenes.length&&
    media_evidence.length===draft.scenes.length,
    'Current private source-only review is required');
  check(reviewer_view&&reviewer_view.shop_id===draft.shop_id&&
    reviewer_view.campaign_id===draft.campaign_id&&
    ID.test(reviewer_view.reviewer_id??'')&&
    ['OWNER','EDITOR','VIEWER'].includes(reviewer_view.role)&&
    reviewer_view.active_membership===true&&
    Number.isSafeInteger(reviewer_view.revision)&&reviewer_view.revision>=0,
    'Authenticated review-only view required');
  const seen=new Set(),originalScenes=clone(proposal.scenes);
  for(const [pos,edit] of originalScenes.entries()){
    const i=edit?.source_scene_index,src=draft.scenes[i],evidence=media_evidence[i];
    check(Number.isInteger(i)&&i>=0&&i<draft.scenes.length&&!seen.has(i)&&
      src?.asset_type==='video'&&src.source_feature==='retailer'&&
      ID.test(src.asset_id??'')&&
      evidence?.asset_id===src.asset_id&&
      evidence.local_media_verified==='LOCAL_BYTES_VERIFIED'&&
      /^[a-f0-9]{64}$/.test(evidence.source_sha256??'')&&
      isFiniteWithin(evidence.source_duration_seconds,0.5,600)&&
      isFiniteWithin(edit.duration,0.5,60)&&
      isFiniteWithin(edit.trim_start,0,evidence.source_duration_seconds-edit.duration+0.001)&&
      edit.mute_source===false,
      'Unverified source, scene rights or unsafe original trim');
    seen.add(i);
  }
  const canApprove=reviewer_view.role!=='VIEWER';
  const state={original_draft_sha256_hint:proposal.draft_sha256_hint,
    shop_id:draft.shop_id,campaign_id:draft.campaign_id,
    reviewer_id:reviewer_view.reviewer_id,expected_revision:reviewer_view.revision,
    can_request_approval:canApprove,
    source_scenes:clone(draft.scenes),scenes:originalScenes,
    captions_advisory:clone(proposal.captions_advisory??[]),
    owned_cutaways_advisory:clone(proposal.owned_cutaways_advisory??[]),
    silence_jump_cut_advisory:clone(proposal.silence_jump_cut_advisory??[]),
    warnings:clone(proposal.warnings??[]),
    media_evidence:clone(media_evidence),
    original_proposal:clone(proposal)};
  // These in-memory objects are for the UI only; the authoritative server
  // must reload current rights, draft, revision, and media bytes on approval.
  return Object.freeze(state);
}
export function adjustTrimStart(session,source_scene_index,trim_start_seconds){
  check(session && session.can_request_approval===true &&
    Number.isInteger(source_scene_index) &&
    Array.isArray(session.scenes)&&Array.isArray(session.media_evidence)&&
    isFiniteWithin(trim_start_seconds,0,600),'Invalid reviewer trim action');
  const scene=session.scenes.find(s=>s.source_scene_index===source_scene_index);
  const media=session.media_evidence[source_scene_index];
  check(scene&&media&&
    trim_start_seconds+scene.duration<=media.source_duration_seconds+0.001,
    'Source trim would exceed original media duration');
  const changed=clone(session.scenes).map(s=>s.source_scene_index===source_scene_index
    ? {...s,trim_start:Math.round(trim_start_seconds*1000)/1000}:s);
  return Object.freeze({...session,scenes:changed});
}
export function proposeReviewDecision(session,{action,confirmed}={}){
  check(session&&session.original_proposal&&
    ['REQUEST_APPROVAL','REJECT_PROPOSAL'].includes(action),
  'Unknown reviewer decision');
  check(session.can_request_approval===true,
    'VIEWER cannot modify reviewer decisions');
  if(action==='REQUEST_APPROVAL')
    check(confirmed===true,
      'Only an explicitly confirming OWNER/EDITOR can request approval');
  const proposal=clone(session.original_proposal);
  proposal.scenes=clone(session.scenes);
  proposal.approved=false;
  proposal.renderable=false;
  proposal.review_status='NEEDS_REVIEW';
  const packet={
    version:'feature7_reviewer_request_v1',
    action,
    shop_id:session.shop_id,campaign_id:session.campaign_id,
    draft_sha256_hint:session.original_draft_sha256_hint,
    expected_revision:session.expected_revision,
    edited_proposal:proposal,
    reviewer_confirmation:action==='REQUEST_APPROVAL' && confirmed===true,
    approved:false,renderable:false,
    requires_authoritative_server_transaction:true
  };
  // The host may enqueue this object asynchronously. Freeze the complete
  // already-cloned proposal so the candidate cannot change after dispatch.
  // This is client-side integrity only; the server still MUST reload and
  // authorize current tenant/source/revision before persisting human review.
  const deepFreeze=(value)=>{
    if(value&&typeof value==='object'&&!Object.isFrozen(value)){
      Object.values(value).forEach(deepFreeze);
      Object.freeze(value);
    }
    return value;
  };
  return deepFreeze(packet);
}
