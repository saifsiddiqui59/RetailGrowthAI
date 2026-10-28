/**
 * Feature7 upstream-based caption projection AFTER real source cuts.
 *
 * Reuses AutoBroll buildCaptions (MIT upstream captions-multiclip.mjs) for
 * phrase grouping; only remaps its source-timed words onto AutoClip Core
 * (MIT) keep spans. Does not implement another caption generator, TTS,
 * F4 overlay renderer, JWT approval or model inference.
 */
import {buildCaptions,EditValidationError} from './autobroll_semantics.mjs';

const check=(ok,msg)=>{if(!ok)throw new EditValidationError(msg);};
const REF=/^[\w-]{1,120}$/;
export function projectUpstreamCaptionsAfterAutoClipCuts({
  shop_id,asset_id,words,keep_segments,source_duration_seconds,
  requested_reel_seconds=15,audio_crossfade_seconds=0.03
}={}){
  check(typeof shop_id==='string'&&REF.test(shop_id)&&
    typeof asset_id==='string'&&REF.test(asset_id)&&
    Array.isArray(words)&&words.length>0&&words.length<=3000&&
    Array.isArray(keep_segments)&&keep_segments.length>=1&&
    keep_segments.length<=32&&
    Number.isFinite(source_duration_seconds)&&
    source_duration_seconds>=.5&&source_duration_seconds<=600&&
    [15,30,60].includes(requested_reel_seconds)&&
    Number.isFinite(audio_crossfade_seconds)&&
    audio_crossfade_seconds>=0&&audio_crossfade_seconds<=0.25&&
    Math.abs(audio_crossfade_seconds*1000-
      Math.round(audio_crossfade_seconds*1000))<1e-6,
  'Valid scoped source, transcript and original reel required');
  let previousEnd=-1;
  for(const w of words){
    check(w&&typeof w.word==='string'&&w.word.length>0&&w.word.length<=80&&
      !/[\u0000-\u001f\u007f<>]/.test(w.word)&&
      Number.isInteger(w.startMs)&&Number.isInteger(w.endMs)&&
      w.startMs>=0&&w.startMs>=previousEnd-50&&
      w.endMs>w.startMs&&w.endMs<=source_duration_seconds*1000+1,
      'Unsafe/misaligned source speech');
    previousEnd=w.endMs;
  }
  // AutoClip Core compose.py audio acrossfade(d) shortens every joined
  // timeline by d and trims d/2 of video on each side of the join.
  // Project only fully visible retained words; never caption removed speech.
  // The source must use the SAME crossfade setting when rendering preview.
  const shortestMs=Math.min(...keep_segments.map(k=>
    Number.isFinite(k?.start)&&Number.isFinite(k?.end)?
      (k.end-k.start)*1000:NaN));
  const fadeMs=keep_segments.length<2?0:Math.min(
    Math.round(audio_crossfade_seconds*1000),Math.floor(shortestMs/2));
  check(Number.isFinite(fadeMs)&&fadeMs>=0,'Invalid upstream fade');
  let position=0,priorSourceEnd=0;
  const cues=[],keepProjection=[];
  for(const [index,entry] of keep_segments.entries()){
    const a=entry?.start,b=entry?.end;
    check(Number.isFinite(a)&&Number.isFinite(b)&&
      a>=priorSourceEnd&&b>a&&b<=source_duration_seconds+.01&&
      b-a>=.35,'Disordered/invalid upstream keep span');
    const from=Math.round(a*1000),to=Math.round(b*1000);
    const visibleFrom=from+(index>0?fadeMs/2:0);
    const visibleTo=to-(index<keep_segments.length-1?fadeMs/2:0);
    check(visibleTo-visibleFrom>=200,'Crossfade erased retained segment');
    const frameStart=position;
    const inside=words.filter(w=>
      w.startMs>=visibleFrom&&w.endMs<=visibleTo);
    // Upstream captions are built ONLY for actually kept speech words.
    // A cut word is not hallucinated as a full spoken word.
    const groups=buildCaptions(inside,asset_id);
    for(const page of groups){
      const start=Math.round(position+(page.startMs-visibleFrom));
      const finish=Math.round(position+(page.endMs-visibleFrom));
      const text=page.words.map(w=>w.text).join(' ').trim();
      check(text.length>0&&text.length<=90&&
        start>=frameStart&&finish<=frameStart+visibleTo-visibleFrom&&finish>start,
        'Caption outside verified retained media');
      if(finish-start<200)continue; // F4 caption track minimum .2s
      if(cues.length)check(start>=cues.at(-1).end_ms,
        'Overlapping caption after nonlinear edit');
      cues.push({
        start:+(start/1000).toFixed(3),
        duration:+((finish-start)/1000).toFixed(3),
        text,
        start_ms:start,end_ms:finish,
        original_source_asset_id:asset_id,
        original_source_start_ms:page.startMs,
        original_source_end_ms:page.endMs,
        derived_from:'AUTOBROLL_REAL_SOURCE_WORDS',
        requires_human_review:true
      });
    }
    keepProjection.push({
      source_start_ms:from,source_end_ms:to,
      visible_source_start_ms:visibleFrom,
      visible_source_end_ms:visibleTo,
      timeline_start_ms:Math.round(frameStart),
      timeline_end_ms:Math.round(frameStart+visibleTo-visibleFrom)
    });
    position+=visibleTo-visibleFrom;
    priorSourceEnd=b;
  }
  check(cues.length>0&&cues.length<=60&&
    position<=requested_reel_seconds*1000+2500,
    'Excess or missing edit caption scope');
  return Object.freeze({
    version:'feature7_autoclip_autobroll_caption_projection_v1',
    shop_id,asset_id,requested_reel_seconds,
    actual_timeline_duration_ms:Math.round(position),
    applied_audio_crossfade_seconds:fadeMs/1000,
    timing_basis:'AUTOCLIP_CORE_AUDIO_CROSSFADE_AND_VIDEO_HALF_TRIM',
    measured_frame_level_sync:false,
    requires_rendered_av_acceptance:true,
    matches_feature4_duration_exactly:
      Math.abs(position-requested_reel_seconds*1000)<=20,
    upstream_caption_project:'andriidrok1/autobroll',
    upstream_cut_project:'branmendo/autoclip-core',
    keep_projection:keepProjection,
    captions:cues,
    // The exact F4 component fields; F4 must separately validate the
    // *approved* target duration, submitted on a trusted server.
    feature4_caption_track:cues.map(c=>({
      start:c.start,duration:c.duration,text:c.text
    })),
    approved:false,renderable:false,
    original_speech_preserved_except_reviewed_cut_regions:true,
    captions_from_real_model_inference_proven:false,
    production_signed_media_ready:false,
    human_review_required:true
  });
}
