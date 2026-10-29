/**
 * Feature7 REAL Faster-Whisper CPU→existing signed transcript contract.
 * Calls pinned upstream SYSTRAN/faster-whisper in faster_whisper_cpu.py.
 * No Python neural network reimplementation or fabricated word timings.
 * Assumes caller is a trusted backend with CURRENT authenticated rights.
 * Never send its grant/HMAC or model config through a browser HTTP request.
 */
import crypto from 'node:crypto';
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
import {spawnSync} from 'node:child_process';
import {verifyPrivateVideo,resolveApprovedLocalVideo} from './media_preflight.mjs';
import {normalizeWhisperx} from './transcript_adapter.mjs';
import {sealTranscriptEvidence} from './transcript_evidence.mjs';
import {feature7CpuOnlyEnv} from './cpu_readiness.mjs';

export class FasterWhisperCpuError extends Error {}
const ensure=(ok,msg)=>{if(!ok)throw new FasterWhisperCpuError(msg);};
const ID=/^[A-Za-z0-9_-]{1,120}$/;
const SHA=/^[a-f0-9]{64}$/;
const LANG=new Set(['auto','en','hi','mr']);

function trustedFile(file,label){
  ensure(typeof file==='string'&&path.isAbsolute(file),
    'Absolute '+label+' required');
  const st=fs.lstatSync(file);
  ensure(st.isFile()&&!st.isSymbolicLink(),'Unsafe '+label);
  return fs.realpathSync(file);
}
function trustedDir(dir,label){
  ensure(typeof dir==='string'&&path.isAbsolute(dir),
    'Absolute '+label+' required');
  const st=fs.lstatSync(dir);
  ensure(st.isDirectory()&&!st.isSymbolicLink(),'Unsafe '+label);
  return fs.realpathSync(dir);
}
function spawnChecked(executable,args,{env,timeoutMs,step}){
  const p=spawnSync(executable,args,{env,timeout:timeoutMs,encoding:'utf8',
    maxBuffer:512*1024,stdio:['ignore','pipe','pipe']});
  // A transcript or a message from failed inference cannot be trusted.
  ensure(!p.error&&p.status===0,step+' failed; no verified ASR was emitted');
}
export function transcribePrivateVideoWithFasterWhisperCPU({
  shop_id,asset_id,job_id,grant,root,relative_path,expected_sha256,
  evidence_key,model_dir,model_manifest,python_bin,ffmpeg_bin='ffmpeg',
  language='auto',threads=2,timeout_ms=360000,now_ms=Date.now()
}={}){
  ensure(typeof job_id==='string'&&ID.test(job_id),
    'Trusted ASR job ID required');
  ensure(typeof expected_sha256==='string'&&SHA.test(expected_sha256),
    'Approved original media SHA256 required');
  ensure(LANG.has(language)&&Number.isInteger(threads)&&threads>=1&&threads<=4&&
    Number.isInteger(timeout_ms)&&timeout_ms>=5000&&timeout_ms<=600000&&
    Number.isSafeInteger(now_ms)&&now_ms>=0,
    'Unsupported locale, threads, timeout or trusted time');
  ensure(Buffer.isBuffer(evidence_key)&&evidence_key.length>=32,
    'Backend-only ASR evidence signing key required');
  const binary=trustedFile(python_bin,'trusted Python runtime');
  const model=trustedDir(model_dir,'approved Faster-Whisper model directory');
  const manifest=trustedFile(model_manifest,'operator model manifest');
  const verified=verifyPrivateVideo({
    shop_id,asset_id,grant,root,relative_path,expected_sha256
  });
  ensure(verified.has_audio===true&&grant.has_audio===true,
    'Approved original speech audio required');
  const original=resolveApprovedLocalVideo({root,relative_path});
  const temp=fs.mkdtempSync(path.join(os.tmpdir(),'retail-feature7-faster-asr-'));
  fs.chmodSync(temp,0o700);
  const env=feature7CpuOnlyEnv({
    PATH:process.env.PATH??'/usr/bin:/bin',
    HOME:temp,TMPDIR:temp,HF_HOME:temp,XDG_CACHE_HOME:temp,
    FEATURE7_GPU_ENABLED:'0',FEATURE7_ALLOW_PAID_INFERENCE:'0',
    FEATURE7_NETWORK_MODELS:'0',FEATURE7_ENABLE_REMOTE_PROVIDER:'0'
  });
  const wav=path.join(temp,'private_audio.wav');
  const output=path.join(temp,'words.json');
  try{
    spawnChecked(ffmpeg_bin,['-nostdin','-hide_banner','-loglevel','error',
      '-protocol_whitelist','file,pipe','-i',original,
      '-map','0:a:0','-vn','-ac','1','-ar','16000','-f','wav',wav],
    {env,timeoutMs:60000,step:'Private 16 kHz audio extraction'});
    const audioStat=fs.lstatSync(wav);
    ensure(audioStat.isFile()&&!audioStat.isSymbolicLink()&&
      audioStat.size>44&&audioStat.size<32*1024*1024,
      'Malformed or oversized original speech audio');
    const stagedWavSha=crypto.createHash('sha256')
      .update(fs.readFileSync(wav)).digest('hex');
    const script=trustedFile(
      path.join(path.dirname(fileURLToPath(import.meta.url)),
        'faster_whisper_cpu.py'),'repository ASR source');
    spawnChecked(binary,[script,'--wav',wav,
      '--model-dir',model,'--model-manifest',manifest,
      '--output-json',output,'--duration',String(verified.duration_seconds),
      '--language',language,'--threads',String(threads)],
    {env,timeoutMs:timeout_ms,step:'Actual local CTranslate2 inference'});
    const st=fs.lstatSync(output);
    ensure(st.isFile()&&!st.isSymbolicLink()&&st.size>0&&st.size<=2*1024*1024,
      'Missing or unsafe real CPU inference result');
    const parsed=JSON.parse(fs.readFileSync(output,'utf8'));
    ensure(parsed.verified_input_sha256===stagedWavSha&&
      crypto.createHash('sha256').update(fs.readFileSync(wav))
        .digest('hex')===stagedWavSha,
      'Actual ASR source WAV identity changed during inference');
    ensure(parsed.version==='feature7_faster_whisper_cpu_transcript_v1'&&
      parsed.engine==='SYSTRAN/faster-whisper'&&
      parsed.word_timestamps_from_actual_model===true&&
      parsed.word_accuracy_benchmarked===false&&
      parsed.approved===false&&parsed.renderable===false&&
      parsed.model_project==='Systran/faster-whisper-small'&&
      parsed.model_revision==='536b0662742c02347bc0e980a01041f333bce120'&&
      SHA.test(parsed.model_bin_sha256??''),
      'Inference model evidence/shape mismatch');
    const normalized=normalizeWhisperx({
      shop_id,asset_id,source_sha256:verified.sha256,
      source_duration_seconds:verified.duration_seconds,transcript:parsed
    });
    // Re-verify byte identity on original media after long-running model call.
    verifyPrivateVideo({shop_id,asset_id,grant,root,relative_path,
      expected_sha256:verified.sha256});
    const modelId='faster_whisper_small_cpu_int8';
    const evidence=sealTranscriptEvidence({
      data:{shop_id,asset_id,job_id,source_sha256:verified.sha256,
        transcript_sha256:normalized.transcript_sha256,model_id:modelId,
        issued_at_ms:now_ms,expires_at_ms:now_ms+5*60*1000},
      key:evidence_key,now_ms
    });
    return Object.freeze({...normalized,
      version:'feature7_signed_faster_whisper_asr_v1',
      model_id:modelId,model_revision:parsed.model_revision,
      model_bin_sha256:parsed.model_bin_sha256,
      transcription_status:'real_local_cpu_decoder_output',
      language:parsed.language,
      actual_decode_wall_seconds:parsed.actual_decode_wall_seconds,
      actual_decode_realtime_factor:parsed.actual_decode_realtime_factor,
      verified_input_sha256:stagedWavSha,
      process_peak_rss_bytes:parsed.process_peak_rss_bytes??null,
      asr_word_accuracy_benchmarked:false,
      independent_word_alignment_accepted:false,
      evidence,local_cpu_inference_invoked:true,
      original_media_sha256:verified.sha256,
      no_remote_model_calls:true,
      approved:false,renderable:false,customer_publishable:false
    });
  }finally{
    fs.rmSync(temp,{recursive:true,force:true,maxRetries:2});
  }
}
