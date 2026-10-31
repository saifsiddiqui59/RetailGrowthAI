'use strict';
const assert=require('node:assert/strict');
const cues=require('../upstream/explainer-cues');
const {compile}=require('../director');
const {verifiedBrief,authoredCandidate}=require('./fixtures/diwali-premium-fixture');
const {captionsFromApprovedDirectorTiming}=require('../caption-preview');
const reject=fn=>assert.throws(fn,/F2_CAPTION_SOURCE_REJECTED|CREATIVE_HANDOFF_REJECTED/);
for(const duration of [15,30,60]){
  const req=verifiedBrief(duration),candidate=authoredCandidate(duration);
  const wordTimes=candidate.voiceover_script.split(/\s+/).map((text,i)=>({
    text,start:i*.15,end:(i+1)*.15,
  }));
  const bundle=compile(req,candidate,{actual_voice_alignment:{
    words:wordTimes,duration:wordTimes.length*.15,
  }});
  assert.equal(bundle.creative_direction_v1.audio_sync.state,'WORD_TIMES_MATCH_PENDING_AUDIO_PROVENANCE');
  const out=captionsFromApprovedDirectorTiming(bundle);
  assert.equal(out.duration_seconds,duration);
  assert.equal(out.source_library,'Kuble-Lab/open-creative-director/lib/explainer-cues.js');
  assert.equal(out.uses_original_upstream_layout,true);
  assert.equal(out.plan_sha256,bundle.approval_record.plan_sha256);
  assert.ok(out.subtitles.length>=1);
  assert.equal(out.source_word_count,wordTimes.length);
  assert.equal(out.can_publish,false);
  assert.equal(out.can_start_gpu,false);
  assert.equal(out.can_render,false);
  assert.equal(out.state,'WORD_TIMES_PREVIEW_PENDING_ORIGINAL_AUDIO_WAVEFORM_REVIEW');
  assert.equal(cues.spokenTokens(out.subtitles.map(x=>x.text).join(' ')).join('|'),
    cues.spokenTokens(candidate.voiceover_script).join('|'));
  let noTiming=compile(req,candidate);
  reject(()=>captionsFromApprovedDirectorTiming(noTiming));
  let changed=structuredClone(bundle);
  changed.creative_direction_v1.voiceover_script+=' BOGUS CLAIM';
  reject(()=>captionsFromApprovedDirectorTiming(changed));
  changed=structuredClone(bundle);
  changed.creative_direction_v1.audio_sync.timing.words[0].text='imposter';
  reject(()=>captionsFromApprovedDirectorTiming(changed));
  changed=structuredClone(bundle);
  changed.creative_direction_v1.audio_sync.timing.words[0].start=-3;
  reject(()=>captionsFromApprovedDirectorTiming(changed));
  changed=structuredClone(bundle);
  changed.approval_record.can_publish=true;
  reject(()=>captionsFromApprovedDirectorTiming(changed));
  console.log(JSON.stringify({duration,lines:out.subtitles.length,wordCount:out.source_word_count,upstream:'Kuble-Lab',state:'PREVIEW',gpu:'OFF'}));
}
console.log('Kuble MIT original timingOf/parseTiming/linesOf caption source reused in 15/30/60s real director acceptance PASS');
