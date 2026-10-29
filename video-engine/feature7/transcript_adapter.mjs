/**
 * Trusted-offline adapter for a supplied WhisperX JSON transcript.
 *
 * Adapted from AutoBroll scripts/lib-transcribe.mjs parseWhisperxJson,
 * with fail-closed timing rather than guessing from missing word boundaries.
 * No model download, subprocess, API, transcript persistence or new renderer.
 */
import crypto from 'node:crypto';

export class TranscriptAdaptationError extends Error {}
const check=(ok,msg)=>{if(!ok) throw new TranscriptAdaptationError(msg);};
const SHA=/^[0-9a-f]{64}$/;

export function normalizeWhisperx({asset_id,shop_id,source_sha256,transcript,
  source_duration_seconds}={}) {
  check(typeof asset_id==='string' && asset_id.length>0 &&
    typeof shop_id==='string' && shop_id.length>0 && SHA.test(source_sha256??'') &&
    Number.isFinite(source_duration_seconds) && source_duration_seconds>0 &&
    source_duration_seconds<=600, 'Missing verified media binding');
  check(transcript && typeof transcript==='object' &&
    Array.isArray(transcript.segments) && transcript.segments.length<=500,
    'Invalid supplied WhisperX transcript');
  const raw=transcript.segments.flatMap(s=>{
    check(s && Array.isArray(s.words) && s.words.length<=200,
      'Invalid ASR segment words');
    return s.words;
  });
  check(raw.length<=3000,'Transcript too large');
  // Preserve authentic Unicode speech (including Devanagari combining marks)
  // without accepting controls or bidirectional formatting injection.
  const forbidden=/[\u0000-\u001f\u007f-\u009f\u202a-\u202e\u2066-\u2069\ufeff]/u;
  const words=[];
  let previousEnd=-1;
  for(const w of raw) {
    check(w && typeof w.word==='string' && w.word.trim().length>0 &&
      [...w.word.trim()].length<=80 && !forbidden.test(w.word) &&
      !/[\ud800-\udbff](?![\udc00-\udfff])|(?<![\ud800-\udbff])[\udc00-\udfff]/u.test(w.word) && typeof w.start==='number' &&
      typeof w.end==='number' && Number.isFinite(w.start) && Number.isFinite(w.end) &&
      w.start>=0 && w.start>=previousEnd-0.05 && w.end>w.start &&
      w.end<=source_duration_seconds+0.001,'Invalid or missing WhisperX word timing');
    // Timestamps are rounded to milliseconds to match AutoBroll semantics.
    const startMs=Math.round(w.start*1000),endMs=Math.round(w.end*1000);
    check(endMs>startMs,'ASR word shorter than one millisecond');
    words.push({word:w.word.trim(),startMs,endMs});
    previousEnd=w.end;
  }
  const digest=crypto.createHash('sha256').update(JSON.stringify(words)).digest('hex');
  // "verified_server" means only that THIS parser validated the supplied shape;
  // worker must bind source_sha256 to checked private bytes and lock transcript.
  return Object.freeze({
    asset_id,shop_id,source_sha256,transcript_sha256:digest,
    transcription_status:'verified_server',words,
    source_duration_seconds,source:'whisperx_supplied_json',
    paid_model_calls:0,privacy:'PRIVATE_LOCAL_WORKER_ONLY'
  });
}

export function projectCaptionsToTrim(captions, trim_start_seconds, duration_seconds, timeline_offset_seconds=0) {
  check(Array.isArray(captions) && Number.isFinite(trim_start_seconds) &&
    trim_start_seconds>=0 && Number.isFinite(duration_seconds) &&
    duration_seconds>0 && Number.isFinite(timeline_offset_seconds) &&
    timeline_offset_seconds>=0, 'Invalid caption clip projection');
  const start=trim_start_seconds*1000,end=start+duration_seconds*1000;
  return captions.filter(c=>c.endMs>start && c.startMs<end).map(c=>{
    check(c && typeof c.clipId==='string' && Array.isArray(c.words) &&
      Number.isFinite(c.startMs) && Number.isFinite(c.endMs) &&
      c.startMs<c.endMs, 'Invalid caption source timing');
    const clippedWords=c.words.filter(w=>w.endMs>start && w.startMs<end).map(w=>({
      ...w,startMs:Math.round(timeline_offset_seconds*1000+Math.max(w.startMs,start)-start),
      endMs:Math.round(timeline_offset_seconds*1000+Math.min(w.endMs,end)-start)
    }));
    const at=Math.round(timeline_offset_seconds*1000+Math.max(c.startMs,start)-start);
    const until=Math.round(timeline_offset_seconds*1000+Math.min(c.endMs,end)-start);
    return {...c,words:clippedWords,
      startMs:at,endMs:until,source_start_ms:c.startMs,source_end_ms:c.endMs};
  }).filter(c=>c.words.length>0 && c.endMs>c.startMs);
}
