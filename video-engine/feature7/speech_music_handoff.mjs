/**
 * Feature7 speech-aware MUSIC DUCKING ADVISORY for existing Feature4 mixer.
 *
 * No audio edit, license, soundtrack, model inference, or self-approval.
 * Source words are assumed independently signed/verified by the trusted
 * ASR worker. This advice must be human-reviewed; Feature4 owns final music.
 * Map through the existing AutoClip keep_projection, never infer that
 * FFmpeg non-silence is spoken words. Original dialogue gain remains 0dB.
 */
import {EditValidationError} from './autobroll_semantics.mjs';
const check=(v,m)=>{if(!v)throw new EditValidationError(m);};
const REF=/^[A-Za-z0-9_-]{1,120}$/;
const SHA=/^[a-f0-9]{64}$/;
// Speech text is later shown to reviewers; reject display-control spoofing
// and malformed UTF-16 even when no renderer is invoked here.
const UNSAFE_WORD=/[\u0000-\u001f\u007f-\u009f\u202a-\u202e\u2066-\u2069\ufeff]/u;
const UNPAIRED_SURROGATE=/[\ud800-\udbff](?![\udc00-\udfff])|(?<![\ud800-\udbff])[\udc00-\udfff]/u;

export function suggestSpeechMusicDucking({
  shop_id,asset_id,source_sha256,words,keep_projection,
  actual_timeline_duration_ms,lead_ms=120,release_ms=180,
  music_gain_db=-16
}={}){
  check(typeof shop_id==='string'&&REF.test(shop_id)&&
    typeof asset_id==='string'&&REF.test(asset_id)&&
    typeof source_sha256==='string'&&SHA.test(source_sha256)&&
    Array.isArray(words)&&words.length>0&&words.length<=3000&&
    Array.isArray(keep_projection)&&keep_projection.length>0&&
    keep_projection.length<=32&&
    Number.isSafeInteger(actual_timeline_duration_ms)&&
    actual_timeline_duration_ms>=500&&actual_timeline_duration_ms<=600000&&
    Number.isInteger(lead_ms)&&lead_ms>=0&&lead_ms<=500&&
    Number.isInteger(release_ms)&&release_ms>=0&&release_ms<=750&&
    Number.isInteger(music_gain_db)&&
    music_gain_db<=-8&&music_gain_db>=-24,
  'Bounded signed speech words and AutoClip clock required');
  let wordEnd=-1;
  for(const w of words){
    check(w&&typeof w.word==='string'&&w.word.trim().length>0&&
      [...w.word.trim()].length<=80&&
      !UNSAFE_WORD.test(w.word)&&!UNPAIRED_SURROGATE.test(w.word)&&
      Number.isSafeInteger(w.startMs)&&Number.isSafeInteger(w.endMs)&&
      w.startMs>=wordEnd-50&&w.endMs>w.startMs&&
      w.startMs>=0&&w.endMs<=600000,
    'Untrusted or unsorted speech times');
    wordEnd=w.endMs;
  }
  let priorSource=-1,priorTimeline=0;
  const active=[];
  for(const segment of keep_projection){
    const a=segment?.visible_source_start_ms;
    const b=segment?.visible_source_end_ms;
    const t=segment?.timeline_start_ms;
    const end=segment?.timeline_end_ms;
    check([a,b,t,end].every(Number.isSafeInteger)&&
      a>=0&&b>a&&b<=600000&&a>=priorSource&&
      t===priorTimeline&&end>t&&
      end-t===b-a&&end<=actual_timeline_duration_ms,
    'Invalid AutoClip video/audio crossfade projection');
    for(const w of words){
      if(w.startMs<a||w.endMs>b)continue;
      active.push({
        start_ms:Math.max(0,t+(w.startMs-a)-lead_ms),
        end_ms:Math.min(actual_timeline_duration_ms,t+(w.endMs-a)+release_ms)
      });
    }
    priorSource=b;
    priorTimeline=end;
  }
  check(priorTimeline===actual_timeline_duration_ms &&
    active.length>0,'Verified spoken words must survive cuts');
  active.sort((a,b)=>a.start_ms-b.start_ms);
  const groups=[];
  for(const clip of active){
    const last=groups.at(-1);
    if(last&&clip.start_ms-last.end_ms<=150){
      last.end_ms=Math.max(last.end_ms,clip.end_ms);
    }else groups.push({...clip});
    check(groups.length<=100,'Excess music automation cues');
  }
  return Object.freeze({
    version:'feature7_music_ducking_handoff_v1',
    shop_id,asset_id,source_sha256,
    timeline_duration_ms:actual_timeline_duration_ms,
    original_dialogue_gain_db:0,
    voice_preservation_required:true,
    recommended_music_gain_db:music_gain_db,
    music_duck_intervals:groups,
    human_review_required:true,
    feature4_mixer_execution_required:true,
    licensed_music_supplied:false,
    independent_asr_signature_verified_here:false,
    approved:false,renderable:false,production_mix_performed:false
  });
}
