/**
 * Feature7 human caption correction proposals; NOT independent ASR, F4 editor
 * or production approval. A signed-in reviewer may propose TEXT changes to
 * existing word-timed AutoBroll cues; no cue can be added/moved or made executable.
 * A trusted host must reload the current tenant, rights, source bytes, revision,
 * and human approval in its database transaction before Feature4 renders.
 */
import crypto from 'node:crypto';
import {EditValidationError} from './autobroll_semantics.mjs';

const valid=(ok,msg)=>{if(!ok)throw new EditValidationError(msg);};
const ID=/^[A-Za-z0-9_-]{1,120}$/;
const SHA=/^[a-f0-9]{64}$/;
const hash=s=>crypto.createHash('sha256').update(s,'utf8').digest('hex');
// Deliberately fail closed on HTML, invisible direction changes, bidi isolates,
// zero-width controls, newlines, and ffmpeg/ASS markup metacharacters.
export function validateReviewerCaptionText(raw){
  valid(typeof raw==='string'&&raw.length>=1&&raw.length<=160,
    'Bounded human correction text required');
  const text=raw.normalize('NFC').trim().replace(/[ \t]+/gu,' ');
  valid(text.length>=1&&text.length<=90&&
    !/[\u0000-\u001f\u007f-\u009f\u200b-\u200f\u202a-\u202e\u2060-\u2069<>&\\{}]/u.test(text)&&
    !/[\r\n]/u.test(text)&&
    text.split(' ').length<=16,
    'Unsafe, invisible or excessive caption correction');
  return text;
}
export function createCaptionCorrectionSession({
  shop_id,asset_id,source_sha256,preview_sha256,
  caption_projection,reviewer_view
}={}){
  valid(typeof shop_id==='string'&&ID.test(shop_id)&&
    typeof asset_id==='string'&&ID.test(asset_id)&&
    typeof source_sha256==='string'&&SHA.test(source_sha256)&&
    typeof preview_sha256==='string'&&SHA.test(preview_sha256)&&
    source_sha256!==preview_sha256,
    'Scoped original-media and preview evidence required');
  valid(reviewer_view&&reviewer_view.shop_id===shop_id&&
    ID.test(reviewer_view.reviewer_id??'')&&
    reviewer_view.active_membership===true&&
    ['OWNER','EDITOR','VIEWER'].includes(reviewer_view.role)&&
    Number.isSafeInteger(reviewer_view.revision)&&reviewer_view.revision>=0,
    'Current reviewer identity/scope required');
  valid(caption_projection&&caption_projection.version===
    'feature7_autoclip_autobroll_caption_projection_v1'&&
    caption_projection.shop_id===shop_id&&
    caption_projection.asset_id===asset_id&&
    caption_projection.approved===false&&
    caption_projection.renderable===false&&
    caption_projection.human_review_required===true&&
    Number.isInteger(caption_projection.actual_timeline_duration_ms)&&
    caption_projection.actual_timeline_duration_ms>0&&
    caption_projection.actual_timeline_duration_ms<=600000&&
    Array.isArray(caption_projection.feature4_caption_track)&&
    caption_projection.feature4_caption_track.length>0&&
    caption_projection.feature4_caption_track.length<=60,
    'Current review-only AutoBroll caption projection required');
  let lastEnd=0;
  const cues=caption_projection.feature4_caption_track.map((cue,index)=>{
    valid(cue&&Object.keys(cue).length===3&&
      Object.hasOwn(cue,'text')&&Object.hasOwn(cue,'start')&&
      Object.hasOwn(cue,'duration')&&
      typeof cue.start==='number'&&Number.isFinite(cue.start)&&
      typeof cue.duration==='number'&&Number.isFinite(cue.duration),
      'Unexpected cue field/clock');
    const startMs=Math.round(cue.start*1000);
    const endMs=Math.round((cue.start+cue.duration)*1000);
    valid(startMs>=lastEnd&&endMs>startMs&&
      endMs-startMs>=200&&
      endMs<=caption_projection.actual_timeline_duration_ms+1,
      'Overlapping or unbounded timed human caption cue');
    const text=validateReviewerCaptionText(cue.text);
    lastEnd=endMs;
    return Object.freeze({index,start_ms:startMs,end_ms:endMs,text,
      original_text_sha256:hash(text)});
  });
  const clockSha=hash(JSON.stringify(cues.map(c=>[c.start_ms,c.end_ms,c.original_text_sha256])));
  return Object.freeze({
    version:'feature7_caption_review_session_v1',
    shop_id,asset_id,source_sha256,preview_sha256,
    reviewer_id:reviewer_view.reviewer_id,
    expected_revision:reviewer_view.revision,
    can_propose:reviewer_view.role!=='VIEWER',
    source_captions_sha256:clockSha,
    actual_timeline_duration_ms:caption_projection.actual_timeline_duration_ms,
    cues:Object.freeze(cues),
    corrections:Object.freeze([]),
    human_review_required:true,approved:false,renderable:false
  });
}
export function editCaptionCorrection(session,cue_index,new_text){
  valid(session?.version==='feature7_caption_review_session_v1'&&
    session.can_propose===true&&Array.isArray(session.cues)&&
    Number.isInteger(cue_index)&&cue_index>=0&&cue_index<session.cues.length,
    'Only an active authorized reviewer can correct an existing cue');
  const normalized=validateReviewerCaptionText(new_text);
  const cue=session.cues[cue_index];
  const revised=session.corrections.filter(c=>c.cue_index!==cue_index);
  if(normalized!==cue.text){
    revised.push(Object.freeze({
      cue_index,
      start_ms:cue.start_ms,end_ms:cue.end_ms,
      original_text_sha256:cue.original_text_sha256,
      corrected_text:normalized
    }));
  }
  valid(revised.length<=session.cues.length,'Too many caption corrections');
  revised.sort((a,b)=>a.cue_index-b.cue_index);
  return Object.freeze({...session,corrections:Object.freeze(revised),
    approved:false,renderable:false});
}
export function requestCaptionCorrectionReview(session,{confirmed=false}={}){
  valid(session?.version==='feature7_caption_review_session_v1'&&
    session.can_propose===true&&
    confirmed===true&&Array.isArray(session.corrections)&&
    session.corrections.length>=1,
    'Explicit human confirmed corrected captions required');
  // Packet NEVER returns approval, a signed media URL or an executable edit.
  const packet={
    version:'feature7_caption_correction_request_v1',
    shop_id:session.shop_id,asset_id:session.asset_id,
    reviewer_id:session.reviewer_id,
    expected_revision:session.expected_revision,
    source_sha256:session.source_sha256,
    preview_sha256:session.preview_sha256,
    source_captions_sha256:session.source_captions_sha256,
    timeline_duration_ms:session.actual_timeline_duration_ms,
    corrections:session.corrections.map(c=>({...c})),
    reviewer_confirmation:true,
    source_word_times_preserved:true,
    unmodified_original_audio_required:true,
    requires_current_backend_rights:true,
    requires_authoritative_server_transaction:true,
    external_model_wer_passed_here:false,
    approved:false,renderable:false,customer_publishable:false
  };
  const packetHash=hash(JSON.stringify(packet));
  // Snapshot each correction BEFORE handing an asynchronous host callback its
  // digest-bound packet. Freezing only the array would leave row text mutable.
  const corrections=Object.freeze(
    packet.corrections.map(row=>Object.freeze({...row})));
  return Object.freeze({...packet,corrections,
    request_sha256_hint:packetHash});
}


/**
 * Corrected caption *preview* using existing AutoBroll cue timing and F7
 * FFmpeg/libass caption overlay. It changes text only; original transcript,
 * recorded audio, keep segments, and trusted media source are untouched.
 * This result CANNOT flow into an executable Feature4 render contract.
 */
export function buildCorrectedCaptionReviewProjection(session,originalProjection){
  valid(session?.version==='feature7_caption_review_session_v1'&&
    Array.isArray(session.corrections)&&session.corrections.length>0&&
    originalProjection?.version===
      'feature7_autoclip_autobroll_caption_projection_v1'&&
    originalProjection.approved===false&&
    originalProjection.renderable===false&&
    originalProjection.human_review_required===true&&
    originalProjection.shop_id===session.shop_id&&
    originalProjection.asset_id===session.asset_id&&
    originalProjection.actual_timeline_duration_ms===
      session.actual_timeline_duration_ms&&
    Array.isArray(originalProjection.feature4_caption_track)&&
    originalProjection.feature4_caption_track.length===session.cues.length,
    'Unmodified source caption clock required for preview');
  const unchanged=originalProjection.feature4_caption_track;
  let lastEnd=0;
  const verified=unchanged.map((cue,index)=>{
    const saved=session.cues[index];
    valid(cue&&saved&&
      Math.round(cue.start*1000)===saved.start_ms&&
      Math.round((cue.start+cue.duration)*1000)===saved.end_ms&&
      hash(validateReviewerCaptionText(cue.text))===saved.original_text_sha256&&
      saved.start_ms>=lastEnd,'Source original captions changed');
    lastEnd=saved.end_ms;
    return [saved.start_ms,saved.end_ms,saved.original_text_sha256];
  });
  valid(hash(JSON.stringify(verified))===session.source_captions_sha256,
    'Stale caption revision cannot be previewed');
  const byId=new Map();
  for(const c of session.corrections){
    const original=session.cues[c?.cue_index];
    valid(original&&original.original_text_sha256===c.original_text_sha256&&
      original.start_ms===c.start_ms&&original.end_ms===c.end_ms&&
      !byId.has(c.cue_index),
      'Foreign or duplicate text correction');
    byId.set(c.cue_index,validateReviewerCaptionText(c.corrected_text));
  }
  // Both arrays are read by an asynchronous offline caption-preview worker.
  // Freeze ROWS as well as the arrays, and project only caption clock/text
  // fields: an extra source cue property must never become renderer metadata.
  // This copies caller cues rather than freezing trusted host input in place.
  const changed=Object.freeze(unchanged.map((cue,i)=>Object.freeze({
    start:cue.start,duration:cue.duration,text:byId.get(i)??cue.text
  })));
  const originalClock=Object.freeze(unchanged.map(cue=>Object.freeze({
    start:cue.start,duration:cue.duration,text:cue.text
  })));
  return Object.freeze({...originalProjection,
    feature4_caption_track:changed,
    original_caption_track_unchanged:originalClock,
    caption_correction_source_sha256:session.source_captions_sha256,
    caption_correction_count:byId.size,
    human_caption_correction_preview_only:true,
    human_speech_word_verification_completed:false,
    original_audio_preservation_required:true,
    approved:false,renderable:false,human_review_required:true
  });
}


/**
 * Verify a client correction against a newly fetched trusted source snapshot.
 * This is only source-level data verification: a production API still MUST
 * derive reviewer_view via JWT/RLS, lock the authoritative media registry,
 * persist a human action and fence the Feature4 dispatch transaction.
 * Neither a JS digest nor a reviewer_view object supplied by a browser
 * confers those rights.
 */
export function verifyCaptionCorrectionRequestForWorker({
  request,original_projection,shop_id,asset_id,
  source_sha256,preview_sha256,reviewer_view
}={}){
  valid(request&&typeof request==='object'&&!Array.isArray(request)&&
    request.version==='feature7_caption_correction_request_v1'&&
    request.reviewer_confirmation===true&&
    request.approved===false&&request.renderable===false&&
    request.customer_publishable===false&&
    Array.isArray(request.corrections)&&
    request.corrections.length>=1&&request.corrections.length<=60,
    'Unapproved confirmed text-only correction request required');
  // The reviewer_view and projection MUST come from the trusted backend,
  // not from request.body. Reconstruct the exact original cue revision.
  let session=createCaptionCorrectionSession({
    shop_id,asset_id,source_sha256,preview_sha256,
    caption_projection:original_projection,reviewer_view
  });
  valid(session.can_propose,'VIEWER may not correct captions');
  const seen=new Set();
  for(const correction of request.corrections){
    const i=correction?.cue_index;
    valid(Number.isInteger(i)&&i>=0&&i<session.cues.length&&
      !seen.has(i),'Unknown, repeated or foreign caption edit');
    seen.add(i);
    session=editCaptionCorrection(session,i,correction.corrected_text);
  }
  const rebuilt=requestCaptionCorrectionReview(session,{confirmed:true});
  // Exact canonical packet values, not the user-supplied hint, define the
  // original source revision and correction candidate.
  valid(request.request_sha256_hint===rebuilt.request_sha256_hint&&
    Object.keys(request).length===Object.keys(rebuilt).length,
    'Stale or forged caption request digest');
  for(const [key,value] of Object.entries(rebuilt)){
    valid(JSON.stringify(request[key])===JSON.stringify(value),
      'Caption request fields changed since source verification');
  }
  return Object.freeze({
    candidate_sha256:rebuilt.request_sha256_hint,
    shop_id,asset_id,source_sha256,preview_sha256,
    expected_revision:reviewer_view.revision,
    source_captions_sha256:session.source_captions_sha256,
    verified_correction_count:session.corrections.length,
    current_snapshot_consistency_checked:true,
    authenticated_jwt_rls_verified_here:false,
    persisted_human_approval_here:false,
    requires_authoritative_server_transaction:true,
    approved:false,renderable:false,customer_publishable:false
  });
}
