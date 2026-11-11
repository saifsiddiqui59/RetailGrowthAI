"""Deterministic original-media byte gate tests, offline Node only."""
import subprocess
import unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
SCRIPT=r"""
import assert from 'node:assert/strict';
import {createHash} from 'node:crypto';
import {bindVerifiedVoiceStudioMedia} from './video-engine/feature7/voicestudio_verified_media.mjs';
const digest=b=>createHash('sha256').update(b).digest('hex');
const video=Buffer.from('synthetic-original-video');
const wav=Buffer.alloc(44+32000);
wav.write('RIFF',0);wav.writeUInt32LE(wav.length-8,4);wav.write('WAVE',8);
wav.write('fmt ',12);wav.writeUInt32LE(16,16);wav.writeUInt16LE(1,20);
wav.writeUInt16LE(1,22);wav.writeUInt32LE(16000,24);
wav.writeUInt32LE(32000,28);wav.writeUInt16LE(2,32);
wav.writeUInt16LE(16,34);wav.write('data',36);wav.writeUInt32LE(32000,40);
const v=digest(video),a=digest(wav),now=1730000000000;
const review={schema:'retailgrowth.feature7-voicestudio-asr-review.v1',
 audio_sha256:a,language:'mr',text:'नमस्कार',words:[{word:'नमस्कार',start:.1,end:.7}],
 approved:false,renderable:false,word_timings_present:true,
 model_revision_verified_by_worker:false,requires_feature7_signed_evidence:true};
const lease={shop_id:'shop1',asset_id:'asset1',job_id:'job1',source_sha256:v,
 audio_sha256:a,model_id:'pinned',active:true,expires_at_ms:now+30000};
const base={shop_id:'shop1',asset_id:'asset1',job_id:'job1',model_id:'pinned',
 original_video_sha256:v,original_audio_sha256:a,review,key:Buffer.alloc(32,3),
 source_duration_seconds:2,now_ms:now,
 readOriginalVideo:async()=>video,readExtractedWav:async()=>wav,
 readCurrentLease:async()=>({...lease})};
const result=await bindVerifiedVoiceStudioMedia(base);
assert.equal(result.evidence.source_sha256,v);
assert.equal(result.captions[0].words[0].text,'नमस्कार');
assert.equal(result.feature4_edit_advice.executable,false);
// An audio stream longer than the original video must not be signed, even
// with authentic PCM bytes, valid SHA and an otherwise active source lease.
await assert.rejects(()=>bindVerifiedVoiceStudioMedia({
 ...base,source_duration_seconds:0.5,
 review:{...review,words:[{word:'नमस्कार',start:.1,end:.4}]}
}));
// Boundary tolerance permits only a small sample-clock rounding difference.
const nearBoundary=await bindVerifiedVoiceStudioMedia({
 ...base,source_duration_seconds:0.99,
 review:{...review,words:[{word:'नमस्कार',start:.1,end:.7}]}
});
assert.equal(nearBoundary.evidence.source_sha256,v);
const denied=async changes=>assert.rejects(()=>bindVerifiedVoiceStudioMedia({...base,...changes}));
await denied({readOriginalVideo:async()=>Buffer.from('changed')});
await denied({readExtractedWav:async()=>Buffer.alloc(64)});
await denied({readOriginalVideo:async()=>Buffer.alloc(0)});
await denied({readOriginalVideo:async()=>Buffer.alloc(256*1024*1024+1)});
await denied({readExtractedWav:async()=>Buffer.alloc(44)});
// A self-consistent digest must not authorize corrupt, compressed or truncated WAV.
const malformed=Buffer.from(wav);malformed.write('NOPE',8);
await denied({readExtractedWav:async()=>malformed,
 original_audio_sha256:digest(malformed),
 review:{...review,audio_sha256:digest(malformed)},
 readCurrentLease:async()=>({...lease,audio_sha256:digest(malformed)})});
const compressed=Buffer.from(wav);compressed.writeUInt16LE(3,20);
await denied({readExtractedWav:async()=>compressed,
 original_audio_sha256:digest(compressed),
 review:{...review,audio_sha256:digest(compressed)},
 readCurrentLease:async()=>({...lease,audio_sha256:digest(compressed)})});
const truncated=wav.subarray(0,wav.length-2);
await denied({readExtractedWav:async()=>truncated,
 original_audio_sha256:digest(truncated),
 review:{...review,audio_sha256:digest(truncated)},
 readCurrentLease:async()=>({...lease,audio_sha256:digest(truncated)})});
// Word end is bound to the exact PCM sample clock (16kHz), not a 20ms
// allowance: a self-consistent signed claim for speech beyond the audio fails.
await denied({review:{...review,words:[{word:'नमस्कार',start:.7,end:1.001}]}});
// One sample of timestamp rounding is allowed at the exact boundary.
const oneSample=await bindVerifiedVoiceStudioMedia({...base,
 review:{...review,words:[{word:'नमस्कार',start:.7,end:1+1/16000}]}});
assert.equal(oneSample.evidence.source_sha256,v);
// Larger-than-one-sample drift fails, including for otherwise valid WAV/SHA/lease.
await denied({review:{...review,words:[{word:'नमस्कार',start:.7,end:1+2/16000}]}});
// Source video is 2s, but the verified WAV contains only 1s of PCM.
// Word timings inside video bounds but outside audio bounds must not be signed.
await denied({review:{...review,words:[{word:'नमस्कार',start:1.1,end:1.4}]}});
await denied({readCurrentLease:async()=>({...lease,shop_id:'foreign'})});
let calls=0;
await denied({readCurrentLease:async()=>({...lease,active:++calls===1})});
calls=0;
await denied({readCurrentLease:async()=>({...lease,expires_at_ms:now+(++calls===1?30000:20000)})});
// Even an unchanged lease snapshot is invalid if the clock advanced past expiry
// during async source reads / evidence generation.
let clock=now;
await denied({readNowMs:()=>clock,
  readExtractedWav:async()=>{clock=now+30001;return wav;}});
clock=now;
await denied({readNowMs:()=>clock,
  readCurrentLease:async()=>{clock=now+30001;return {...lease};}});
// An injected clock that rolls backwards after signing must not revive a lease.
clock=now;
let leaseReads=0;
await denied({readNowMs:()=>clock,
  readCurrentLease:async()=>{
    clock=now+(++leaseReads===1?100:50);
    return {...lease};
  }});
// Sub-millisecond rollback cannot be hidden by integer truncation.
clock=now;leaseReads=0;
await denied({readNowMs:()=>clock,
 readCurrentLease:async()=>{
   clock=now+(++leaseReads===1?100.9:100.1);
   return {...lease};
 }});
// Fractional expiry must fail closed: 0.1ms beyond the lease is expired.
clock=now;leaseReads=0;
await denied({readNowMs:()=>clock,
 readCurrentLease:async()=>{
   clock=now+(++leaseReads===1?100:30000.1);
   return {...lease};
 }});
// A fractional but monotonic reading is valid before expiry.
clock=now;leaseReads=0;
const fractionalOk=await bindVerifiedVoiceStudioMedia({...base,
 readNowMs:()=>clock,
 readCurrentLease:async()=>{
   clock=now+(++leaseReads===1?100.1:100.9);
   return {...lease};
 }});
assert.equal(fractionalOk.evidence.source_sha256,v);
// A monotonic clock advancing across both lease reads remains valid.
clock=now;
leaseReads=0;
const monotonic=await bindVerifiedVoiceStudioMedia({...base,
  readNowMs:()=>clock,
  readCurrentLease:async()=>{
    clock=now+(++leaseReads===1?100:200);
    return {...lease};
  }});
assert.equal(monotonic.evidence.source_sha256,v);
clock=now;
await denied({readNowMs:()=>Number.NaN});
clock=now;
const signedWithClock=await bindVerifiedVoiceStudioMedia({...base,readNowMs:()=>clock});
assert.equal(signedWithClock.evidence.source_sha256,v);
// A malicious caller cannot substitute another valid source with matching
// self-declared hashes while the authoritative lease pins the original bytes.
const otherVideo=Buffer.from('synthetic-other-video');
await denied({readOriginalVideo:async()=>otherVideo,
 original_video_sha256:digest(otherVideo)});
const otherWav=Buffer.from(wav);otherWav[44]^=1;
await denied({readExtractedWav:async()=>otherWav,
 original_audio_sha256:digest(otherWav),
 review:{...review,audio_sha256:digest(otherWav)}});
// Lease changes during signing must deny, even when active and unexpired.
for (const field of ['asset_id','job_id','source_sha256','audio_sha256','model_id']) {
 let reads=0;
 await denied({readCurrentLease:async()=>{
   const current={...lease};
   if (++reads===2) current[field]=field.endsWith('sha256')?'0'.repeat(64):'changed';
   return current;
 }});
}
// A clock that expires only on the second lease check must fail closed.
clock=now;leaseReads=0;
await denied({readNowMs:()=>clock,
 readCurrentLease:async()=>{
   clock=now+(++leaseReads===1?100:30001);
   return {...lease};
 }});
// A second data chunk must not be accepted even when RIFF and SHA match.
const duplicateData=Buffer.concat([wav,Buffer.from('data'),Buffer.from([2,0,0,0]),Buffer.alloc(2)]);
duplicateData.writeUInt32LE(duplicateData.length-8,4);
await denied({readExtractedWav:async()=>duplicateData,
 original_audio_sha256:digest(duplicateData),
 review:{...review,audio_sha256:digest(duplicateData)},
 readCurrentLease:async()=>({...lease,audio_sha256:digest(duplicateData)})});
// A data chunk before fmt is not a valid bounded PCM source for signing.
const dataFirst=Buffer.concat([wav.subarray(0,12),wav.subarray(36),wav.subarray(12,36)]);
await denied({readExtractedWav:async()=>dataFirst,
 original_audio_sha256:digest(dataFirst),
 review:{...review,audio_sha256:digest(dataFirst)},
 readCurrentLease:async()=>({...lease,audio_sha256:digest(dataFirst)})});
// A legitimate odd-sized pre-audio RIFF chunk needs exactly one zero pad.
const oddChunk=Buffer.concat([Buffer.from('JUNK'),Buffer.from([1,0,0,0]),Buffer.from([7,0])]);
const padded=Buffer.concat([wav.subarray(0,12),oddChunk,wav.subarray(12)]);
padded.writeUInt32LE(padded.length-8,4);
const paddedDigest=digest(padded);
const paddedLease=()=>({...lease,audio_sha256:paddedDigest});
const paddedReview={...review,audio_sha256:paddedDigest};
const paddedSigned=await bindVerifiedVoiceStudioMedia({...base,
 readExtractedWav:async()=>padded,original_audio_sha256:paddedDigest,
 review:paddedReview,readCurrentLease:async()=>paddedLease()});
assert.equal(paddedSigned.evidence.source_sha256,v);
// Nonzero padding cannot be blessed merely by recalculating the SHA and lease.
const poisonedPad=Buffer.from(padded);poisonedPad[21]=255;
const poisonedDigest=digest(poisonedPad);
await denied({readExtractedWav:async()=>poisonedPad,
 original_audio_sha256:poisonedDigest,
 review:{...review,audio_sha256:poisonedDigest},
 readCurrentLease:async()=>({...lease,audio_sha256:poisonedDigest})});
// A missing pad byte must fail without accepting the next chunk header as padding.
const missingPad=Buffer.concat([padded.subarray(0,21),padded.subarray(22)]);
missingPad.writeUInt32LE(missingPad.length-8,4);
const missingDigest=digest(missingPad);
await denied({readExtractedWav:async()=>missingPad,
 original_audio_sha256:missingDigest,
 review:{...review,audio_sha256:missingDigest},
 readCurrentLease:async()=>({...lease,audio_sha256:missingDigest})});
// A trailing metadata chunk after samples is ambiguous and must never be signed.
const trailing=Buffer.concat([wav,Buffer.from('JUNK'),Buffer.from([4,0,0,0]),Buffer.alloc(4)]);
trailing.writeUInt32LE(trailing.length-8,4);
await denied({readExtractedWav:async()=>trailing,
 original_audio_sha256:digest(trailing),
 review:{...review,audio_sha256:digest(trailing)},
 readCurrentLease:async()=>({...lease,audio_sha256:digest(trailing)})});
// Even a zero-length trailing chunk must be denied.
const zeroTrailing=Buffer.concat([wav,Buffer.from('LIST'),Buffer.alloc(4)]);
zeroTrailing.writeUInt32LE(zeroTrailing.length-8,4);
await denied({readExtractedWav:async()=>zeroTrailing,
 original_audio_sha256:digest(zeroTrailing),
 review:{...review,audio_sha256:digest(zeroTrailing)},
 readCurrentLease:async()=>({...lease,audio_sha256:digest(zeroTrailing)})});
console.log('original bytes, Marathi captions and lease revocation denials passed');
"""
class VerifiedMediaTests(unittest.TestCase):
    def test_trusted_worker_byte_gate(self):
        result=subprocess.run(['node','--input-type=module','--eval',SCRIPT],
            cwd=ROOT,capture_output=True,text=True,timeout=30)
        self.assertEqual(result.returncode,0,result.stdout+result.stderr)
if __name__=='__main__':
    unittest.main()
