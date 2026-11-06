/**
 * Feature7 strictly CPU/offline execution policy. Not a cloud GPU controller:
 * it cannot start/stop a charged Azure resource or verify other services.
 * Protects Feature7's own child process from accidental CUDA/GPU/paid calls.
 */
import fs from 'node:fs';
import path from 'node:path';

export class Feature7ComputePolicyError extends Error {}
const deny=(ok,msg)=>{if(!ok)throw new Feature7ComputePolicyError(msg);};
const OFF=new Set(['','0','false','no','off']);
export function feature7CpuOnlyEnv(input={}){
  deny(input&&typeof input==='object'&&!Array.isArray(input),'Invalid compute config');
  for(const key of ['FEATURE7_GPU_ENABLED','FEATURE7_ALLOW_PAID_INFERENCE',
    'FEATURE7_NETWORK_MODELS','FEATURE7_ENABLE_REMOTE_PROVIDER']){
    // Unknown or ambiguous switches are unsafe, even if the child env would
    // later override them. Only explicit OFF values are accepted.
    deny(OFF.has(String(input[key]??'').trim().toLowerCase()),
      'GPU, network models and paid inference are disabled for Feature7');
  }
  return Object.freeze({
    ...input,
    FEATURE7_GPU_ENABLED:'0',FEATURE7_ALLOW_PAID_INFERENCE:'0',
    FEATURE7_NETWORK_MODELS:'0',FEATURE7_ENABLE_REMOTE_PROVIDER:'0',
    CUDA_VISIBLE_DEVICES:'',HIP_VISIBLE_DEVICES:'',
    ROCR_VISIBLE_DEVICES:'',GPU_DEVICE_ORDINAL:'-1',
    HF_HUB_OFFLINE:'1',TRANSFORMERS_OFFLINE:'1',
    HF_DATASETS_OFFLINE:'1',PIP_NO_INDEX:'1',
    PYTHONNOUSERSITE:'1',OMP_NUM_THREADS:'2'
  });
}
function safeLocalFile(p){
  if(typeof p!=='string'||!path.isAbsolute(p))return false;
  try{
    const s=fs.lstatSync(p);
    if(!s.isFile()||s.isSymbolicLink())return false;
    fs.accessSync(p,fs.constants.X_OK);
    return true;
  }
  catch{return false;}
}
function safeLocalDir(p){
  if(typeof p!=='string'||!path.isAbsolute(p))return false;
  try{
    const s=fs.lstatSync(p);
    if(!s.isDirectory()||s.isSymbolicLink())return false;
    // An empty directory cannot stand in for an installed ASR model.
    // Presence alone still does NOT prove weights, licensing or inference.
    return fs.readdirSync(p).some(name=>{
      const item=fs.lstatSync(path.join(p,name));
      return item.isFile()&&!item.isSymbolicLink();
    });
  }
  catch{return false;}
}
/**
 * Reports what can actually be certified with locally installed components.
 * Missing weights is BLOCKED, never simulated green by the ASR stub.
 */
export function inspectFeature7CpuReadiness({
  env=process.env,whisperx_bin=null,model_dir=null,
  independent_license_approved=false,word_accuracy_verified=false,
  authenticated_upload_live=false,approval_db_live=false,
  feature4_final_renderer_live=false,hosted_e2e_verified=false
}={}){
  const resolved=feature7CpuOnlyEnv(env);
  const cli=safeLocalFile(whisperx_bin);
  const model=safeLocalDir(model_dir);
  const genuine_asr_ready=cli&&model&&independent_license_approved===true&&
    word_accuracy_verified===true;
  const hosted_ready=genuine_asr_ready&&authenticated_upload_live===true&&
    approval_db_live===true&&feature4_final_renderer_live===true&&
    hosted_e2e_verified===true;
  return Object.freeze({
    feature:'feature7',
    cpu_only:true,gpu_started:false,paid_inference_started:false,
    remote_model_downloads_enabled:false,
    node_cpu_environment:resolved.CUDA_VISIBLE_DEVICES==='',
    private_video_intake_source_ready:true,
    transcript_cpu_adapter_source_ready:true,
    actual_whisperx_executable_present:cli,
    actual_local_model_directory_present:model,
    independent_model_rights_confirmed:independent_license_approved===true,
    real_word_accuracy_verified:word_accuracy_verified===true,
    genuine_cpu_asr_ready:genuine_asr_ready,
    authenticated_upload_live:authenticated_upload_live===true,
    human_approval_db_live:approval_db_live===true,
    feature4_final_renderer_live:feature4_final_renderer_live===true,
    hosted_e2e_verified:hosted_e2e_verified===true,
    feature7_release_ready:hosted_ready,
    gpu_start_authorized:false,
    recommendation:'KEEP_GPU_OFF_UNTIL_SEPARATELY_APPROVED_AND_RELEASE_GATES_PASS'
  });
}
if(process.argv[1]&&import.meta.url===new URL('file://'+process.argv[1]).href){
  try{
    const report=inspectFeature7CpuReadiness({
      whisperx_bin:process.env.FEATURE7_WHISPERX_BIN,
      model_dir:process.env.FEATURE7_WHISPERX_MODEL_DIR
    });
    process.stdout.write(JSON.stringify(report,null,2)+'\n');
  }catch(e){process.stderr.write('Feature7 GPU-OFF gate: '+e.message+'\n');process.exitCode=1;}
}
