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
clock=now;
await denied({readNowMs:()=>Number.NaN});
clock=now;
const signedWithClock=await bindVerifiedVoiceStudioMedia({...base,readNowMs:()=>clock});
assert.equal(signedWithClock.evidence.source_sha256,v);
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
console.log('original bytes, Marathi captions and lease revocation denials passed');
"""
class VerifiedMediaTests(unittest.TestCase):
    def test_trusted_worker_byte_gate(self):
        result=subprocess.run(['node','--input-type=module','--eval',SCRIPT],
            cwd=ROOT,capture_output=True,text=True,timeout=30)
        self.assertEqual(result.returncode,0,result.stdout+result.stderr)
if __name__=='__main__':
    unittest.main()
