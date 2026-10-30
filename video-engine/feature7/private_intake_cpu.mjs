/**
 * Feature7 CPU-only private video intake for trusted/offline workers.
 *
 * This is NOT a public upload endpoint, RLS, user auth or an approved media
 * registry. The caller must supply an authenticated server-side current
 * membership/authorization function, never a browser-provided grant.
 * Stores a private unapproved MP4 and probes its bytes. Never auto-approves,
 * publishes, transcribes or generates a signed playback URL.
 */
import fs from 'node:fs';
import path from 'node:path';
import crypto from 'node:crypto';
import {verifyPrivateVideo} from './media_preflight.mjs';

export class PrivateIntakeError extends Error {}
const check=(ok,msg)=>{if(!ok)throw new PrivateIntakeError(msg);};
const ID=/^[A-Za-z0-9_-]{1,120}$/;
const SHA=/^[a-f0-9]{64}$/;
const MAX=128*1024*1024;
const O=fs.constants;
function currentAuthorization(auth,shop_id,asset_id){
  return auth&&auth.shop_id===shop_id&&auth.asset_id===asset_id&&
    auth.active_membership===true&&
    ['OWNER','EDITOR'].includes(auth.role)&&
    auth.intake_authorized===true&&auth.video_rights_declared===true&&
    Number.isInteger(auth.max_bytes)&&auth.max_bytes>0&&
    auth.max_bytes<=MAX;
}
function directory(p){
  const st=fs.lstatSync(p);
  check(st.isDirectory()&&!st.isSymbolicLink(),'Private storage cannot be linked');
  return fs.realpathSync(p);
}
function safeDestination(root,shop){
  check(typeof root==='string'&&path.isAbsolute(root),'Absolute private root required');
  check(ID.test(shop),'Invalid shop identifier');
  const abs=directory(root);
  const shopDir=path.join(abs,shop);
  fs.mkdirSync(shopDir,{recursive:true,mode:0o700});
  check(directory(shopDir)===shopDir,'Private shop directory escaped root');
  return {abs,shopDir};
}
export function stagePrivateFootageCPU({
  source_path,private_root,shop_id,asset_id,expected_sha256,
  getCurrentIntakeAuthorization,now_ms=Date.now()
}={}){
  check([shop_id,asset_id].every(x=>typeof x==='string'&&ID.test(x)) &&
    typeof getCurrentIntakeAuthorization==='function' &&
    Number.isSafeInteger(now_ms) && now_ms>=0,
  'Current trusted video intake authorization required');
  check(typeof source_path==='string'&&path.isAbsolute(source_path),
    'Only a server-staged absolute local MP4 source is supported');
  // Auth callback MUST use current server JWT membership and upload policy.
  const auth=getCurrentIntakeAuthorization({shop_id,asset_id});
  check(currentAuthorization(auth,shop_id,asset_id),
    'Current OWNER/EDITOR and bounded video intake authorization required');
  // A trusted backend may supply an immutable registry revision. If supplied,
  // it must remain unchanged throughout the intake; this is not a DB lease.
  check(auth.authorization_revision===undefined||
    (typeof auth.authorization_revision==='string'&&
      /^[A-Za-z0-9_-]{1,128}$/.test(auth.authorization_revision)),
    'Invalid intake authorization revision');
  const initialRevision=auth.authorization_revision;
  check(expected_sha256===undefined||
    (typeof expected_sha256==='string'&&SHA.test(expected_sha256)),
  'Invalid expected video digest');

  const srcStat=fs.lstatSync(source_path);
  check(srcStat.isFile()&&!srcStat.isSymbolicLink()&&
    srcStat.size>12&&srcStat.size<=auth.max_bytes,
  'Linked, oversized or invalid staged source');
  const fd=fs.openSync(source_path,O.O_RDONLY|(O.O_NOFOLLOW??0));
  let bytes;
  try {
    const st=fs.fstatSync(fd);
    check(st.isFile()&&st.size>12&&st.size<=auth.max_bytes&&
      st.size===srcStat.size&&st.ino===srcStat.ino,
      'Staged source changed during intake');
    bytes=Buffer.alloc(st.size);
    let offset=0;
    while(offset<bytes.length){
      const n=fs.readSync(fd,bytes,offset,bytes.length-offset,offset);
      check(n>0,'Staged source ended unexpectedly');
      offset+=n;
    }
    const after=fs.fstatSync(fd);
    check(after.size===st.size&&after.mtimeMs===st.mtimeMs,
      'Staged source changed during intake');
  } finally {fs.closeSync(fd);}
  check(bytes.toString('ascii',4,8)==='ftyp','Invalid MP4 file signature');
  const sha=crypto.createHash('sha256').update(bytes).digest('hex');
  check(expected_sha256===undefined||sha===expected_sha256,
    'Staged file hash differs from approved intake expectation');
  const {shopDir}=safeDestination(private_root,shop_id);
  const relative_path=shop_id+'/'+asset_id+'.mp4';
  const final=path.join(shopDir,asset_id+'.mp4');
  const temp=path.join(shopDir,'.'+asset_id+'.'+crypto.randomBytes(8).toString('hex')+'.tmp');
  let stored=false;
  try {
    const out=fs.openSync(temp,O.O_WRONLY|O.O_CREAT|O.O_EXCL|(O.O_NOFOLLOW??0),0o600);
    try {
      fs.writeFileSync(out,bytes);
      fs.fsyncSync(out);
    } finally {fs.closeSync(out);}
    // link() is atomic NO-REPLACE: existing media is never overwritten.
    fs.linkSync(temp,final);
    stored=true;
    const internalProbeGrant={
      shop_id,asset_id,issued_by:'trusted_server',source:'retailer_upload',
      active:true,rights_status:'APPROVED',media_type:'video',
      mime_type:'video/mp4',relative_path,sha256:sha
    };
    // Transient probe grant is NOT returned. This is file validation only.
    const probe=verifyPrivateVideo({
      shop_id,asset_id,grant:internalProbeGrant,
      root:private_root,relative_path,expected_sha256:sha
    });
    check(probe.bytes<=auth.max_bytes,'Media over server intake quota');
    // Re-query the authoritative callback AFTER staging and probing. If the
    // membership, rights, quota or optional registry revision changed during
    // the CPU work, the catch block removes the newly staged private object.
    // Production still requires a transaction/lease and current JWT/RLS.
    const fresh=getCurrentIntakeAuthorization({shop_id,asset_id});
    check(currentAuthorization(fresh,shop_id,asset_id)&&
      probe.bytes<=fresh.max_bytes&&
      (initialRevision===undefined||
        fresh.authorization_revision===initialRevision),
      'Intake authorization revoked or changed during staging');
    return Object.freeze({
      shop_id,asset_id,relative_path,source_sha256:sha,
      bytes:probe.bytes,width:probe.width,height:probe.height,
      duration_seconds:probe.duration_seconds,has_audio:probe.has_audio,
      video_codec:probe.video_codec,audio_codec:probe.audio_codec,
      gpu_started:false,model_calls:0,network_calls:0,
      media_rights_status:'PENDING_INDEPENDENT_REVIEW',
      registration_status:'NOT_REGISTERED_IN_SUPABASE',
      approved:false,renderable:false,
      requires_current_jwt_rls_and_registry:true
    });
  }catch(e){
    if(stored)fs.rmSync(final,{force:true});
    throw e;
  }finally{
    fs.rmSync(temp,{force:true});
    bytes.fill(0);
  }
}
