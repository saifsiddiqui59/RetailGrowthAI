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
// Validate the extracted audio container, not merely its SHA: a digest of junk
// bytes is still junk. Restrict to bounded, uncompressed PCM WAV.
function pcmWavDuration(b) {
  if (b.length<44 || b.toString('ascii',0,4)!=='RIFF' ||
      b.toString('ascii',8,12)!=='WAVE' || b.readUInt32LE(4)!==b.length-8) return null;
  let offset=12,fmt=null,data=0,byteRate=0,seenData=false;
  while (offset+8<=b.length) {
    const id=b.toString('ascii',offset,offset+4);
    const len=b.readUInt32LE(offset+4);
    const start=offset+8,end=start+len;
    if (end>b.length) return null;
    // No chunks may follow PCM samples: reject appended payloads even when RIFF
    // length and attacker-supplied digest are internally consistent.
    if (seenData) return null;
    if (id==='fmt ') {
      if (fmt!==null || len<16) return null;
      const format=b.readUInt16LE(start),channels=b.readUInt16LE(start+2);
      const rate=b.readUInt32LE(start+4),declaredByteRate=b.readUInt32LE(start+8);
      const align=b.readUInt16LE(start+12),bits=b.readUInt16LE(start+14);
      if (format!==1 || channels<1 || channels>2 || rate<8000 || rate>48000 ||
          bits!==16 || align!==channels*2 || declaredByteRate!==rate*align) return null;
      fmt=align;
      byteRate=rate*align;
    }
    if (id==='data') {if (seenData || fmt===null || len===0) return null;seenData=true;data=len;}
    // RIFF odd-sized chunks require a zero pad byte. Do not sign ambiguous
    // hidden payload bytes, even if an attacker supplies a matching digest.
    if (len%2 && (end>=b.length || b[end]!==0)) return null;
    offset=end+(len%2);
  }
  return offset===b.length && fmt!==null && seenData && data>0 && data%fmt===0
    ? data/byteRate : null;
}
export async function bindVerifiedVoiceStudioMedia({
  readOriginalVideo,readExtractedWav,readCurrentLease,
  original_video_sha256,original_audio_sha256,
  shop_id,asset_id,job_id,model_id,review,key,
  source_duration_seconds,now_ms=Date.now(),readNowMs
}={}) {
  deny([readOriginalVideo,readExtractedWav,readCurrentLease].every(f=>typeof f==='function') &&
    SHA.test(original_video_sha256??'') && SHA.test(original_audio_sha256??'') &&
    Number.isSafeInteger(now_ms) &&
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
    deny(Number.isFinite(t) && t>=lastCheckedMs && t<=Number.MAX_SAFE_INTEGER);
    lastCheckedMs=Math.floor(t);
    return lastCheckedMs;
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
    source_duration_seconds>0 && wavDuration<=source_duration_seconds+0.02 &&
    sha(wav)===original_audio_sha256);
  // A valid HMAC must never bless word offsets beyond the actual PCM sample clock.
  // The original video may be longer than the extracted speech segment.
  deny(Array.isArray(review?.words) && review.words.every(w=>
    Number.isFinite(w?.end) && w.end<=wavDuration+0.02));
  const lease=await readCurrentLease({shop_id,asset_id,job_id});
  const signed=bindVoiceStudioReview({review,shop_id,asset_id,job_id,
    original_video_sha256,original_audio_sha256,source_duration_seconds,
    lease,model_id,key,now_ms:checkedTime()});
  // Fail closed if revocation/scope changes during the signing operation.
  const current=await readCurrentLease({shop_id,asset_id,job_id});
  deny(current && current.active===true &&
    ['shop_id','asset_id','job_id','source_sha256','audio_sha256','model_id','expires_at_ms']
      .every(field=>current[field]===lease[field]) &&
    current.expires_at_ms>checkedTime());
  return signed;
}
