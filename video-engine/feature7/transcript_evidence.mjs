/**
 * Feature #7 private transcript provenance.
 * This is an internal service-to-service HMAC, NOT an end-user JWT or
 * authorization. Only the trusted worker may handle the secret. No UI route.
 */
import crypto from 'node:crypto';

export class TranscriptEvidenceError extends Error {}
const fail = (ok, reason) => {if (!ok) throw new TranscriptEvidenceError(reason);};
const KEY = /^[A-Za-z0-9_-]{1,120}$/;
const SHA = /^[a-f0-9]{64}$/;
const MAX_TTL_MS = 10 * 60 * 1000;
const skew = 30 * 1000;

function privateKey(key) {
  fail(Buffer.isBuffer(key) && key.length >= 32, 'Server evidence secret missing');
  return key;
}
function fields(data) {
  fail(data && typeof data === 'object' && !Array.isArray(data), 'Bad evidence payload');
  const {shop_id,asset_id,job_id,source_sha256,transcript_sha256,model_id,
    issued_at_ms,expires_at_ms} = data;
  fail([shop_id,asset_id,job_id,model_id].every(s => typeof s === 'string' && KEY.test(s)) &&
    SHA.test(source_sha256) && SHA.test(transcript_sha256) &&
    Number.isSafeInteger(issued_at_ms) && Number.isSafeInteger(expires_at_ms) &&
    issued_at_ms >= 0 && expires_at_ms > issued_at_ms &&
    expires_at_ms-issued_at_ms <= MAX_TTL_MS,
  'Invalid transcript binding or lifetime');
  return {version:'feature7_asr_evidence_v1',shop_id,asset_id,job_id,
    source_sha256,transcript_sha256,model_id,issued_at_ms,expires_at_ms};
}
function sign(payload,key) {
  return crypto.createHmac('sha256',privateKey(key)).update(
    'retailgrowth.feature7.asr.v1\n'+JSON.stringify(payload),'utf8').digest('hex');
}
export function sealTranscriptEvidence({data,key,now_ms=Date.now()}) {
  const payload=fields(data);
  fail(Number.isSafeInteger(now_ms) && payload.issued_at_ms <= now_ms+skew &&
    now_ms <= payload.expires_at_ms, 'Evidence issued too late or expired');
  return Object.freeze({...payload,mac:sign(payload,key)});
}
export function verifyTranscriptEvidence({evidence,key,expect,now_ms=Date.now()}) {
  fail(evidence && typeof evidence === 'object' && !Array.isArray(evidence),
    'Missing transcript evidence');
  const payload=fields(evidence);
  fail(evidence.version===payload.version && typeof evidence.mac==='string' &&
    SHA.test(evidence.mac) &&
    Number.isSafeInteger(now_ms) && now_ms >= payload.issued_at_ms-skew &&
    now_ms <= payload.expires_at_ms,'Expired or malformed transcript evidence');
  fail(expect && ['shop_id','asset_id','job_id','source_sha256',
    'transcript_sha256'].every(field => typeof expect[field]==='string' &&
      expect[field] === payload[field]) &&
    // Optional trusted-worker model pin: existing offline fixtures may omit it,
    // but a coordinator with a licensed/approved model must supply it.
    (expect.model_id === undefined ||
      (typeof expect.model_id === 'string' && expect.model_id === payload.model_id)),
    'Transcript evidence scope, model or digest mismatch');
  const mac=Buffer.from(evidence.mac,'hex');
  const calculated=Buffer.from(sign(payload,key),'hex');
  fail(crypto.timingSafeEqual(mac,calculated),'Transcript evidence signature mismatch');
  return Object.freeze({...payload,verified:true});
}
