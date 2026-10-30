/**
 * Feature7 uploaded-footage gap-cut preview with original source coordinates.
 *
 * This is NOT Feature4's renderer, not an executable edit command, and never
 * mutes / overwrites source audio. It describes individually speech-supported
 * source ranges for a HUMAN to review; F4 currently executes only one
 * contiguous trim per original scene and must not accept these as new scenes.
 *
 * Speech words must already be source-relative, bounded and verified upstream.
 * Inspired by AutoBroll trim-silence.mjs; retains MIT attribution in sibling.
 */
import {EditValidationError, speechRuns} from './autobroll_semantics.mjs';

const requireOk = (ok,msg)=>{if(!ok)throw new EditValidationError(msg);};
const toMs = x=>Math.round(x*1000);

export function suggestGapCuts({asset_id,source_scene_index,words,
  source_duration_seconds,target_duration_seconds,
  max_removals=8}={}) {
  requireOk(typeof asset_id==='string' && /^[A-Za-z0-9_-]{1,100}$/.test(asset_id) &&
    Number.isInteger(source_scene_index) && source_scene_index>=0 &&
    Array.isArray(words) && words.length<=3000 &&
    Number.isFinite(source_duration_seconds) && source_duration_seconds>=0.5 &&
    source_duration_seconds<=600 && Number.isFinite(target_duration_seconds) &&
    target_duration_seconds>=0.5 &&
    target_duration_seconds<=source_duration_seconds &&
    Number.isInteger(max_removals) && max_removals>=0 && max_removals<=16,
  'Invalid speech-gap preview source');
  let previous = -1;
  for(const w of words){
    requireOk(w && typeof w.word==='string' && w.word.length>0 && w.word.length<=80 &&
      Number.isInteger(w.startMs) && Number.isInteger(w.endMs) &&
      w.startMs>=0 && w.startMs>=previous && w.endMs>w.startMs &&
      w.endMs<=toMs(source_duration_seconds),
    'Unordered or out-of-source speech boundary');
    previous=w.endMs;
  }
  const candidateRuns=speechRuns(words,source_duration_seconds);
  // Extend gap runs only as preview; do NOT assume every non-speech section is
  // dispensable (music, important ambience or offscreen dialogue may remain).
  const runs=[];
  for(const x of candidateRuns){
    const start=toMs(x.inSec),end=toMs(x.outSec);
    if(end<=start)continue;
    const prev=runs.at(-1);
    if(prev && start<=prev.source_end_ms){
      prev.source_end_ms=Math.max(prev.source_end_ms,end);
    } else runs.push({source_start_ms:start,source_end_ms:end});
  }
  const proposals=[];
  let removeMs=0;
  for(let i=1;i<runs.length;i++){
    const gapStart=runs[i-1].source_end_ms;
    const gapEnd=runs[i].source_start_ms;
    const diff=gapEnd-gapStart;
    // speechRuns intentionally filters tiny isolated utterances. Never treat
    // the resulting uncovered interval as silence if any original verified
    // word lies inside it: that could erase a short but critical "no".
    const containsSpeech=words.some(w=>w.startMs<gapEnd && w.endMs>gapStart);
    if(diff>=250 && !containsSpeech && proposals.length<max_removals){
      proposals.push({source_start_ms:gapStart,source_end_ms:gapEnd,
        proposed_remove_ms:diff,
        reason:'word_timing_pause_only',
        preserve_original_audio:true,requires_human_review:true,
        feature4_executable:false});
      removeMs+=diff;
    }
  }
  const speechMs=runs.reduce((s,x)=>s+x.source_end_ms-x.source_start_ms,0);
  const keepMs=Math.round(source_duration_seconds*1000)-removeMs;
  return Object.freeze({
    version:'feature7_silence_preview_v1',
    asset_id,source_scene_index,
    target_duration_ms:toMs(target_duration_seconds),
    source_duration_ms:toMs(source_duration_seconds),
    detected_speech_ranges:runs,
    removable_gap_candidates:proposals,
    potential_removed_ms:removeMs,
    remaining_if_all_candidates_removed_ms:keepMs,
    speech_supported_ms:speechMs,
    sufficient_to_fill_target:keepMs>=toMs(target_duration_seconds),
    advisory_only:true,approved:false,feature4_executable:false,
    human_must_review_original_audio:true,
    no_auto_deletion:true
  });
}
