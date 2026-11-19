"""Deterministic pre-I/O VoiceStudio envelope denial; CPU only, no network."""
import subprocess
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = r"""
import assert from 'node:assert/strict';
import {bindVerifiedVoiceStudioMedia} from './video-engine/feature7/voicestudio_verified_media.mjs';
const sha='a'.repeat(64),key=Buffer.alloc(32,1);
let reads=0, getters=0;
const options={
  shop_id:'shopA',asset_id:'assetA',job_id:'jobA',model_id:'modelA',
  original_video_sha256:sha,original_audio_sha256:sha,
  source_duration_seconds:2,key,now_ms:1730000000000,
  readOriginalVideo:async()=>{reads++;throw Error('private video read');},
  readExtractedWav:async()=>{reads++;throw Error('private wav read');},
  readCurrentLease:async()=>{reads++;throw Error('private lease read');}
};
const reject=async review=>{
  await assert.rejects(bindVerifiedVoiceStudioMedia({...options,review}),
    /Unverified original media or lease/);
  assert.equal(reads,0,'invalid review triggered private I/O');
};
const valid={
  schema:'retailgrowth.feature7-voicestudio-asr-review.v1',
  approved:false,renderable:false,language:'hi',audio_sha256:sha,
  text:'नमस्ते',word_timings_present:true,
  model_revision_verified_by_worker:false,
  requires_feature7_signed_evidence:true,
  words:[{word:'नमस्ते',start:0,end:0.5}]
};
await reject(null);
await reject({...valid,words:[]});
await reject({...valid,words:new Array(2001).fill(valid.words[0])});
await reject({...valid,approved:true});
await reject({...valid,renderable:true});
await reject({...valid,schema:'unexpected'});
await reject({...valid,word_timings_present:false});
await reject({...valid,model_revision_verified_by_worker:true});
await reject({...valid,requires_feature7_signed_evidence:false});
for (const field of ['words','schema','approved','language','text']) {
  const hostile={...valid};
  Object.defineProperty(hostile,field,{get(){getters++;throw Error('getter invoked')}});
  await reject(hostile);
}
assert.equal(getters,0);
console.log('pre-I/O VoiceStudio review denials passed');
"""
class VoiceStudioEarlyReviewTests(unittest.TestCase):
    def test_invalid_envelopes_do_not_read_private_media(self):
        result=subprocess.run(['node','--input-type=module','--eval',SCRIPT],
            cwd=ROOT,capture_output=True,text=True,timeout=20)
        self.assertEqual(result.returncode,0,result.stdout+result.stderr)
