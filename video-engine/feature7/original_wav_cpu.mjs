/**
 * Feature7 original-WAV -> actual Faster-Whisper CPU -> Feature2 signed QA.
 *
 * This is a server-only ADAPTER, not an HTTP endpoint or an alternate STT
 * decoder. The only source of authority is an independently trusted current
 * JWT/RLS+job/lease callback supplied by the coordinator backend.
 * No browser, serialized "trusted_server" grant or user JWT can call this.
 *
 * The original Feature2 PCM16-mono WAV byte identity is signed; unlike the
 * video path we never transcode WAV into MP4 or sign a derived source digest.
 * Real inference uses faster_whisper_cpu.py -> upstream WhisperModel.
 */
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
import crypto from 'node:crypto';
import {spawnSync} from 'node:child_process';
import {normalizeWhisperx} from './transcript_adapter.mjs';
import {sealTranscriptEvidence} from './transcript_evidence.mjs';
import {feature7CpuOnlyEnv} from './cpu_readiness.mjs';

export class OriginalAudioAsrDenied extends Error {}
const need=(ok,msg)=>{if(!ok)throw new OriginalAudioAsrDenied(msg);};
const ID=/^[A-Za-z0-9_-]{1,120}$/;
const SHA=/^[a-f0-9]{64}$/;
const LIMIT=20_000_000;
const bytesHash=data=>crypto.createHash('sha256').update(data).digest('hex');
const validId=x=>typeof x==='string'&&ID.test(x);
const validSha=x=>typeof x==='string'&&SHA.test(x);
const isPlain=x=>x&&typeof x==='object'&&!Array.isArray(x);
const realFile=(file,name)=>{
  need(typeof file==='string'&&path.isAbsolute(file),'Absolute '+name+' needed');
  const st=fs.lstatSync(file);
  need(st.isFile()&&!st.isSymbolicLink(),'Unsafe '+name);
  return fs.realpathSync(file);
};
const realDir=(dir,name)=>{
  need(typeof dir==='string'&&path.isAbsolute(dir),'Absolute '+name+' needed');
  const st=fs.lstatSync(dir);
  need(st.isDirectory()&&!st.isSymbolicLink(),'Unsafe '+name);
  return fs.realpathSync(dir);
};
function privateFile(root,relative){
  const base=realDir(root,'private audio root');
  need(typeof relative==='string'&&relative.length<=240&&
    !relative.includes('\\')&&!path.isAbsolute(relative)&&
    /^[A-Za-z0-9_.\/-]+$/.test(relative)&&
    relative.endsWith('.wav')&&
    relative.split('/').every(x=>x&&x!=='.'&&x!=='..'),
    'Unsafe private WAV location');
  let current=base;
  const parts=relative.split('/');
  for(let i=0;i<parts.length;i++){
    current=path.join(current,parts[i]);
    const st=fs.lstatSync(current);
    need(!st.isSymbolicLink()&&
      (i===parts.length-1?st.isFile():st.isDirectory()),
      'Private WAV cannot pass through links');
  }
  const original=fs.realpathSync(current);
  need(original.startsWith(base+path.sep),'Private WAV escaped tenant root');
  return original;
}
export function inspectOriginalPrivatePCM16Wav({
  root,relative_path,expected_sha256
}={}){
  need(validSha(expected_sha256),'Source original WAV SHA256 required');
  const original=privateFile(root,relative_path);
  const st=fs.lstatSync(original);
  need(st.isFile()&&st.size>=128&&st.size<=LIMIT,
    'Empty/oversized original WAV');
  // O_NOFOLLOW rejects changed final symlinks; an independent coordinator
  // lease/immutable cloud object generation is required for full race safety.
  const fd=fs.openSync(original,fs.constants.O_RDONLY|fs.constants.O_NOFOLLOW);
  let bytes;
  try{
    const opened=fs.fstatSync(fd);
    need(opened.isFile()&&opened.size===st.size,'Source WAV changed on open');
    bytes=Buffer.alloc(opened.size);
    let offset=0;
    while(offset<bytes.length){
      const n=fs.readSync(fd,bytes,offset,bytes.length-offset,offset);
      need(n>0,'Original private WAV truncated');
      offset+=n;
    }
    need(fs.fstatSync(fd).size===opened.size,'Source WAV changed mid-read');
  }finally{fs.closeSync(fd);}
  need(bytesHash(bytes)===expected_sha256,'Original WAV bytes have changed');
  need(bytes.toString('ascii',0,4)==='RIFF'&&
    bytes.toString('ascii',8,12)==='WAVE'&&
    bytes.readUInt32LE(4)+8===bytes.length,
    'Not an exact canonical RIFF/WAV');
  let fmt=null,pcmBytes=null;
  let finalOffset=12,chunkCount=0,seenData=false;
  for(let offset=12;offset+8<=bytes.length;){
    need(++chunkCount<=24,'Too many untrusted WAV chunks');
    need(!seenData,'Untrusted WAV chunks after speech samples');
    const tag=bytes.toString('ascii',offset,offset+4);
    const len=bytes.readUInt32LE(offset+4);
    const start=offset+8;
    need(len>=0&&start+len<=bytes.length,'WAV chunk exceeds input');
    need(['fmt ','data','JUNK','LIST'].includes(tag),
      'Unrecognized WAV chunk');
    if(tag==='fmt '){
      need(fmt===null&&pcmBytes===null&&len===16,
        'Invalid, extended or duplicate PCM format');
      fmt={format:bytes.readUInt16LE(start),
        channels:bytes.readUInt16LE(start+2),
        rate:bytes.readUInt32LE(start+4),
        byteRate:bytes.readUInt32LE(start+8),
        align:bytes.readUInt16LE(start+12),
        bits:bytes.readUInt16LE(start+14)};
    }
    if(tag==='data'){
      need(fmt!==null&&pcmBytes===null&&len>0,
        'Audio samples require one validated PCM format');
      pcmBytes=len;
      seenData=true;
    }
    need((tag==='fmt '||tag==='data')||len<=65536,
      'Oversized ancillary WAV chunk');
    offset=start+len+(len%2);
    finalOffset=offset;
  }
  need(finalOffset===bytes.length,'Trailing/invalid RIFF chunk bytes');
  need(fmt&&fmt.format===1&&fmt.channels===1&&fmt.bits===16&&
    fmt.align===2&&fmt.byteRate===fmt.rate*2&&
    fmt.rate>=16000&&fmt.rate<=48000&&pcmBytes!==null&&pcmBytes%2===0,
    'Feature2 original WAV must be mono PCM16 at 16–48kHz');
  const seconds=Math.round((pcmBytes/2/fmt.rate)*1000)/1000;
  need(seconds>=.2&&seconds<=65,'Invalid original narration length');
  return Object.freeze({source_sha256:expected_sha256,
    duration_seconds:seconds,sample_rate_hz:fmt.rate,
    source_media_kind:'audio/wav',raw_source_bytes:bytes,
    original_path:original,byte_length:bytes.length});
}
function assertCurrent({read_current_audio,shop_id,campaign_id,
  creative_plan_sha256,asset_id,job_id,expected_sha256,
  expected_duration_seconds,root,relative_path,registry_revision}){
  const scope={shop_id,campaign_id,creative_plan_sha256,asset_id,job_id};
  const a=read_current_audio(Object.freeze({...scope}));
  need(isPlain(a)&&a.shop_id===shop_id&&
    a.campaign_id===campaign_id&&
    a.creative_plan_sha256===creative_plan_sha256&&
    a.audio_asset_id===asset_id&&a.job_id===job_id&&
    a.original_audio_sha256===expected_sha256&&
    a.source_media_kind==='audio/wav'&&a.mime_type==='audio/wav'&&
    a.original_duration_seconds===expected_duration_seconds&&
    a.private_root===root&&a.relative_path===relative_path&&
    a.registry_revision===registry_revision&&
    a.origin==='trusted_feature7_original_audio_worker'&&
    a.active_membership===true&&a.tenant_rights_current===true&&
    a.editor_role_authorized===true&&a.approved_source_rights===true&&
    a.job_lease_current===true&&a.revoked_at===null,
    'Authoritative source WAV/job/rights no longer current');
  return a;
}
export function transcribeFeature2OriginalWavCPU({
  shop_id,campaign_id,creative_plan_sha256,asset_id,job_id,
  expected_sha256,expected_duration_seconds,registry_revision,
  root,relative_path,read_current_audio,save_verified_job,
  python_bin,model_dir,model_manifest,evidence_key,
  language='auto',threads=2,timeout_ms=360000,now_ms=Date.now()
}={}){
  need([shop_id,campaign_id,asset_id,job_id].every(validId)&&
    [creative_plan_sha256,expected_sha256].every(validSha)&&
    Number.isSafeInteger(registry_revision)&&registry_revision>=0&&
    typeof expected_duration_seconds==='number'&&
    Number.isFinite(expected_duration_seconds)&&
    expected_duration_seconds>=.2&&expected_duration_seconds<=65&&
    typeof read_current_audio==='function'&&
    typeof save_verified_job==='function'&&
    Buffer.isBuffer(evidence_key)&&evidence_key.length>=32,
    'Only trusted current registered Feature2 original-audio job allowed');
  need(['auto','en','hi','mr'].includes(language)&&
    Number.isInteger(threads)&&threads>=1&&threads<=4&&
    Number.isInteger(timeout_ms)&&timeout_ms>=5000&&timeout_ms<=600000&&
    Number.isSafeInteger(now_ms)&&now_ms>=0,
    'Invalid bounded CPU job settings');
  // Reject model/executable misconfiguration before reading private media.
  const python=realFile(python_bin,'Python worker');
  const model=realDir(model_dir,'model checkpoint');
  const manifest=realFile(model_manifest,'model manifest');
  assertCurrent({read_current_audio,shop_id,campaign_id,
    creative_plan_sha256,asset_id,job_id,expected_sha256,
    expected_duration_seconds,registry_revision,root,relative_path});
  const original=inspectOriginalPrivatePCM16Wav({
    root,relative_path,expected_sha256});
  need(original.duration_seconds===expected_duration_seconds,
    'Registered original WAV duration differs from PCM frames');
  const tmp=fs.mkdtempSync(path.join(os.tmpdir(),'retail-f7-original-wav-'));
  fs.chmodSync(tmp,0o700);
  const env=feature7CpuOnlyEnv({
    PATH:process.env.PATH??'/usr/bin:/bin',
    HOME:tmp,TMPDIR:tmp,HF_HOME:tmp,XDG_CACHE_HOME:tmp,
    FEATURE7_GPU_ENABLED:'0',FEATURE7_ALLOW_PAID_INFERENCE:'0',
    FEATURE7_NETWORK_MODELS:'0',FEATURE7_ENABLE_REMOTE_PROVIDER:'0'
  });
  const staged=path.join(tmp,'original_audio.wav');
  const output=path.join(tmp,'words.json');
  try{
    fs.writeFileSync(staged,original.raw_source_bytes,{flag:'wx',mode:0o600});
    const script=realFile(path.join(path.dirname(fileURLToPath(import.meta.url)),
      'faster_whisper_cpu.py'),'actual Faster-Whisper Python implementation');
    const args=[script,'--wav',staged,'--model-dir',model,
      '--model-manifest',manifest,'--output-json',output,
      '--duration',String(original.duration_seconds),
      '--language',language,'--threads',String(threads)];
    const run=spawnSync(python,args,{env,encoding:'utf8',timeout:timeout_ms,
      maxBuffer:128*1024,stdio:['ignore','pipe','pipe']});
    need(!run.error&&run.status===0,
      'Real offline Faster-Whisper inference failed; no transcript accepted');
    const st=fs.lstatSync(output);
    need(st.isFile()&&!st.isSymbolicLink()&&
      st.size>0&&st.size<=2*1024*1024,
      'Missing/unsafe original WAV speech inference result');
    const decoded=JSON.parse(fs.readFileSync(output,'utf8'));
    need(decoded.verified_input_sha256===expected_sha256&&
      bytesHash(fs.readFileSync(staged))===expected_sha256,
      'Actual CPU inference must prove original input WAV identity');
    need(decoded.version==='feature7_faster_whisper_cpu_transcript_v1'&&
      decoded.engine==='SYSTRAN/faster-whisper'&&
      decoded.model_project==='Systran/faster-whisper-small'&&
      /^[a-f0-9]{40}$/.test(decoded.model_revision??'')&&
      validSha(decoded.model_bin_sha256)&&
      decoded.word_timestamps_from_actual_model===true&&
      decoded.word_accuracy_benchmarked===false&&
      decoded.approved===false&&decoded.renderable===false,
      'Only real model output is accepted from approved CPU process');
    const words=normalizeWhisperx({shop_id,asset_id,
      source_sha256:expected_sha256,
      source_duration_seconds:original.duration_seconds,
      transcript:decoded});
    need(words.words.length>=1&&words.words.length<=600&&
      words.words.every((w,i)=>w.startMs>=0&&w.endMs>w.startMs&&
        w.endMs<=Math.round(original.duration_seconds*1000)+1&&
        (i===0||w.startMs>=words.words[i-1].endMs)),
      'F2 requires strictly ordered actual word timestamps');
    // Verify the source SHA and trusted active registry AGAIN after inference.
    const after=inspectOriginalPrivatePCM16Wav({
      root,relative_path,expected_sha256});
    need(after.duration_seconds===original.duration_seconds,
      'Original source WAV changed during CPU inference');
    assertCurrent({read_current_audio,shop_id,campaign_id,
      creative_plan_sha256,asset_id,job_id,expected_sha256,
      expected_duration_seconds,registry_revision,root,relative_path});
    const model_id='faster_whisper_small_cpu_int8';
    const receipt=Object.freeze({
      ...words,
      version:'feature7_signed_faster_whisper_asr_v1',
      source_media_kind:'audio/wav',shop_id,campaign_id,
      creative_plan_sha256,asset_id,job_id,
      source_sha256:expected_sha256,
      original_media_sha256:expected_sha256,
      source_duration_seconds:original.duration_seconds,
      model_id,model_revision:decoded.model_revision,
      model_bin_sha256:decoded.model_bin_sha256,
      verified_input_sha256:decoded.verified_input_sha256,
      process_peak_rss_bytes:decoded.process_peak_rss_bytes??null,
      transcription_status:'real_local_cpu_decoder_output',
      language:decoded.language,
      actual_decode_wall_seconds:decoded.actual_decode_wall_seconds,
      actual_decode_realtime_factor:decoded.actual_decode_realtime_factor,
      local_cpu_inference_invoked:true,no_remote_model_calls:true,
      evidence:sealTranscriptEvidence({
        data:{shop_id,asset_id,job_id,source_sha256:expected_sha256,
          transcript_sha256:words.transcript_sha256,model_id,
          issued_at_ms:now_ms,expires_at_ms:now_ms+300000},
        key:evidence_key,now_ms
      }),
      approved:false,renderable:false,customer_publishable:false
    });
    // Persistence is server-only; does not grant human approval. If the
    // durable write/reload fails, do not return a signed client-visible receipt.
    const persisted=save_verified_job(Object.freeze({
      job_id,shop_id,campaign_id,audio_asset_id:asset_id,
      source_media_kind:'audio/wav',
      original_audio_sha256:expected_sha256,
      origin:'trusted_feature7_original_audio_worker',
      revoked_at:null,receipt
    }));
    need(isPlain(persisted)&&persisted.job_id===job_id&&
      persisted.shop_id===shop_id&&persisted.campaign_id===campaign_id&&
      persisted.audio_asset_id===asset_id&&
      persisted.source_media_kind==='audio/wav'&&
      persisted.original_audio_sha256===expected_sha256&&
      persisted.origin==='trusted_feature7_original_audio_worker'&&
      persisted.revoked_at===null&&
      JSON.stringify(persisted.receipt)===JSON.stringify(receipt),
      'Durable authoritative original-audio job write unconfirmed');
    return Object.freeze({job_id,shop_id,campaign_id,
      audio_asset_id:asset_id,source_media_kind:'audio/wav',
      original_audio_sha256:expected_sha256,
      origin:'trusted_feature7_original_audio_worker',
      revoked_at:null,receipt,
      human_approval_performed:false,
      customer_publishable:false});
  }finally{
    fs.rmSync(tmp,{recursive:true,force:true,maxRetries:2});
  }
}
