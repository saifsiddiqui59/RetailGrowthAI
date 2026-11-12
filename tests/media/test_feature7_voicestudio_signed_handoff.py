"""Offline Node bridge tests; no model, network, cloud or GPU."""
import subprocess
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
SCRIPT=r"""
import assert from 'node:assert/strict';
import {bindVoiceStudioReview} from './video-engine/feature7/voicestudio_signed_handoff.mjs';
import {verifyTranscriptEvidence} from './video-engine/feature7/transcript_evidence.mjs';
const video='a'.repeat(64),audio='b'.repeat(64),key=Buffer.alloc(32,7);
const now=1730000000000;
const review={schema:'retailgrowth.feature7-voicestudio-asr-review.v1',
 audio_sha256:audio,language:'hi',text:'नमस्ते दुनिया',
 words:[{word:'नमस्ते',start:.1,end:.5},{word:'दुनिया',start:.7,end:1.2}],
 approved:false,renderable:false,word_timings_present:true,
 model_revision_verified_by_worker:false,requires_feature7_signed_evidence:true};
const lease={shop_id:'shopA',asset_id:'video1',job_id:'job1',
 source_sha256:video,audio_sha256:audio,model_id:'licensed-pin',
 active:true,expires_at_ms:now+60000};
const input={review,shop_id:'shopA',asset_id:'video1',job_id:'job1',
 original_video_sha256:video,original_audio_sha256:audio,
 source_duration_seconds:2,lease,model_id:'licensed-pin',key,now_ms:now};
const ok=bindVoiceStudioReview(input);
assert.equal(ok.evidence.source_sha256,video);
assert.equal(ok.transcript.words[0].word,'नमस्ते');
assert.equal(ok.captions[0].words[0].text,'नमस्ते');
assert.equal(ok.approved,false);
assert.equal(ok.feature4_edit_advice.executable,false);
verifyTranscriptEvidence({evidence:ok.evidence,key,now_ms:now,
 expect:{shop_id:'shopA',asset_id:'video1',job_id:'job1',
 source_sha256:video,transcript_sha256:ok.transcript.transcript_sha256,
 model_id:'licensed-pin'}});
const reject=(patch)=>assert.throws(()=>bindVoiceStudioReview({...input,...patch}));
reject({shop_id:'shopB'});
reject({original_video_sha256:'c'.repeat(64)});
reject({original_audio_sha256:'c'.repeat(64)});
reject({model_id:'other'});
reject({now_ms:now+60001});
// Never permit negative or overflowing clocks to produce signed lease evidence.
reject({now_ms:-1,lease:{...lease,expires_at_ms:60000}});
reject({now_ms:Number.MAX_SAFE_INTEGER-599999,
 lease:{...lease,expires_at_ms:Number.MAX_SAFE_INTEGER}});
reject({now_ms:1.5});
reject({lease:{...lease,active:false}});
reject({lease:{...lease,job_id:'foreign'}});
reject({review:{...review,approved:true}});
reject({review:{...review,words:[{word:'x',start:1.5,end:1.0}]}});
reject({review:{...review,words:[{word:'x',start:0,end:3}]}});
reject({review:{...review,words:[{word:'\u202Ebad',start:0,end:.5}]}});
assert.throws(()=>verifyTranscriptEvidence({evidence:ok.evidence,key,
 now_ms:now,expect:{shop_id:'shopB',asset_id:'video1',job_id:'job1',
 source_sha256:video,transcript_sha256:ok.transcript.transcript_sha256}}));
console.log('VoiceStudio signed handoff positive and negative cases passed');
"""
class VoiceStudioSignedHandoffTests(unittest.TestCase):
    def test_offline_bridge_and_tenant_denials(self):
        result=subprocess.run(['node','--input-type=module','--eval',SCRIPT],
            cwd=ROOT,capture_output=True,text=True,timeout=20)
        self.assertEqual(result.returncode,0,result.stdout+result.stderr)

if __name__=='__main__':
    unittest.main()
