/**
 * Feature7 private media-rights attestation (internal service only).
 *
 * The existing issued_by marker is NOT authentication. This module signs a
 * server-validated media registry revision + exact video source bytes,
 * tenant, job ID and short expiration. Still require actual JWT/RLS checks.
 * An HMAC is not legal permission, a signed URL or upload authorization.
 */
import crypto from 'node:crypto';

export class MediaRightsEvidenceError extends Error {}
const check=(v,msg)=>{if(!v)throw new MediaRightsEvidenceError(msg);};
const KEY=/^[A-Za-z0-9_-]{1,120}$/,SHA=/^[a-f0-9]{64}$/;
const MAX_TTL=5*60*1000;
const required=['shop_id','asset_id','job_id','source_sha256','rights_revision',
 'media_type','mime_type','relative_path','issued_at_ms','expires_at_ms'];

function normalize(data){
  check(data && typeof data==='object'&&!Array.isArray(data),
    'Missing signed private media rights');
  check([data.shop_id,data.asset_id,data.job_id,data.rights_revision].every(
    v=>typeof v==='string'&&KEY.test(v))&&
    typeof data.source_sha256==='string'&&SHA.test(data.source_sha256)&&
    data.media_type==='video'&&data.mime_type==='video/mp4'&&
    typeof data.relative_path==='string'&&
    /^[A-Za-z0-9._/-]{1,220}$/.test(data.relative_path)&&
    data.relative_path.endsWith('.mp4')&&
    data.relative_path.split('/').every(p=>p!=='.'&&p!=='..'&&p.length>0)&&
    Number.isSafeInteger(data.issued_at_ms)&&
    Number.isSafeInteger(data.expires_at_ms)&&
    data.issued_at_ms>=0&&data.expires_at_ms>data.issued_at_ms&&
    data.expires_at_ms-data.issued_at_ms<=MAX_TTL,
    'Invalid signed private video scope');
  return Object.fromEntries([
    ['version','feature7_media_rights_v1'],
    ...required.map(k=>[k,data[k]])
  ]);
}
function hmac(payload,key){
  check(Buffer.isBuffer(key)&&key.length>=32,
    'Trusted server media-rights secret missing');
  return crypto.createHmac('sha256',key)
    .update('retailgrowth.feature7.media_rights.v1\n'+JSON.stringify(payload))
    .digest('hex');
}
export function sealMediaRightsEvidence({data,key,now_ms=Date.now()}={}){
  const payload=normalize(data);
  check(Number.isSafeInteger(now_ms)&&now_ms>=payload.issued_at_ms&&
    now_ms<=payload.expires_at_ms,'Cannot sign expired private rights');
  return Object.freeze({...payload,mac:hmac(payload,key)});
}
export function verifyMediaRightsEvidence({
  evidence,key,expect,now_ms=Date.now()
}={}){
  const data=normalize(evidence);
  check(evidence.version===data.version&&
    typeof evidence.mac==='string'&&SHA.test(evidence.mac)&&
    Number.isSafeInteger(now_ms)&&now_ms>=data.issued_at_ms&&
    now_ms<=data.expires_at_ms,
    'Media-rights evidence expired or malformed');
  check(expect&&
    ['shop_id','asset_id','job_id','source_sha256','relative_path',
      'rights_revision'].every(k=>expect[k]===data[k])&&
    data.media_type==='video'&&data.mime_type==='video/mp4',
    'Wrong tenant, job, rights generation or source bytes');
  const signed=Buffer.from(hmac(data,key),'hex');
  const received=Buffer.from(evidence.mac,'hex');
  check(crypto.timingSafeEqual(signed,received),
    'Invalid media-rights attestation');
  return Object.freeze({...data,verified:true});
}
