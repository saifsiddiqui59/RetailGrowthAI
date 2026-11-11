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
const wav=Buffer.concat([Buffer.from('RIFF'),Buffer.alloc(60,1)]);
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
await denied({readCurrentLease:async()=>({...lease,shop_id:'foreign'})});
let calls=0;
await denied({readCurrentLease:async()=>({...lease,active:++calls===1})});
calls=0;
await denied({readCurrentLease:async()=>({...lease,expires_at_ms:now+(++calls===1?30000:20000)})});
console.log('original bytes, Marathi captions and lease revocation denials passed');
"""
class VerifiedMediaTests(unittest.TestCase):
    def test_trusted_worker_byte_gate(self):
        result=subprocess.run(['node','--input-type=module','--eval',SCRIPT],
            cwd=ROOT,capture_output=True,text=True,timeout=30)
        self.assertEqual(result.returncode,0,result.stdout+result.stderr)
if __name__=='__main__':
    unittest.main()
