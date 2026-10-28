/**
 * Feature7 reviewer timeline projection for already-approved owned footage.
 * No audio processing, video rendering or copied Feature4 UI. Exact times
 * and authorized IDs are handed to the existing Feature4 editor as advisory.
 */
import crypto from 'node:crypto';
export class TimelineReviewError extends Error {}
const check=(ok,msg)=>{if(!ok)throw new TimelineReviewError(msg);};
const REF=/^[A-Za-z0-9_-]{1,120}$/;

export function buildReviewTimeline({proposal,draft,approved_asset_grants}={}) {
  check(proposal && proposal.review_status==='NEEDS_REVIEW' &&
    proposal.approved===false && proposal.renderable===false &&
    proposal.shop_id===draft?.shop_id &&
    Array.isArray(proposal.scenes) &&
    Array.isArray(draft.scenes) &&
    proposal.scenes.length===draft.scenes.length &&
    [15,30,60].includes(draft.duration_seconds),
    'Current original review-only proposal required');
  check(Array.isArray(approved_asset_grants) && approved_asset_grants.length<=40,
    'Invalid private asset grants');
  const grants=new Map();
  for(const grant of approved_asset_grants){
    check(grant && typeof grant.asset_id==='string' && REF.test(grant.asset_id) &&
      !grants.has(grant.asset_id) &&
      grant.shop_id===proposal.shop_id && grant.active===true &&
      grant.rights_status==='APPROVED' &&
      grant.source==='retailer_upload' &&
      grant.issued_by==='trusted_server' &&
      ['video','image'].includes(grant.media_type),
      'Foreign, revoked or forged timeline asset');
    grants.set(grant.asset_id,grant);
  }
  const scenes=[];
  const seen=new Set();
  let position=0;
  for(const edit of proposal.scenes) {
    const index=edit.source_scene_index,src=draft.scenes[index];
    check(Number.isInteger(index) && index>=0 && index<draft.scenes.length &&
      !seen.has(index) && src?.source_feature==='retailer' &&
      src.asset_type==='video' && grants.get(src.asset_id)?.media_type==='video' &&
      Number.isFinite(edit.duration) && edit.duration>=0.5 &&
      Number.isFinite(edit.trim_start) && edit.trim_start>=0 &&
      edit.mute_source===false,'Bad audio/source edit');
    seen.add(index);
    scenes.push({source_scene_index:index,asset_id:src.asset_id,
      start_ms:Math.round(position*1000),
      end_ms:Math.round((position+edit.duration)*1000),
      trim_start_ms:Math.round(edit.trim_start*1000),
      muted:false,source_audio_preserved:true});
    position+=edit.duration;
  }
  check(Math.abs(position-draft.duration_seconds)<0.001,
    'Non-contiguous approved edit time');
  const captions=[];
  const rawCaps=proposal.captions_advisory??[];
  check(Array.isArray(rawCaps) && rawCaps.length<=300,'Too many caption pages');
  for(const cap of rawCaps) {
    const sc=scenes.find(s=>s.source_scene_index===cap.source_scene_index);
    check(sc && cap.clipId===sc.asset_id &&
      Number.isInteger(cap.timeline_start_ms) &&
      Number.isInteger(cap.timeline_end_ms) &&
      cap.timeline_end_ms>cap.timeline_start_ms &&
      cap.timeline_start_ms>=sc.start_ms &&
      cap.timeline_end_ms<=sc.end_ms &&
      Array.isArray(cap.words) && cap.words.length<=7 &&
      cap.words.every(w=>typeof w.text==='string' &&
        w.text.length>0 && w.text.length<=80 &&
        !/[\u0000-\u001f\u007f<>]/.test(w.text)),
      'Caption outside scene or unsafe text');
    captions.push({scene_index:sc.source_scene_index,asset_id:sc.asset_id,
      start_ms:cap.timeline_start_ms,end_ms:cap.timeline_end_ms,
      text:cap.words.map(w=>w.text).join(' '),
      requires_review:true,feature4_renderer_ready:false});
  }
  captions.sort((a,b)=>a.start_ms-b.start_ms);
  const broll=[];
  const cues=[...(proposal.broll_advisory??[]),
    ...(proposal.owned_cutaways_advisory??[])];
  check(cues.length<=48,'Too many B-roll suggestions');
  for(const cue of cues) {
    const sc=scenes.find(s=>s.source_scene_index===cue.source_scene_index);
    const g=grants.get(cue.asset_id);
    const start=cue.timeline_start_ms??(
      Number.isFinite(cue.source_start_ms) && sc
        ?Math.round(sc.start_ms+cue.source_start_ms-sc.trim_start_ms):NaN);
    const end=cue.timeline_end_ms??(
      Number.isFinite(cue.source_end_ms) && sc
        ?Math.round(sc.start_ms+cue.source_end_ms-sc.trim_start_ms):NaN);
    check(sc && g && ['image','video'].includes(g.media_type) &&
      cue.asset_id!==sc.asset_id &&
      ['inset','top','fullscreen'].includes(cue.mode) &&
      Number.isInteger(start) && Number.isInteger(end) &&
      start>=sc.start_ms && end<=sc.end_ms && end>start,
      'B-roll cue not in eligible authorized scene');
    broll.push({source_scene_index:sc.source_scene_index,
      asset_id:cue.asset_id,start_ms:start,end_ms:end,mode:cue.mode,
      requires_review:true,feature4_renderer_ready:false});
  }
  broll.sort((a,b)=>a.start_ms-b.start_ms);
  const digest=crypto.createHash('sha256').update(JSON.stringify({
    scenes,captions,broll
  })).digest('hex');
  return Object.freeze({
    version:'feature7_review_timeline_v1',
    shop_id:proposal.shop_id,campaign_id:proposal.campaign_id,
    duration_ms:draft.duration_seconds*1000,scenes,captions,broll,
    review_sha256:digest,approved:false,renderable:false,
    original_audio_preserved:true,
    supported_edit_fields:['source_scene_index','duration','trim_start','mute_source'],
    pending_feature4_effects:['timed_captions','broll_inserts','internal_jump_cuts']
  });
}
