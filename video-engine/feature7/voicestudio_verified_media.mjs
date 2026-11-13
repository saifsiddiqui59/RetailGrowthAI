/** Offline trusted-worker byte gate for Feature7 VoiceStudio evidence.
 * No browser/HTTP entrypoint, no model invocation, no persistence.
 * Readers must be bound by the caller to current authenticated tenant context.
 */
import {createHash} from 'node:crypto';
import {bindVoiceStudioReview} from './voicestudio_signed_handoff.mjs';
import {EditValidationError} from './autobroll_semantics.mjs';
const deny=(ok)=>{if(!ok)throw new EditValidationError('Unverified original media or lease');};
const sha=b=>createHash('sha256').update(b).digest('hex');
const SHA=/^[a-f0-9]{64}$/;
// Lease receipts must contain own, ordinary data properties. Accessors can
// return different scopes or expiry values during snapshot and final checks.
const LEASE_FIELDS=['shop_id','asset_id','job_id','source_sha256',
  'audio_sha256','model_id','active','expires_at_ms'];
function leaseValues(receipt) {
  deny(receipt!==null && typeof receipt==='object');
  const values=Object.create(null);
  for (const field of LEASE_FIELDS) {
    const descriptor=Object.getOwnPropertyDescriptor(receipt,field);
    deny(descriptor && Object.hasOwn(descriptor,'value'));
    values[field]=descriptor.value;
  }
  return values;
}
// Validate the extracted audio container, not merely its SHA: a digest of junk
// bytes is still junk. Restrict to bounded, uncompressed PCM WAV.
function pcmWavDuration(b) {
  if (b.length<44 || b.toString('ascii',0,4)!=='RIFF' ||
      b.toString('ascii',8,12)!=='WAVE' || b.readUInt32LE(4)!==b.length-8) return null;
  let offset=12,fmt=null,data=0,byteRate=0,sampleRate=0,seenData=false;
  // Bound chunk-walking work independently of byte size: a 64 MiB file can
  // otherwise contain millions of empty metadata chunks before PCM samples.
  // Reject excessive metadata even when the overall WAV byte limit is respected.
  let chunkCount=0, metadataBytes=0;
  while (offset+8<=b.length) {
    if (++chunkCount>128) return null;
    // RIFF chunk identifiers are printable four-byte ASCII FourCCs. Do not
    // silently skip binary/control identifiers with attacker-pinned digests.
    for (let i=offset;i<offset+4;i++) if (b[i]<0x20 || b[i]>0x7e) return null;
    const id=b.toString('ascii',offset,offset+4);
    const len=b.readUInt32LE(offset+4);
    const start=offset+8,end=start+len;
    if (end>b.length) return null;
    // No chunks may follow PCM samples: reject appended payloads even when RIFF
    // length and attacker-supplied digest are internally consistent.
    if (seenData) return null;
    // A valid PCM digest must not conceal tens of MiB of non-audio payload.
    // Bound all pre-audio metadata together, including padding and fmt bytes.
    if (id!=='data') {
      metadataBytes+=8+len+(len%2);
      if (metadataBytes>1024*1024) return null;
    }
    if (id==='fmt ') {
      if (fmt!==null || len<16) return null;
      const format=b.readUInt16LE(start),channels=b.readUInt16LE(start+2);
      const rate=b.readUInt32LE(start+4),declaredByteRate=b.readUInt32LE(start+8);
      const align=b.readUInt16LE(start+12),bits=b.readUInt16LE(start+14);
      // Plain PCM fmt is 16 bytes; the only supported extended PCM fmt is
      // WAVEFORMATEX with cbSize=0. Reject opaque extra format metadata.
      if ((len!==16 && (len!==18 || b.readUInt16LE(start+16)!==0)) ||
          format!==1 || channels<1 || channels>2 || rate<8000 || rate>48000 ||
          bits!==16 || align!==channels*2 || declaredByteRate!==rate*align) return null;
      fmt=align;
      byteRate=rate*align;
      sampleRate=rate;
    }
    if (id==='data') {if (seenData || fmt===null || len===0) return null;seenData=true;data=len;}
    // RIFF odd-sized chunks require a zero pad byte. Do not sign ambiguous
    // hidden payload bytes, even if an attacker supplies a matching digest.
    if (len%2 && (end>=b.length || b[end]!==0)) return null;
    offset=end+(len%2);
  }
  return offset===b.length && fmt!==null && seenData && data>0 && data%fmt===0
    ? {seconds:data/byteRate,sampleRate} : null;
}
export async function bindVerifiedVoiceStudioMedia({
  readOriginalVideo,readExtractedWav,readCurrentLease,
  original_video_sha256,original_audio_sha256,
  shop_id,asset_id,job_id,model_id,review,key,
  source_duration_seconds,now_ms=Date.now(),readNowMs
}={}) {
  deny([readOriginalVideo,readExtractedWav,readCurrentLease].every(f=>typeof f==='function') &&
    SHA.test(original_video_sha256??'') && SHA.test(original_audio_sha256??'') &&
    // Reject impossible source clocks before invoking private media readers.
    // Otherwise invalid requests can force up to 320 MiB of unnecessary I/O.
    Number.isFinite(source_duration_seconds) && source_duration_seconds>0 &&
    source_duration_seconds<=180 &&
    Number.isSafeInteger(now_ms) && now_ms>=0 &&
    Number.isSafeInteger(now_ms+600000) &&
    (readNowMs===undefined || typeof readNowMs==='function'));
  // Track elapsed time across asynchronous media reads; a lease can expire
  // even if its snapshot is unchanged. An injected clock is for offline tests.
  const started=performance.now();
  const currentTime=()=>readNowMs ? readNowMs() : now_ms+Math.max(0,performance.now()-started);
  // Never allow an injected or system clock to move backwards between lease checks.
  // A rollback could otherwise make an expired lease appear active at return.
  let lastCheckedMs=now_ms;
  const checkedTime=()=>{
    const t=currentTime();
    // Compare raw readings before integer conversion. Flooring first masks
    // backwards sub-millisecond jumps at lease expiry boundaries.
    deny(Number.isFinite(t) && t>=lastCheckedMs && t<=Number.MAX_SAFE_INTEGER);
    lastCheckedMs=t;
    // Round UP so a lease cannot survive by truncating a fractional ms.
    return Math.ceil(t);
  };
  // Bounded buffers: no file paths, URLs, user-provided digests as substitutes.
  const video=await readOriginalVideo({shop_id,asset_id,job_id});
  deny(Buffer.isBuffer(video) && video.length>0 && video.length<=256*1024*1024);
  deny(sha(video)===original_video_sha256);
  const wav=await readExtractedWav({shop_id,asset_id,job_id,video_sha256:original_video_sha256});
  deny(Buffer.isBuffer(wav) && wav.length>=44 && wav.length<=64*1024*1024);
  const wavDuration=pcmWavDuration(wav);
  // An extracted full-source WAV cannot contain more PCM time than its
  // claimed original video. Otherwise valid signed words could refer to
  // fabricated audio beyond the video timeline.
  deny(wavDuration!==null && Number.isFinite(source_duration_seconds) &&
    source_duration_seconds>0 &&
    wavDuration.seconds<=source_duration_seconds+1/wavDuration.sampleRate &&
    sha(wav)===original_audio_sha256);
  // A valid HMAC must never bless word offsets beyond the actual PCM sample clock.
  // Permit at most one PCM sample for decimal timestamp rounding, not a 20ms
  // interval that could sign words with no corresponding original audio.
  // The original video may be longer than the extracted speech segment.
  // Reject oversized ASR responses before iterating over attacker-supplied words.
  // The signed transcript contract allows at most 2000 words.
  // Snapshot exact ASR word fields before checking the PCM clock. Accessor-backed
  // or inherited fields could change after the clock check but before HMAC
  // signing, allowing a different word timeline to be signed.
  // The review's words property itself is untrusted. Read its descriptor
  // before inspecting length or entries: an accessor can execute arbitrary
  // code before any lease/source evidence is validated.
  deny(review!==null && typeof review==='object');
  const wordsDescriptor=Object.getOwnPropertyDescriptor(review,'words');
  deny(wordsDescriptor && Object.hasOwn(wordsDescriptor,'value'));
  const reviewWords=wordsDescriptor.value;
  deny(Array.isArray(reviewWords) && reviewWords.length>=1 &&
    reviewWords.length<=2000);
  // Never dispatch through an upstream array's overridable map method or
  // read accessor-backed array indices. Sparse words are not timing evidence.
  const words=Array.from({length:reviewWords.length},(_,index)=>{
    const entry=Object.getOwnPropertyDescriptor(reviewWords,String(index));
    deny(entry && Object.hasOwn(entry,'value'));
    const w=entry.value;
    deny(w!==null && typeof w==='object');
    const values=Object.create(null);
    for (const field of ['word','start','end']) {
      const descriptor=Object.getOwnPropertyDescriptor(w,field);
      deny(descriptor && Object.hasOwn(descriptor,'value'));
      values[field]=descriptor.value;
    }
    return values;
  });
  deny(words.every(w=>Number.isFinite(w.end) &&
    w.end<=wavDuration.seconds+1/wavDuration.sampleRate));
  // Snapshot only the upstream review contract's own data properties. Object
  // spread executes arbitrary metadata getters and can change the source digest,
  // language or approval flags after the PCM clock has been verified.
  const stableReview=Object.create(null);
  for (const field of ['schema','audio_sha256','language','text','approved',
    'renderable','word_timings_present','model_revision_verified_by_worker',
    'requires_feature7_signed_evidence']) {
    const descriptor=Object.getOwnPropertyDescriptor(review,field);
    deny(descriptor && Object.hasOwn(descriptor,'value'));
    stableReview[field]=descriptor.value;
  }
  stableReview.words=words;
  const lease=await readCurrentLease({shop_id,asset_id,job_id});
  // Snapshot the first lease: a storage adapter may reuse and mutate its object
  // on the second read. Comparing two aliases would silently accept revocation.
  // A revoked or malformed lease must not be allowed to mutate the worker's
  // source/review inputs through a reused object reference. Capture only the
  // expected lease fields, never trust inherited prototype properties.
  const leaseSnapshot=leaseValues(lease);
  const signed=bindVoiceStudioReview({review:stableReview,shop_id,asset_id,job_id,
    original_video_sha256,original_audio_sha256,source_duration_seconds,
    lease:leaseSnapshot,model_id,key,now_ms:checkedTime()});
  // Fail closed if revocation/scope changes during the signing operation.
  const current=await readCurrentLease({shop_id,asset_id,job_id});
  // The final receipt must be an authoritative own-field snapshot too;
  // inherited active/scope fields cannot revive a revoked or swapped lease.
  const finalLease=leaseValues(current);
  deny(finalLease.active===true &&
    ['shop_id','asset_id','job_id','source_sha256','audio_sha256','model_id','expires_at_ms']
      .every(field=>finalLease[field]===leaseSnapshot[field]) &&
    finalLease.expires_at_ms>checkedTime());
  return signed;
}
