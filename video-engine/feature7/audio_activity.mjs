/**
 * Feature7 CPU-only audio-activity analysis using the existing FFmpeg binary.
 * Based on AutoBroll's speech-gap / pad approach, but DOES NOT claim a
 * silence detector is ASR or voice activity detection: music and tones count
 * as non-silent too. Use verified word timings for actual speech-aware cuts.
 */
import {spawnSync} from 'node:child_process';
import {verifiedLocalMp4Path} from './local_mp4_guard.mjs';

export class AudioAnalysisError extends Error {}

export function parseSilencedetect(stderr, durationSec) {
  if(typeof stderr!=='string' || !(Number.isFinite(durationSec) && durationSec>0 && durationSec<=600))
    throw new AudioAnalysisError('Invalid silence analysis input');
  const spans=[];
  let start=null;
  for(const line of stderr.split(/\r?\n/)) {
    const mStart=line.match(/silence_start:\s*(-?\d+(?:\.\d+)?)/);
    if(mStart) {
      const v=Number(mStart[1]);
      if(Number.isFinite(v) && start===null) start=Math.max(0,Math.min(durationSec,v));
    }
    const mEnd=line.match(/silence_end:\s*(-?\d+(?:\.\d+)?)/);
    if(mEnd && start!==null) {
      const end=Math.max(0,Math.min(durationSec,Number(mEnd[1])));
      if(end>start) spans.push({start_seconds:+start.toFixed(3),end_seconds:+end.toFixed(3)});
      start=null;
    }
  }
  if(start!==null && durationSec>start) spans.push({
    start_seconds:+start.toFixed(3),end_seconds:+durationSec.toFixed(3)
  });
  const normalized=[];
  for(const s of spans.sort((a,b)=>a.start_seconds-b.start_seconds)) {
    const prev=normalized.at(-1);
    if(prev && prev.end_seconds>=s.start_seconds) prev.end_seconds=Math.max(prev.end_seconds,s.end_seconds);
    else normalized.push(s);
  }
  const active=[];
  let from=0;
  for(const s of normalized) {
    if(s.start_seconds-from>=0.1) active.push({start_seconds:+from.toFixed(3),
      end_seconds:s.start_seconds});
    from=Math.max(from,s.end_seconds);
  }
  if(durationSec-from>=0.1) active.push({start_seconds:+from.toFixed(3),
    end_seconds:+durationSec.toFixed(3)});
  return {silence_intervals:normalized,non_silent_intervals:active,
    classification:'AUDIO_ACTIVITY_NOT_SPEECH',original_audio_preserved:true};
}

export function analyzeLocalAudioActivity({path, duration_seconds, has_audio,
  ffmpeg_bin='ffmpeg'}={}) {
  if(typeof path!=='string' || !path.startsWith('/') ||
    !Number.isFinite(duration_seconds) || duration_seconds<0.5 ||
    duration_seconds>600 || has_audio!==true)
    throw new AudioAnalysisError('An approved local audio-video and duration are required');
  const source=verifiedLocalMp4Path(path,AudioAnalysisError);
  const p=spawnSync(ffmpeg_bin,['-hide_banner','-nostdin','-v','info',
    '-protocol_whitelist','file,pipe','-f','mp4',
    '-i',source,'-vn','-af','silencedetect=noise=-35dB:d=0.35',
    '-f','null','-'],{encoding:'utf8',timeout:60000,maxBuffer:512*1024});
  if(p.error || p.status!==0) throw new AudioAnalysisError('FFmpeg audio-analysis failed');
  return parseSilencedetect(p.stderr,duration_seconds);
}
