/**
 * Feature7 objective CPU speech-quality benchmark against a HUMAN reference.
 *
 * The SRT is a reference, not model inference. A good score alone NEVER
 * proves a genuine WhisperX binary, licensed weights, original speaker
 * permission, correct tenant rights or production release readiness.
 */
export class SpeechQualityError extends Error {}
const check=(v,m)=>{if(!v)throw new SpeechQualityError(m);};
const SHA=/^[a-f0-9]{64}$/;
const stamp=(t)=>{
  const m=/^(\d\d):(\d\d):(\d\d),(\d{3})$/.exec(t);
  check(m,'Invalid reference subtitle timestamp');
  const [hh,mm,ss,ms]=m.slice(1).map(Number);
  check(mm<60&&ss<60,'Invalid reference subtitle clock');
  return ((hh*60+mm)*60+ss)*1000+ms;
};
const tokens=t=>(t.toLocaleLowerCase('en').match(/[\p{L}\p{N}]+(?:['’][\p{L}\p{N}]+)*/gu)??[]);
function cuesFromSrt(text,sourceMs){
  check(typeof text==='string'&&text.length>0&&text.length<=120000,
    'Human reference subtitle required');
  const blocks=text.trim().split(/\r?\n[ \t]*\r?\n/);
  check(blocks.length>=1&&blocks.length<=500,'Invalid number of SRT cues');
  let prev=0;
  return blocks.map(block=>{
    const lines=block.trim().split(/\r?\n/);
    check(lines.length>=3&&/^\d{1,4}$/.test(lines[0].trim()),
      'Malformed subtitle cue index');
    const match=/^(\d\d:\d\d:\d\d,\d{3}) --> (\d\d:\d\d:\d\d,\d{3})$/.exec(lines[1].trim());
    check(match,'Malformed subtitle cue boundaries');
    const start=stamp(match[1]),end=stamp(match[2]);
    check(start>=prev&&end>start&&end<=sourceMs+500,
      'Out-of-order or out-of-source reference captions');
    prev=end;
    const text=lines.slice(2).join(' ').trim();
    check(text.length>0&&text.length<=1000,'Invalid human reference cue text');
    const words=tokens(text);
    check(words.length>0&&words.length<=100,'Invalid human reference text');
    return {start_ms:start,end_ms:end,words};
  });
}
function levenshtein(a,b){
  let prev=Array.from({length:b.length+1},(_,i)=>i);
  for(let i=1;i<=a.length;i++){
    const next=[i];
    for(let j=1;j<=b.length;j++)
      next[j]=Math.min(prev[j]+1,next[j-1]+1,
        prev[j-1]+(a[i-1]===b[j-1]?0:1));
    prev=next;
  }
  return prev[b.length];
}
export function evaluateSpeechAgainstReference({
  reference_srt,normalized_asr,source_duration_seconds,
  expected_source_sha256,max_word_error_rate=0.25,
  minimum_cue_coverage=0.8
}={}){
  check(Number.isFinite(source_duration_seconds)&&
    source_duration_seconds>0&&source_duration_seconds<=600&&
    typeof expected_source_sha256==='string'&&SHA.test(expected_source_sha256)&&
    normalized_asr&&normalized_asr.source_sha256===expected_source_sha256&&
    Array.isArray(normalized_asr.words)&&normalized_asr.words.length<=3000&&
    Number.isFinite(max_word_error_rate)&&
    max_word_error_rate>=0&&max_word_error_rate<=1&&
    Number.isFinite(minimum_cue_coverage)&&
    minimum_cue_coverage>=0&&minimum_cue_coverage<=1,
    'Private matched ASR/reference scope required');
  const sourceMs=Math.round(source_duration_seconds*1000);
  const cues=cuesFromSrt(reference_srt,sourceMs);
  const words=normalized_asr.words;
  let prior=-1;
  const observed=[];
  for(const w of words){
    check(w&&typeof w.word==='string'&&w.word.length<=80&&
      Number.isInteger(w.startMs)&&Number.isInteger(w.endMs)&&
      w.startMs>=0&&w.startMs>=prior-50&&w.endMs>w.startMs&&
      w.endMs<=sourceMs+1,'Bad ASR word timing');
    observed.push(...tokens(w.word));
    prior=w.endMs;
  }
  const expected=cues.flatMap(c=>c.words);
  check(expected.length>0&&expected.length<=3000,
    'Out-of-bounds human speech reference');
  const errors=levenshtein(expected,observed);
  const wer=errors/expected.length;
  const covered=cues.filter(c=>words.some(w=>
    w.startMs<=c.end_ms+350&&w.endMs>=c.start_ms-350)).length;
  const coverage=covered/cues.length;
  return Object.freeze({
    version:'feature7_cpu_speech_quality_v1',
    expected_source_sha256,
    reference_word_count:expected.length,recognized_word_count:observed.length,
    reference_cue_count:cues.length,covered_cue_count:covered,
    word_edit_distance:errors,word_error_rate:+wer.toFixed(4),
    cue_coverage_ratio:+coverage.toFixed(4),
    thresholds_passed:wer<=max_word_error_rate&&
      coverage>=minimum_cue_coverage,
    original_media_preserved:true,
    benchmark_only:true,
    actual_model_inference_proven:false,
    model_weights_license_verified:false,
    customer_release_ready:false,
    explanation:'A human SRT reference and supplied word JSON cannot prove real CPU model inference or customer rights.'
  });
}
