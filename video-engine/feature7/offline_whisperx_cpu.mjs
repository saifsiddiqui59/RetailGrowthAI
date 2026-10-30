/**
 * Feature7 CPU-only, optional local WhisperX inference via its actual CLI.
 *
 * No model download or install occurs here. The operator must preinstall a
 * reviewed WhisperX executable, model and aligner weights in a network-isolated
 * worker. This is the real CLI invocation path, not a transcription simulation.
 * CI exercises protocol with a fake executable; genuine model accuracy remains
 * untested until operator provides weights and legal approved speech.
 */
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import crypto from 'node:crypto';
import {spawnSync} from 'node:child_process';
import {verifyPrivateVideo,resolveApprovedLocalVideo} from './media_preflight.mjs';
import {normalizeWhisperx} from './transcript_adapter.mjs';
import {sealTranscriptEvidence} from './transcript_evidence.mjs';

export class OfflineAsrError extends Error {}
const requireOk=(ok,msg)=>{if(!ok) throw new OfflineAsrError(msg);};
function trustedExecutable(binary) {
  requireOk(typeof binary==='string' && path.isAbsolute(binary),'Configured WhisperX executable must be absolute');
  const stat=fs.lstatSync(binary);
  requireOk(stat.isFile() && !stat.isSymbolicLink(),'Invalid WhisperX executable');
  return fs.realpathSync(binary);
}
function localModel(model_dir) {
  requireOk(typeof model_dir==='string' && path.isAbsolute(model_dir),
    'WhisperX model must be a local absolute directory');
  const st=fs.lstatSync(model_dir);
  requireOk(st.isDirectory() && !st.isSymbolicLink(),'WhisperX model missing');
  return fs.realpathSync(model_dir);
}
// Kept as a small exported primitive for real subprocess timeout regression
// tests. SIGKILL is deliberate: SIGTERM can be caught/ignored by a hung CPU
// model process, leaving a synchronous worker blocked past its time budget.
export function runBoundedOfflineCommand(binary,args,timeoutMs,env,step) {
  requireOk(typeof binary==='string'&&binary.length>0&&
    Array.isArray(args)&&args.every(arg=>typeof arg==='string')&&
    Number.isSafeInteger(timeoutMs)&&timeoutMs>0&&timeoutMs<=600000&&
    typeof step==='string'&&step.length>0,
  'Invalid bounded offline command');
  const p=spawnSync(binary,args,{
    env,encoding:'utf8',timeout:timeoutMs,killSignal:'SIGKILL',
    maxBuffer:256*1024,stdio:['ignore','pipe','pipe']
  });
  requireOk(!p.error && p.status===0,step+' failed or timed out (no transcript approved)');
}
export function transcribePrivateClipCPU({
  shop_id,asset_id,job_id,grant,root,relative_path,expected_sha256,
  evidence_key,whisperx_bin,model_dir,model_id='whisperx_local_cpu_v1',
  ffmpeg_bin='ffmpeg',timeout_ms=360000,now_ms=Date.now()
}={}) {
  requireOk(typeof job_id==='string' && /^[A-Za-z0-9_-]{1,120}$/.test(job_id),
    'Trusted ASR job ID required');
  requireOk(Number.isInteger(timeout_ms) && timeout_ms>=5000 && timeout_ms<=600000,
    'ASR wall-time must be bounded');
  const binary=trustedExecutable(whisperx_bin);
  const model=localModel(model_dir);
  const original=verifyPrivateVideo({
    shop_id,asset_id,grant,root,relative_path,expected_sha256
  });
  requireOk(original.has_audio===true && grant.has_audio===true,
    'Speech ASR requires a verified approved audio track');
  const source=resolveApprovedLocalVideo({root,relative_path});
  const working=fs.mkdtempSync(path.join(os.tmpdir(),'retail-feature7-asr-'));
  fs.chmodSync(working,0o700);
  const env={
    PATH:process.env.PATH??'/usr/bin:/bin',
    HOME:working,
    HF_HOME:working,
    XDG_CACHE_HOME:working,
    HF_HUB_OFFLINE:'1',TRANSFORMERS_OFFLINE:'1',HF_DATASETS_OFFLINE:'1',
    TOKENIZERS_PARALLELISM:'false',
    CUDA_VISIBLE_DEVICES:'',PYTHONNOUSERSITE:'1',
    OMP_NUM_THREADS:'2'
  };
  try {
    const wav=path.join(working,'source.wav');
    runBoundedOfflineCommand(ffmpeg_bin,['-hide_banner','-nostdin','-v','error','-y',
      '-protocol_whitelist','file,pipe',
      '-i',source,'-vn','-ac','1','-ar','16000','-f','wav',wav],
    60000,env,'Private WAV extraction');
    requireOk(fs.statSync(wav).size<30*1024*1024,'Excessive private WAV size');
    const outDir=path.join(working,'transcripts');
    fs.mkdirSync(outDir,{mode:0o700});
    // WhisperX accepts an explicitly staged local faster-whisper model path.
    // VAD/aligner dependencies must already be cached in the egress-disabled
    // runtime; otherwise the command fails closed.
    runBoundedOfflineCommand(binary,[wav,'--model',model,'--device','cpu',
      '--compute_type','int8','--output_format','json',
      '--output_dir',outDir],timeout_ms,env,'WhisperX CPU inference');
    const jsonFile=path.join(outDir,'source.json');
    const st=fs.lstatSync(jsonFile);
    requireOk(st.isFile() && !st.isSymbolicLink() &&
      st.size>0 && st.size<=2*1024*1024,'Missing or oversized local ASR output');
    const transcript=JSON.parse(fs.readFileSync(jsonFile,'utf8'));
    const normalized=normalizeWhisperx({
      asset_id,shop_id,source_sha256:original.sha256,
      source_duration_seconds:original.duration_seconds,transcript
    });
    // Re-verify source bytes after inference: no stale/changed source accepted.
    verifyPrivateVideo({shop_id,asset_id,grant,root,relative_path,
      expected_sha256:original.sha256});
    const evidence=sealTranscriptEvidence({
      data:{shop_id,asset_id,job_id,source_sha256:original.sha256,
        transcript_sha256:normalized.transcript_sha256,model_id,
        issued_at_ms:now_ms,expires_at_ms:now_ms+5*60*1000},
      key:evidence_key,now_ms
    });
    return Object.freeze({
      ...normalized,transcription_status:'verified_local_cpu_asr',
      model_id,evidence,local_cli_invoked:true,
      original_media_sha256:original.sha256,
      no_remote_model_calls:true
    });
  } finally {
    fs.rmSync(working,{recursive:true,force:true,maxRetries:2});
  }
}
