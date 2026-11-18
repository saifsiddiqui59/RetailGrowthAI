/**
 * Feature7 source-only approval/revision fence for Feature4 F4-15.
 *
 * NOT a hosted human-review endpoint or a database. Callers must retrieve a
 * current JWT/RLS-authenticated OWNER/EDITOR membership and store the approval
 * atomically in the coordinator's DB. This module makes the approved-execution
 * handoff deterministic and independently testable without Feature4 changes.
 */
import crypto from 'node:crypto';
import {draftHashHint} from './autobroll_semantics.mjs';

export class ReviewFenceError extends Error {}
const check=(ok,msg)=>{if(!ok) throw new ReviewFenceError(msg);};
const REF=/^[A-Za-z0-9_-]{1,120}$/,SHA=/^[a-f0-9]{64}$/;
const MAX_TTL=10*60*1000;
const allowedSceneKeys=new Set(['source_scene_index','duration','trim_start','mute_source',
  'animation_preset','transition']);
const anim=new Set(['subtle_zoom','fade','slide','pop','glow']);
const trans=new Set(['fade','slide','cut']);

function stableJSON(x) {
  if(Array.isArray(x)) return x.map(stableJSON);
  if(x && typeof x==='object')return Object.fromEntries(Object.keys(x).sort()
    .map(k=>[k,stableJSON(x[k])]));
  return x;
}
function sha(x) {
  return crypto.createHash('sha256').update(JSON.stringify(stableJSON(x))).digest('hex');
}
function secret(key) {
  check(Buffer.isBuffer(key) && key.length>=32,'Missing private review service key');
  return key;
}
function mac(payload,key){
  return crypto.createHmac('sha256',secret(key)).update(
    'retailgrowth.feature7.review.v1\n'+JSON.stringify(payload)).digest('hex');
}
function validateCandidate(proposal,draft) {
  check(proposal && proposal.source_feature==='feature7' &&
    proposal.review_status==='NEEDS_REVIEW' && proposal.approved===false &&
    proposal.renderable===false && proposal.timeline_version==='creative_reel_v1' &&
    proposal.shop_id===draft?.shop_id && proposal.campaign_id===draft?.campaign_id &&
    proposal.draft_sha256_hint===draftHashHint(draft) &&
    [15,30,60].includes(draft.duration_seconds) && Array.isArray(draft.scenes) &&
    Array.isArray(proposal.scenes) && proposal.scenes.length===draft.scenes.length &&
    proposal.scenes.length>=1 && proposal.scenes.length<=12,
  'Only original reviewed Feature7 proposals may be approved');
  const used=new Set();
  let total=0;
  for(const scene of proposal.scenes) {
    check(scene && typeof scene==='object' &&
      Object.keys(scene).every(k=>allowedSceneKeys.has(k)) &&
      Number.isInteger(scene.source_scene_index) &&
      scene.source_scene_index>=0 && scene.source_scene_index<draft.scenes.length &&
      !used.has(scene.source_scene_index) &&
      typeof scene.duration==='number' && Number.isFinite(scene.duration) &&
      scene.duration>=0.5 && scene.duration<=60 &&
      typeof scene.trim_start==='number' && Number.isFinite(scene.trim_start) &&
      scene.trim_start>=0 && scene.trim_start<=3600 &&
      scene.mute_source===false &&
      (scene.animation_preset===undefined||anim.has(scene.animation_preset)) &&
      (scene.transition===undefined||trans.has(scene.transition)),
    'Unreviewed edit, source mute, invalid trim or duplicate scene');
    used.add(scene.source_scene_index);
    total+=scene.duration;
  }
  check(Math.abs(total-draft.duration_seconds)<0.001,
    'Approved scene durations must fill original video');
}
function validateContext(context,proposal) {
  check(context && context.shop_id===proposal.shop_id &&
    context.campaign_id===proposal.campaign_id &&
    typeof context.reviewer_id==='string' && REF.test(context.reviewer_id) &&
    context.active_membership===true &&
    ['OWNER','EDITOR'].includes(context.role) &&
    context.video_rights_current===true &&
    Number.isSafeInteger(context.revision) && context.revision>=0 &&
    typeof context.source_snapshot_sha256==='string' &&
    SHA.test(context.source_snapshot_sha256),
  'Missing current trusted reviewer, source rights, or revision');
}
// Called by server transaction AFTER seeing the human's specific approval
// action. This receipt does NOT persist itself anywhere.
export function sealHumanEditApproval({proposal,draft,context,
  approval_id,canonical_draft_sha256,key,now_ms=Date.now()}={}) {
  validateCandidate(proposal,draft);
  validateContext(context,proposal);
  check(typeof approval_id==='string' && REF.test(approval_id) &&
    SHA.test(canonical_draft_sha256??'') &&
    Number.isSafeInteger(now_ms) && now_ms>=0 &&
    now_ms<=Number.MAX_SAFE_INTEGER-MAX_TTL,
  'Missing server canonical draft hash or approval id');
  const payload={
    version:'feature7_review_receipt_v1',approval_id,
    shop_id:proposal.shop_id,campaign_id:proposal.campaign_id,
    reviewer_id:context.reviewer_id,role:context.role,
    revision:context.revision,
    source_snapshot_sha256:context.source_snapshot_sha256,
    candidate_sha256:sha(proposal),
    draft_sha256:canonical_draft_sha256,
    issued_at_ms:now_ms,expires_at_ms:now_ms+MAX_TTL
  };
  return Object.freeze({...payload,mac:mac(payload,key)});
}
// Called by coordinator after re-reading authoritative DB state in a single
// transaction. Then it must persist approval, prevent duplicate use, and pass
// exact output to Feature4's execute_approved_edit.
export function buildFeature4EditHandoff({proposal,draft,context,receipt,
  canonical_draft_sha256,key,now_ms=Date.now()}={}) {
  validateCandidate(proposal,draft);
  validateContext(context,proposal);
  check(receipt && typeof receipt==='object' &&
    receipt.version==='feature7_review_receipt_v1' &&
    typeof receipt.mac==='string' && SHA.test(receipt.mac) &&
    typeof receipt.approval_id==='string' && REF.test(receipt.approval_id) &&
    Number.isSafeInteger(now_ms) &&
    Number.isSafeInteger(receipt.issued_at_ms) &&
    Number.isSafeInteger(receipt.expires_at_ms) &&
    receipt.issued_at_ms>=0 &&
    receipt.expires_at_ms>receipt.issued_at_ms &&
    now_ms>=receipt.issued_at_ms &&
    now_ms<=receipt.expires_at_ms &&
    receipt.expires_at_ms-receipt.issued_at_ms<=MAX_TTL &&
    receipt.shop_id===context.shop_id &&
    receipt.campaign_id===context.campaign_id &&
    receipt.reviewer_id===context.reviewer_id &&
    receipt.role===context.role &&
    receipt.revision===context.revision &&
    receipt.source_snapshot_sha256===context.source_snapshot_sha256 &&
    receipt.candidate_sha256===sha(proposal) &&
    receipt.draft_sha256===canonical_draft_sha256 &&
    canonical_draft_sha256 && SHA.test(canonical_draft_sha256),
  'Stale, revoked or cross-tenant review');
  const payload={
    version:receipt.version,approval_id:receipt.approval_id,
    shop_id:receipt.shop_id,campaign_id:receipt.campaign_id,
    reviewer_id:receipt.reviewer_id,role:receipt.role,revision:receipt.revision,
    source_snapshot_sha256:receipt.source_snapshot_sha256,
    candidate_sha256:receipt.candidate_sha256,
    draft_sha256:receipt.draft_sha256,
    issued_at_ms:receipt.issued_at_ms,expires_at_ms:receipt.expires_at_ms
  };
  check(crypto.timingSafeEqual(Buffer.from(mac(payload,key),'hex'),
    Buffer.from(receipt.mac,'hex')),'Invalid approval signature');
  return Object.freeze({
    approved_edits:{
      source_feature:'feature7',approved:true,
      approval_id:receipt.approval_id,timeline_version:'creative_reel_v1',
      shop_id:proposal.shop_id,campaign_id:proposal.campaign_id,
      draft_sha256:canonical_draft_sha256,
      scenes:proposal.scenes.map(s=>({...s}))
    },
    snapshot_edit_plan:{
      source_feature:'feature7',approved:true,
      approval_id:receipt.approval_id,timeline_version:'creative_reel_v1'
    },
    approved_in_source_only:true,
    requires_authoritative_db_persistence:true,
    no_render_performed:true
  });
}
