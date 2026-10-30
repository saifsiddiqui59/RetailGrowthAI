"""Offline Feature7 reviewer async safety regression: no hosted approval or assets."""
from pathlib import Path
import shutil
import subprocess
import unittest

ROOT=Path(__file__).resolve().parents[2]
JS=r'''import assert from 'node:assert/strict';
import {proposeUploadedFootageEdits} from './video-engine/feature7/autobroll_semantics.mjs';
import {mountFeature7ReviewPanel} from './video-engine/feature7/reviewer_panel.mjs';
class FakeNode {
  constructor(tag,doc){
    this.tag=tag;this.ownerDocument=doc;this.children=[];this.handlers={};
    this.attributes={};this.value='';this.textContent='';this.checked=false;
    this.disabled=false;this.hidden=false;this.src='';
  }
  setAttribute(k,v){this.attributes[k]=v;}
  removeAttribute(k){delete this.attributes[k];if(k==='src')this.src='';}
  replaceChildren(...n){this.children=n;}
  append(...n){this.children.push(...n);}
  appendChild(n){this.children.push(n);}
  prepend(n){this.children.unshift(n);}
  addEventListener(k,f){this.handlers[k]=f;}
}
const doc={createElement(tag){return new FakeNode(tag,doc)}};
const target=new FakeNode('main',doc);
const shop='async-shop',campaign='async-campaign',asset='async-owned-source';
const draft={shop_id:shop,campaign_id:campaign,duration_seconds:15,
  scenes:[{asset_id:asset,asset_type:'video',source_feature:'retailer',duration:15,start:0}]};
const plan=proposeUploadedFootageEdits({shop_id:shop,campaign_id:campaign,draft,
  footage:[{scene_index:0,asset_id:asset,source_duration_seconds:20,
    has_audio:true,transcription_status:'verified_server',
    transcript_sha256:'a'.repeat(64),
    words:[{word:'Hello',startMs:1000,endMs:1300},
      {word:'world.',startMs:1400,endMs:1800}],broll_candidates:[]}],
  grants:[{asset_id:asset,shop_id:shop,issued_by:'trusted_server',
    source:'retailer_upload',rights_status:'APPROVED',active:true,
    media_type:'video',has_audio:true}]});
const captionProjection={version:'feature7_autoclip_autobroll_caption_projection_v1',
  shop_id:shop,asset_id:asset,approved:false,renderable:false,
  human_review_required:true,actual_timeline_duration_ms:14940,
  feature4_caption_track:[{start:1,duration:0.8,text:'Hello world'}]};
const decisions=[],captionDecisions=[],reviewDeferred=[],captionDeferred=[];
const app=mountFeature7ReviewPanel({target,draft,proposal:plan,
  media_evidence:[{asset_id:asset,local_media_verified:'LOCAL_BYTES_VERIFIED',
    source_sha256:'a'.repeat(64),source_duration_seconds:20}],
  reviewer_view:{shop_id:shop,campaign_id:campaign,reviewer_id:'reviewer-a',
    active_membership:true,role:'EDITOR',revision:3},
  caption_correction_input:{shop_id:shop,asset_id:asset,
    source_sha256:'a'.repeat(64),preview_sha256:'b'.repeat(64),
    caption_projection:captionProjection},
  onReviewRequest(packet){decisions.push(packet);
    return new Promise((resolve,reject)=>reviewDeferred.push({resolve,reject}));},
  onCaptionReviewRequest(packet){captionDecisions.push(packet);
    return new Promise((resolve,reject)=>captionDeferred.push({resolve,reject}));}});
const nodes=(n)=>[n,...n.children.flatMap(nodes)];
const select=nodes(target).find(n=>n.tag==='select'&&
  n.attributes['aria-label']==='Choose uploaded source scene');
const trim=nodes(target).find(n=>n.tag==='input'&&n.type==='range');
const approval=nodes(target).find(n=>n.tag==='button'&&
  n.textContent==='Request human approval');
const confirm=nodes(target).find(n=>n.tag==='label'&&
  n.textContent==='I have reviewed the selected clip and original speech audio.').children[0];
const feedback=nodes(target).find(n=>n.className==='rgai-f7-feedback');
confirm.checked=true;approval.handlers.click();
assert.equal(decisions.length,1);assert.equal(approval.disabled,true);
select.handlers.change();
assert.equal(approval.disabled,true,'Scene switch must not permit duplicate');
trim.value='1';trim.handlers.input();
assert.equal(approval.disabled,false);
confirm.checked=true;approval.handlers.click();
assert.equal(decisions.length,2);assert.equal(approval.disabled,true);
reviewDeferred[0].reject(new Error('stale'));await Promise.resolve();await Promise.resolve();
assert.equal(approval.disabled,true,'Old request failure reopened new request');
assert.doesNotMatch(feedback.textContent,/Request failed/);
reviewDeferred[1].reject(new Error('current'));await Promise.resolve();await Promise.resolve();
assert.equal(approval.disabled,false,'Current failed request should allow safe manual retry');
confirm.checked=true;approval.handlers.click();
assert.equal(decisions.length,3);assert.equal(approval.disabled,true);
reviewDeferred[2].resolve(false);
await Promise.resolve();await Promise.resolve();await Promise.resolve();
assert.equal(approval.disabled,false,
  'Async host refusal must release review pending lock for a manual retry');
assert.match(feedback.textContent,/Request failed/);
assert.equal(app.getReviewSnapshot().approved,false);
const field=nodes(target).find(n=>n.className==='rgai-f7-caption-correction');
const captionNodes=nodes(field);
const textarea=captionNodes.find(n=>n.tag==='textarea');
const save=captionNodes.find(n=>n.tag==='button'&&n.textContent==='Save caption suggestion');
const send=captionNodes.find(n=>n.tag==='button'&&
  n.textContent==='Request caption correction review');
const verified=captionNodes.find(n=>n.tag==='label'&&
  n.textContent==='I checked the corrected words against the actual speaker.').children[0];
const cueSelect=captionNodes.find(n=>n.tag==='select');
textarea.value='Hello store';save.handlers.click();verified.checked=true;send.handlers.click();
assert.equal(captionDecisions.length,1);assert.equal(send.disabled,true);
cueSelect.handlers.change();assert.equal(send.disabled,true,
  'Switching caption cue must not allow duplicate');
textarea.value='Hello shop';save.handlers.click();
assert.equal(send.disabled,false,'Changed caption enables new request');
verified.checked=true;send.handlers.click();
assert.equal(captionDecisions.length,2);assert.equal(send.disabled,true);
captionDeferred[0].reject(new Error('stale caption'));
await Promise.resolve();await Promise.resolve();
assert.equal(send.disabled,true,'Old caption callback reopened new request');
captionDeferred[1].reject(new Error('new caption'));
await Promise.resolve();await Promise.resolve();
assert.equal(send.disabled,false);
verified.checked=true;send.handlers.click();
assert.equal(captionDecisions.length,3);assert.equal(send.disabled,true);
captionDeferred[2].resolve(false);
await Promise.resolve();await Promise.resolve();await Promise.resolve();
assert.equal(send.disabled,false,
  'Async host refusal must release caption pending lock for a manual retry');
assert.equal(app.getReviewSnapshot().approved,false);
app.destroy();assert.equal(target.children.length,0);
process.stdout.write('OK: stale async callbacks fenced and duplicate requests denied');
'''

@unittest.skipUnless(shutil.which("node"),"Requires Node.js")
class Feature7ReviewAsyncSafetyTests(unittest.TestCase):
    def test_stale_callbacks_and_unchanged_scene_caption_switches(self):
        proc=subprocess.run(["node","--input-type=module","-e",JS],
            cwd=ROOT,text=True,capture_output=True,timeout=25)
        self.assertEqual(proc.returncode,0,proc.stderr[-3000:])
        self.assertIn("stale async callbacks fenced",proc.stdout)

if __name__=="__main__":unittest.main()
