'use strict';

// Original Kuble-Lab/Open Creative Director MIT caption-line and timing
// algorithms. NO custom caption tokenizer, subtitle layout or scene clock.
// This is a DRAFT preview, not real spoken-audio verification or a renderer.
const cues=require('./upstream/explainer-cues');
const {expectedPlanSha}=require('./handoff-approval');
const crypto=require('node:crypto');
const reject=reason=>{throw new Error('F2_CAPTION_SOURCE_REJECTED: '+reason)};
const sha=value=>crypto.createHash('sha256').update(JSON.stringify(value)).digest('hex');
function captionsFromApprovedDirectorTiming(bundle){
  if(!bundle || typeof bundle!=='object')reject('Director bundle required');
  const plan=bundle.creative_direction_v1;
  const receipt=bundle.approval_record;
  const motion=bundle.motion_direction_v1;
  if(!plan||!receipt||!Array.isArray(motion))reject('Incomplete creative source');
  const fingerprint=expectedPlanSha(bundle);
  if(fingerprint!==receipt.plan_sha256 || plan.aspect_ratio!=='9:16' ||
     ![15,30,60].includes(plan.duration_seconds))reject('Only intact source Reel plans');
  const audio=plan.audio_sync;
  if(!audio||audio.state!=='WORD_TIMES_MATCH_PENDING_AUDIO_PROVENANCE'||
     !audio.timing) reject('Real word-timestamp preview requires source-reconciled alignment');
  // parseTiming and spokenTokens are the ORIGINAL MIT upstream source,
  // reused without copying or rewriting the speech-layout algorithm.
  const parsed=cues.parseTiming(audio.timing);
  if(!parsed||!Array.isArray(parsed.words)||!parsed.words.length ||
     parsed.duration > plan.duration_seconds ||
     parsed.duration<=0)reject('Invalid original word alignment');
  const transcript=cues.spokenTokens(parsed.words.map(x=>x.text).join(' '));
  const script=cues.spokenTokens(plan.voiceover_script);
  if(JSON.stringify(transcript)!==JSON.stringify(script))
    reject('Caption transcript differs from approved Creative Director script');
  // Use upstream timingOf() to derive line breaks, not model guesses.
  const originalTiming=cues.timingOf(parsed.words,parsed.duration);
  if(!originalTiming||!Array.isArray(originalTiming.lines)||!originalTiming.lines.length)
    reject('Pinned MIT caption line builder unavailable');
  const lines=originalTiming.lines.map((line,i)=>{
    if(!Number.isFinite(line.start)||!Number.isFinite(line.end)||
       line.start<0||line.end<=line.start||line.end>plan.duration_seconds||
       typeof line.text!=='string'||!line.text.trim()||
       line.text.length>cues.LINE_CHARS+12)
      reject('Invalid timed caption line '+i);
    return {
      id:'caption-'+(i+1),
      start_seconds:line.start,end_seconds:line.end,
      text:line.text,
      role:'VOICEOVER_CAPTION_NOT_PRODUCT_CLAIM',
      audible_speech_proven:false,
    };
  });
  for(let i=1;i<lines.length;i++)
    if(lines[i].start_seconds<lines[i-1].end_seconds)reject('Overlapping caption lines');
  return {
    contract:'feature2_upstream_caption_preview_v1',
    source_library:'Kuble-Lab/open-creative-director/lib/explainer-cues.js',
    plan_sha256:fingerprint,
    caption_manifest_sha256:sha(lines),
    shop_id:plan.shop_id,campaign_id:plan.campaign_id,
    duration_seconds:plan.duration_seconds,
    source_word_count:parsed.words.length,
    subtitles:lines,
    state:'WORD_TIMES_PREVIEW_PENDING_ORIGINAL_AUDIO_WAVEFORM_REVIEW',
    uses_original_upstream_layout:true,
    can_render:false,can_publish:false,can_start_gpu:false,
  };
}
module.exports={captionsFromApprovedDirectorTiming};
