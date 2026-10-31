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
    // FFmpeg may report an interval closing slightly beyond final video time.
    // Accept at most 2 seconds of decoder overshoot; clamp below to the
    // verified source duration, never emit out-of-source edit coordinates.
    if(!validNumber(start,duration_seconds+2) ||
      !validNumber(end,duration_seconds+2) || end<=start)continue;
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

/**
 * Read-only real FFmpeg scene-cut evidence for human hook/pacing review.
 * Unlike keyword B-roll cues this DOES NOT infer SKU, plot, meaning, acting,
 * model identity, consent or suitability. No automatic cutting/publishing.
 */
export function parseSceneChangeLog(log,duration_seconds){
  check(typeof log==='string'&&log.length<=300000&&
    validNumber(duration_seconds,600)&&duration_seconds>=.5,
    'Invalid scene-change evidence');
  const timestamps=[];
  const re=/\bpts_time:\s*([\d.]+)\b/g;
  let match;
  while((match=re.exec(log))!==null){
    const time=Number(match[1]);
    check(validNumber(time,duration_seconds+0.05),
      'Out-of-source scene-change time');
    const rounded=+Math.min(time,duration_seconds).toFixed(3);
    check(!timestamps.length||rounded>=timestamps.at(-1),
      'Out-of-order scene changes');
    if(rounded>=.2 && rounded<=duration_seconds-.2 &&
      (!timestamps.length||rounded-timestamps.at(-1)>=.1)){
      timestamps.push(rounded);
    }
    check(timestamps.length<=64,'Excess scene cuts');
  }
  return Object.freeze({
    classification:'SCENE_CHANGE_REVIEW_ADVISORY_ONLY',
    scene_change_seconds:timestamps,
    first_three_seconds_change_count:timestamps.filter(t=>t<=3).length,
    hook_pacing_review_needed:timestamps.every(t=>t>3),
    semantic_product_relevance_verified:false,
    no_automatic_shot_choice:true,
    no_scene_deletion:true,
    human_review_required:true
  });
}

export function analyzeLocalSceneChangesCPU({
  path,duration_seconds,threshold=.12,timeout_ms=45000
}={}){
  check(typeof path==='string'&&path.length>0&&
    !/^(https?:)?\/\//i.test(path)&&
    validNumber(duration_seconds,600)&&duration_seconds>=.5&&
    Number.isFinite(threshold)&&threshold>=.08&&threshold<=.6&&
    Number.isInteger(timeout_ms)&&timeout_ms>=1000&&timeout_ms<=60000,
    'Invalid local scene-change request');
  const args=['-hide_banner','-nostdin','-v','info','-threads','1',
    '-i',path,'-map','0:v:0','-an','-vf',
    "scale=320:-2,select='gt(scene,"+threshold.toFixed(3)+")',showinfo",
    '-vsync','0','-f','null','-'];
  const result=spawnSync('ffmpeg',args,{
    encoding:'utf8',stdio:['ignore','pipe','pipe'],
    timeout:timeout_ms,maxBuffer:300000
  });
  check(!result.error&&result.status===0,
    'CPU scene-change analysis failed or timed out');
  return parseSceneChangeLog(result.stderr,duration_seconds);
}
