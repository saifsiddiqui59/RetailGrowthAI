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
reject({review:{...review,schema:'retailgrowth.feature7-voicestudio-asr-reviewSnapshot.v1'}});
reject({review:{...review,schema:'unexpected-review-v1'}});
// Bound untrusted upstream text independently of the word-count limit.
reject({review:{...review,text:'x'.repeat(20001)}});
assert.equal(bindVoiceStudioReview({...input,review:{...review,text:'x'.repeat(20000)}}).approved,false);
reject({review:{...review,words:[{word:'x',start:1.5,end:1.0}]}});
reject({review:{...review,words:[{word:'x',start:0,end:3}]}});
reject({review:{...review,words:[{word:'\u202Ebad',start:0,end:.5}]}});
assert.throws(()=>verifyTranscriptEvidence({evidence:ok.evidence,key,
 now_ms:now,expect:{shop_id:'shopB',asset_id:'video1',job_id:'job1',
 source_sha256:video,transcript_sha256:ok.transcript.transcript_sha256}}));
// Accessors must never execute before HMAC or source/lease validation.
for (const field of ['schema','language','audio_sha256','words','text']) {
  let calls=0;
  const hostile={...review};
  Object.defineProperty(hostile,field,{enumerable:true,get(){calls++;throw Error('getter executed');}});
  reject({review:hostile});
  assert.equal(calls,0,field);
}
for (const field of ['shop_id','source_sha256','active','expires_at_ms']) {
  let calls=0;
  const hostile={...lease};
  Object.defineProperty(hostile,field,{enumerable:true,get(){calls++;throw Error('getter executed');}});
  reject({lease:hostile});
  assert.equal(calls,0,field);
}
reject({review:Object.assign(Object.create({schema:review.schema}),
  Object.fromEntries(Object.entries(review).filter(([k])=>k!=='schema')))});
reject({lease:Object.assign(Object.create({active:true}),
  Object.fromEntries(Object.entries(lease).filter(([k])=>k!=='active')))});
// Reject invalid word values before invoking the normalizer. These values
// must never reach the HMAC signing path, even if an adapter is permissive.
for (const word of [
  {word:'',start:.1,end:.5},
  {word:'x'.repeat(121),start:.1,end:.5},
  {word:'ok',start:NaN,end:.5},
  {word:'ok',start:Infinity,end:.5},
  {word:'ok',start:'0.1',end:.5},
  {word:'ok',start:.5,end:.5},
  {word:'ok',start:-.1,end:.5},
  {word:'ok',start:.1,end:2.1},
  {word:'ok',start:.1,end:null}
]) reject({review:{...review,words:[word]}});
// A long valid VoiceStudio review must pass the existing normalizer's 200-word
// per-segment limit without truncation, reordering, or changing the HMAC hash.
{
  const words=Array.from({length:201},(_,i)=>({
    word:'शब्द',start:i*.005,end:i*.005+.004
  }));
  const signed=bindVoiceStudioReview({...input,review:{...review,words}});
  assert.equal(signed.transcript.words.length,201);
  // Every original millisecond boundary and word identity survives the
  // 200-word segmentation boundary used by the existing F7 normalizer.
  for (let i=0;i<words.length;i++) {
    assert.equal(signed.transcript.words[i].word,words[i].word);
    assert.equal(signed.transcript.words[i].startMs,Math.round(words[i].start*1000));
    assert.equal(signed.transcript.words[i].endMs,Math.round(words[i].end*1000));
  }

  assert.equal(signed.whisperx_json.segments[0].words.length,201);
  assert.equal(signed.transcript.words[200].word,'शब्द');
  const tooMany=Array.from({length:2001},(_,i)=>({
    word:'शब्द',start:i*.0005,end:i*.0005+.0004
  }));
  reject({review:{...review,words:tooMany}});
}
// Array index accessors must not run even if they are own properties.
// An index getter could exfiltrate tenant identifiers or mutate lease state.
{
  let calls=0;
  const words=[...review.words];
  Object.defineProperty(words,'0',{configurable:true,enumerable:true,
    get(){calls++;throw Error('word slot getter executed');}});
  reject({review:{...review,words}});
  assert.equal(calls,0);
}
// A prototype-only array slot is sparse and cannot be trusted.
{
  const words=[...review.words];
  delete words[0];
  const inherited=Object.create(Array.prototype);
  Object.setPrototypeOf(words,inherited);
  inherited[0]=review.words[0];
  reject({review:{...review,words}});
}
// A hostile word getter must not run while building signed evidence.
for (const field of ['word','start','end']) {
  let calls=0;
  const hostile={...review.words[0]};
  Object.defineProperty(hostile,field,{enumerable:true,get(){calls++;throw Error('word getter executed');}});
  reject({review:{...review,words:[hostile,review.words[1]]}});
  assert.equal(calls,0,field);
}
reject({review:{...review,words:[,review.words[1]]}});
// A lease revoked while a word is normalized cannot be signed. A Proxy can
// mutate the authoritative lease without exposing an accessor descriptor.
for (const field of ['active','shop_id','expires_at_ms']) {
  const mutable={...lease};
  let changed=false;
  const word=new Proxy({...review.words[0]},{
    get(target,property,receiver) {
      if (property==='word' && !changed) {
        changed=true;
        mutable[field]=field==='active'?false:
          field==='shop_id'?'foreign':now-1;
      }
      return Reflect.get(target,property,receiver);
    }
  });
  reject({lease:mutable,review:{...review,words:[word,review.words[1]]}});
  assert.equal(changed,true,field);
}

// Word normalization must not allow review flags or source identity to drift.
for (const field of ['approved','renderable','language','audio_sha256','words','text']) {
  const mutable={...review};
  let changed=false;
  const first=new Proxy({...review.words[0]},{
    get(target,property,receiver) {
      if (property==='word' && !changed) {
        changed=true;
        mutable[field]=field==='approved'||field==='renderable'?true:
          field==='language'?'mr':field==='audio_sha256'?'c'.repeat(64):
          field==='words'?[...review.words]:review.text+' changed';
      }
      return Reflect.get(target,property,receiver);
    }
  });
  mutable.words=[first,review.words[1]];
  reject({review:mutable});
  assert.equal(changed,true,field);
}
// In-place array slot replacement must fail even when the review retains
// the same words-array reference and all top-level approval flags stay fixed.
{
  const mutable={...review,words:[...review.words]};
  let swapped=false;
  const first=new Proxy({...review.words[0]},{
    get(target,field,receiver) {
      if(field==='word' && !swapped) {
        swapped=true;
        mutable.words[1]={word:'forged',start:.7,end:1.2};
      }
      return Reflect.get(target,field,receiver);
    }
  });
  mutable.words[0]=first;
  reject({review:mutable});
  assert.equal(swapped,true);
}
// A word may mutate another word's values without replacing the array slot.
// The signed normalized transcript must reject this in-place TOCTOU change.
for (const field of ['word','start','end']) {
  const words=review.words.map(w=>({...w}));
  let changed=false;
  words[0]=new Proxy(words[0],{
    get(target,property,receiver) {
      if(property==='word' && !changed) {
        changed=true;
        words[1][field]=field==='word'?'forged':field==='start'?.8:1.1;
      }
      return Reflect.get(target,property,receiver);
    }
  });
  reject({review:{...review,words}});
  assert.equal(changed,true,field);
}
// A mid-normalization replacement with an accessor must not execute it.
{
  const mutable={...review};
  let getterCalls=0;
  const first=new Proxy({...review.words[0]},{
    get(target,property,receiver) {
      if(property==='word') {
        Object.defineProperty(mutable,'language',{configurable:true,
          get(){getterCalls++;throw Error('unsafe review getter');}});
      }
      return Reflect.get(target,property,receiver);
    }
  });
  mutable.words=[first,review.words[1]];
  reject({review:mutable});
  assert.equal(getterCalls,0);
}
// A Proxy's ordinary get trap must not override own-data review snapshots.
// All fields used for signing come from descriptors, not arbitrary reads.
{
  let gets=0;
  const proxy=new Proxy({...review},{
    get(target,field,receiver) {
      if (['schema','approved','renderable','language','audio_sha256','words','text'].includes(field)) {
        gets++;
        throw Error('untrusted review get trap');
      }
      return Reflect.get(target,field,receiver);
    }
  });
  const signed=bindVoiceStudioReview({...input,review:proxy});
  assert.equal(signed.evidence.source_sha256,video);
  assert.equal(signed.language,'hi');
  assert.equal(gets,0);
}
// Null-prototype records with explicit own data fields remain compatible.
assert.equal(bindVoiceStudioReview({...input,review:Object.assign(Object.create(null),review),
  lease:Object.assign(Object.create(null),lease)}).approved,false);
console.log('VoiceStudio signed handoff positive and negative cases passed');
"""
class VoiceStudioSignedHandoffTests(unittest.TestCase):
    def test_offline_bridge_and_tenant_denials(self):
        result=subprocess.run(['node','--input-type=module','--eval',SCRIPT],
            cwd=ROOT,capture_output=True,text=True,timeout=20)
        self.assertEqual(result.returncode,0,result.stdout+result.stderr)

if __name__=='__main__':
    unittest.main()
