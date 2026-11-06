/**
 * Versioned REVIEW-ONLY Feature7->Feature4 speech-edit evidence bundle.
 * Combines already implemented MIT AutoClip Core cuts, AutoBroll captions,
 * Feature7 speech/music guidance, and real decoded-media QA.
 *
 * No second editor, no render, authorization, media URL, license, approval,
 * provider call or permission to assume a browser snapshot is trusted.
 * Feature4 must validate live RLS rights and issue an approved F4 contract.
 */
import crypto from 'node:crypto';
import {EditValidationError} from './autobroll_semantics.mjs';

const check=(ok,message)=>{if(!ok)throw new EditValidationError(message);};
const ID=/^[A-Za-z0-9_-]{1,120}$/;
const SHA=/^[a-f0-9]{64}$/;
const round=(x)=>Math.round(x*1000);
// Keep signed review-only evidence immutable after its digest is computed.
const freezeReviewPacket=(packet)=>{
  for(const key of ['source_keep_segments','caption_projection',
    'caption_track','music_duck_intervals']){
    packet[key].forEach(row=>Object.freeze(row));
    Object.freeze(packet[key]);
  }
  Object.freeze(packet.objective_qa_faults);
  return Object.freeze(packet);
};
export function createFeature4SpeechReviewHandoff({
  shop_id,asset_id,original_source_sha256,preview_sha256,
  autoclip_plan,caption_projection,music_handoff,decoded_quality
}={}){
  check(typeof shop_id==='string'&&ID.test(shop_id)&&
    typeof asset_id==='string'&&ID.test(asset_id)&&
    typeof original_source_sha256==='string'&&SHA.test(original_source_sha256)&&
    typeof preview_sha256==='string'&&SHA.test(preview_sha256)&&
    original_source_sha256!==preview_sha256,
    'Trusted source and unique rendered-preview hashes required');
  const plan=autoclip_plan,cap=caption_projection,music=music_handoff,qa=decoded_quality;
  check(plan&&plan.engine==='branmendo/autoclip-core'&&
    plan.engine_license==='MIT'&&
    plan.source_sha256===original_source_sha256&&
    plan.human_review_required===true&&plan.approved===false&&
    plan.renderable===false&&
    Array.isArray(plan.keep_segments)&&plan.keep_segments.length>=2&&
    plan.keep_segments.length<=32&&
    Number.isFinite(plan.source_duration_seconds)&&
    plan.source_duration_seconds>0&&plan.source_duration_seconds<=600,
    'Unapproved genuine AutoClip cut evidence required');
  check(cap&&cap.version==='feature7_autoclip_autobroll_caption_projection_v1'&&
    cap.shop_id===shop_id&&cap.asset_id===asset_id&&
    cap.approved===false&&cap.renderable===false&&
    cap.human_review_required===true&&
    cap.requires_rendered_av_acceptance===true&&
    Array.isArray(cap.keep_projection)&&
    cap.keep_projection.length===plan.keep_segments.length&&
    Array.isArray(cap.feature4_caption_track)&&
    cap.feature4_caption_track.length>0&&
    [15,30,60].includes(cap.requested_reel_seconds)&&
    Number.isInteger(cap.actual_timeline_duration_ms)&&
    cap.actual_timeline_duration_ms>0,
    'Feature7 current AutoBroll caption/clock evidence required');
  let current=0,priorEnd=-1;
  for(let i=0;i<plan.keep_segments.length;i++){
    const p=plan.keep_segments[i],m=cap.keep_projection[i];
    check(Number.isFinite(p?.start)&&Number.isFinite(p?.end)&&
      p.start>=0&&p.start>=priorEnd&&p.end>p.start&&
      p.end<=plan.source_duration_seconds+.01&&
      m?.source_start_ms===round(p.start)&&
      m?.source_end_ms===round(p.end)&&
      Number.isInteger(m.visible_source_start_ms)&&
      Number.isInteger(m.visible_source_end_ms)&&
      m.visible_source_start_ms>=m.source_start_ms&&
      m.visible_source_start_ms<m.visible_source_end_ms&&
      m.visible_source_end_ms<=m.source_end_ms&&
      m.timeline_start_ms===current&&
      m.timeline_end_ms===current+
        (m.visible_source_end_ms-m.visible_source_start_ms),
      'Invalid nonlinear cut/word clock mapping');
    priorEnd=p.end;current=m.timeline_end_ms;
  }
  check(current===cap.actual_timeline_duration_ms&&
    current<=cap.requested_reel_seconds*1000+2500&&
    music&&music.version==='feature7_music_ducking_handoff_v1'&&
    music.shop_id===shop_id&&music.asset_id===asset_id&&
    music.source_sha256===original_source_sha256&&
    music.timeline_duration_ms===current&&
    music.original_dialogue_gain_db===0&&
    music.voice_preservation_required===true&&
    music.feature4_mixer_execution_required===true&&
    music.approved===false&&music.renderable===false&&
    Number.isInteger(music.recommended_music_gain_db)&&
    music.recommended_music_gain_db>=-24&&
    music.recommended_music_gain_db<=-8&&
    Array.isArray(music.music_duck_intervals)&&
    music.music_duck_intervals.length<=100&&
    qa&&qa.version==='feature7_decoded_quality_v1'&&
    qa.source_sha256===preview_sha256&&
    qa.real_decoding_performed===true&&qa.source_bytes_unchanged===true&&
    qa.commercial_quality_accepted===false&&qa.approved===false&&
    qa.customer_publishable===false&&
    Array.isArray(qa.faults)&&qa.faults.length<=20&&
    Math.abs(qa.duration_seconds*1000-current)<=250,
    'Real preview quality / dialogue handoff mismatch');
  let lastDuck=0;
  for(const cue of music.music_duck_intervals){
    check(cue&&Number.isInteger(cue.start_ms)&&
      Number.isInteger(cue.end_ms)&&
      cue.start_ms>=lastDuck&&
      cue.end_ms>cue.start_ms&&cue.end_ms<=current,
      'Invalid, overlapping or out-of-bounds music/voice automation');
    lastDuck=cue.end_ms;
  }
  check(qa.faults.every(f=>typeof f==='string'&&
    /^[A-Z0-9_]{1,80}$/.test(f)),
    'Untrusted media QA fault text');
  let last=0;
  for(const cue of cap.feature4_caption_track){
    check(cue&&typeof cue.text==='string'&&cue.text.length>0&&
      cue.text.length<=90&&!/[<>\u0000-\u001f\u007f]/.test(cue.text)&&
      Number.isFinite(cue.start)&&Number.isFinite(cue.duration)&&
      cue.start>=last&&cue.duration>=.2&&
      (cue.start+cue.duration)*1000<=current+1,
      'Out-of-order speech caption');
    last=cue.start+cue.duration;
  }
  const envelope={
    version:'feature7_feature4_speech_review_bundle_v1',
    shop_id,asset_id,original_source_sha256,preview_sha256,
    rendered_preview_duration_ms:current,
    source_keep_segments:plan.keep_segments.map(p=>({...p})),
    caption_projection:cap.keep_projection.map(p=>({...p})),
    caption_track:cap.feature4_caption_track.map(c=>({...c})),
    music_duck_intervals:music.music_duck_intervals.map(c=>({...c})),
    original_dialogue_gain_db:0,
    recommended_music_gain_db:music.recommended_music_gain_db,
    objective_qa_faults:[...qa.faults],
    objective_qa_passed:qa.objective_checks_passed===true&&qa.faults.length===0,
    upstream_cut_engine:'branmendo/autoclip-core',
    upstream_caption_engine:'andriidrok1/autobroll',
    full_feature4_multi_cut_contract_implemented:false,
    transcription_model_accuracy_verified:false,
    human_creative_acceptance_verified:false,
    video_rights_currently_verified_by_backend:false,
    separately_persisted_approval_required:true,
    human_review_required:true,
    approved:false,renderable:false,customer_publishable:false
  };
  const canonical=JSON.stringify(envelope);
  return freezeReviewPacket({...envelope,
    review_payload_sha256:crypto.createHash('sha256').update(canonical).digest('hex')});
}
