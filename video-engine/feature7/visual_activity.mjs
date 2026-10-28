/**
 * Feature7 low-cost real footage QA from FFmpeg blackdetect + freezedetect.
 * This only emits reviewer advisories. It does not render, cut, upload,
 * classify speech or delete retailer content. A static talking-head shot is
 * often intentional, so freeze detection must NEVER auto-discard frames.
 */
import {spawnSync} from 'node:child_process';
import {EditValidationError} from './autobroll_semantics.mjs';

const check=(ok,msg)=>{if(!ok)throw new EditValidationError(msg);};
const validNumber=(value,max)=>Number.isFinite(value)&&value>=0&&value<=max;

function readIntervals(log,pattern,duration_seconds,maxEvents=32) {
  const ranges=[];
  let match;
  while((match=pattern.exec(log))!==null){
    const start=Number(match[1]),end=Number(match[2]);
    if(!validNumber(start,duration_seconds+.2) ||
      !validNumber(end,duration_seconds+.2) || end<=start)continue;
    const from=Math.max(0,Math.min(duration_seconds,start));
    const to=Math.max(from,Math.min(duration_seconds,end));
    if(to-from>=.2)ranges.push({start_seconds:+from.toFixed(3),end_seconds:+to.toFixed(3)});
    if(ranges.length>maxEvents)throw new EditValidationError('Too many visual QA events');
  }
  return ranges;
}
export function parseVisualQaLog(log,duration_seconds){
  check(typeof log==='string' && log.length<=300000 &&
    validNumber(duration_seconds,600)&&duration_seconds>=.5,
  'Invalid FFmpeg visual QA log');
  const black=readIntervals(log,/black_start:([\d.]+)\s+black_end:([\d.]+)/g,duration_seconds);
  const freezes=readIntervals(log,/freeze_start:\s*([\d.]+)[\s\S]{0,180}?freeze_end:\s*([\d.]+)/g,duration_seconds);
  return Object.freeze({
    classification:'VISUAL_QUALITY_ADVISORY_ONLY',
    black_intervals:black,
    freeze_intervals:freezes,
    no_scene_deletion:true,
    no_media_modification:true,
    no_visual_semantic_model:true,
    human_review_required:true
  });
}

export function analyzeLocalVisualActivity({path,duration_seconds,timeout_ms=45000}={}){
  check(typeof path==='string' && path.length>0 &&
    !/^(https?:)?\/\//i.test(path) &&
    validNumber(duration_seconds,600)&&duration_seconds>=.5 &&
    Number.isInteger(timeout_ms)&&timeout_ms>=1000&&timeout_ms<=60000,
  'Invalid private visual QA source');
  const args=['-hide_banner','-nostdin','-v','info','-threads','1',
    '-i',path,'-map','0:v:0','-an','-vf',
    'fps=2,blackdetect=d=0.5:pix_th=0.10,freezedetect=n=-60dB:d=2',
    '-f','null','-'];
  const outcome=spawnSync('ffmpeg',args,{
    encoding:'utf8',stdio:['ignore','pipe','pipe'],
    timeout:timeout_ms,maxBuffer:300000
  });
  check(!outcome.error && outcome.status===0,
    'Private FFmpeg visual QA failed or timed out');
  return parseVisualQaLog(outcome.stderr,duration_seconds);
}
