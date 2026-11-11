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
export async function bindVerifiedVoiceStudioMedia({
  readOriginalVideo,readExtractedWav,readCurrentLease,
  original_video_sha256,original_audio_sha256,
  shop_id,asset_id,job_id,model_id,review,key,
  source_duration_seconds,now_ms=Date.now()
}={}) {
  deny([readOriginalVideo,readExtractedWav,readCurrentLease].every(f=>typeof f==='function') &&
    SHA.test(original_video_sha256??'') && SHA.test(original_audio_sha256??'') &&
    Number.isSafeInteger(now_ms));
  // Bounded buffers: no file paths, URLs, user-provided digests as substitutes.
  const video=await readOriginalVideo({shop_id,asset_id,job_id});
  deny(Buffer.isBuffer(video) && video.length>0 && video.length<=256*1024*1024);
  deny(sha(video)===original_video_sha256);
  const wav=await readExtractedWav({shop_id,asset_id,job_id,video_sha256:original_video_sha256});
  deny(Buffer.isBuffer(wav) && wav.length>=44 && wav.length<=64*1024*1024);
  deny(sha(wav)===original_audio_sha256);
  const lease=await readCurrentLease({shop_id,asset_id,job_id});
  const signed=bindVoiceStudioReview({review,shop_id,asset_id,job_id,
    original_video_sha256,original_audio_sha256,source_duration_seconds,
    lease,model_id,key,now_ms});
  // Fail closed if revocation/scope changes during the signing operation.
  const current=await readCurrentLease({shop_id,asset_id,job_id});
  deny(current && current.active===true &&
    ['shop_id','asset_id','job_id','source_sha256','audio_sha256','model_id','expires_at_ms']
      .every(field=>current[field]===lease[field]) &&
    current.expires_at_ms>now_ms);
  return signed;
}
