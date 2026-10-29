"""Feature7 reviewer panel and immutable review request tests, no live auth."""
import json
from pathlib import Path
import shutil
import subprocess
import unittest
from test_feature7_semantic import sample

ROOT=Path(__file__).resolve().parents[2]
SCRIPT=r"""
import fs from 'node:fs';
import {proposeUploadedFootageEdits} from './video-engine/feature7/autobroll_semantics.mjs';
import {createReviewSession,adjustTrimStart,proposeReviewDecision}
  from './video-engine/feature7/review_actions.mjs';
import {mountFeature7ReviewPanel}
  from './video-engine/feature7/reviewer_panel.mjs';
const req=JSON.parse(fs.readFileSync(0,'utf8'));
const plan=proposeUploadedFootageEdits(req.input);
const evidence=[{asset_id:req.input.draft.scenes[0].asset_id,
  local_media_verified:'LOCAL_BYTES_VERIFIED',
  source_sha256:'a'.repeat(64),source_duration_seconds:20}];
if(req.bad==='foreign')evidence[0].asset_id='foreign-video';
if(req.bad==='too_short')evidence[0].source_duration_seconds=5;
if(req.bad==='changed_draft')req.input.draft.scenes[0].duration=12;
const reviewer={shop_id:req.input.shop_id,
  campaign_id:req.input.campaign_id,reviewer_id:'reviewer-1',
  active_membership:true,role:req.role??'OWNER',revision:3};
if(req.bad==='revoked')reviewer.active_membership=false;
let session=createReviewSession({draft:req.input.draft,
  proposal:plan,media_evidence:evidence,reviewer_view:reviewer});
if(req.operation==='actions'){
  if(req.bad==='bad_trim')session=adjustTrimStart(session,0,999);
  else session=adjustTrimStart(session,0,2);
  const result=proposeReviewDecision(session,{
    action:req.action??'REQUEST_APPROVAL',confirmed:req.confirmed??true});
  process.stdout.write(JSON.stringify(result));
}else{
  class Node {
    constructor(tag,doc){this.tag=tag;this.ownerDocument=doc;this.children=[];
      this.handlers={};this.attributes={};this.textContent='';this.hidden=false;
      this.disabled=false;this.checked=false;this.value='';}
    setAttribute(k,v){this.attributes[k]=v;}
    removeAttribute(k){delete this.attributes[k];}
    replaceChildren(...n){this.children=n;}
    append(...n){this.children.push(...n);}
    appendChild(n){this.children.push(n);}
    prepend(n){this.children.unshift(n);}
    addEventListener(k,f){this.handlers[k]=f;}
  }
  const doc={createElement(tag){return new Node(tag,doc);}};
  const target=new Node('main',doc);
  const events=[];
  const handle=mountFeature7ReviewPanel({
    target,draft:req.input.draft,proposal:plan,
    media_evidence:evidence,reviewer_view:reviewer,
    trusted_media_object_urls:{'owned-video-a':'blob:authorized-test-video'},
    onReviewRequest(packet){events.push(packet);}
  });
  const flatten=n=>[n,...n.children.flatMap(flatten)];
  const all=flatten(target);
  const video=all.find(n=>n.tag==='video');
  const checkbox=all.find(n=>n.tag==='input'&&n.type==='checkbox');
  const slider=all.find(n=>n.tag==='input'&&n.type==='range');
  const approve=all.find(n=>n.tag==='button'&&n.textContent.includes('approval'));
  if(req.operation==='ui_trim'){
    slider.value='2';
    slider.handlers.input();
    checkbox.checked=true;
  }else if(req.operation==='ui_unconfirmed'){
    checkbox.checked=false;
  }else checkbox.checked=true;
  approve.handlers.click();
  if(req.operation==='ui_double_click')approve.handlers.click();
  process.stdout.write(JSON.stringify({
    video_url:video.src,video_hidden:video.hidden,
    slider_disabled:slider.disabled,approve_disabled:approve.disabled,
    events,feedback:all.find(n=>n.className==='rgai-f7-feedback')?.textContent,
    view:handle.getReviewSnapshot()
  }));
}
"""

@unittest.skipUnless(shutil.which("node"),"Node required")
class Feature7ReviewerTests(unittest.TestCase):
    def go(self,**kwargs):
        data={"input":sample(),**kwargs}
        return subprocess.run(["node","--input-type=module","-e",SCRIPT],
          input=json.dumps(data),text=True,capture_output=True,cwd=ROOT,timeout=10)

    def test_manual_trim_outputs_review_request_not_self_approved(self):
        r=self.go(operation='actions')
        self.assertEqual(r.returncode,0,r.stderr)
        x=json.loads(r.stdout)
        self.assertTrue(x['reviewer_confirmation'])
        self.assertFalse(x['approved'])
        self.assertFalse(x['renderable'])
        self.assertEqual(x['expected_revision'],3)
        self.assertEqual(x['edited_proposal']['scenes'][0]['trim_start'],2)
        self.assertFalse(x['edited_proposal']['scenes'][0]['mute_source'])
        self.assertTrue(x['requires_authoritative_server_transaction'])

    def test_viewer_cannot_approve_or_reject(self):
        for action in ('REQUEST_APPROVAL','REJECT_PROPOSAL'):
            with self.subTest(action=action):
                r=self.go(operation='actions',role='VIEWER',action=action)
                self.assertNotEqual(r.returncode,0,r.stdout)

    def test_unconfirmed_or_invalid_trim_and_rights_denied(self):
        for change in [
          {'operation':'actions','confirmed':False},
          {'operation':'actions','bad':'bad_trim'},
          {'operation':'actions','bad':'foreign'},
          {'operation':'actions','bad':'too_short'},
          {'operation':'actions','bad':'changed_draft'},
          {'operation':'actions','bad':'revoked'}
        ]:
            with self.subTest(change=change):
                r=self.go(**change)
                self.assertNotEqual(r.returncode,0,r.stdout)

    def test_duplicate_review_click_is_deduplicated_until_edit(self):
        r=self.go(operation='ui_double_click')
        self.assertEqual(r.returncode,0,r.stderr)
        out=json.loads(r.stdout)
        self.assertEqual(len(out['events']),1)
        self.assertTrue(out['approve_disabled'])
        self.assertFalse(out['view']['approved'])

    def test_embeddable_review_panel_is_interactive_and_never_claims_approval(self):
        r=self.go(operation='ui_trim')
        self.assertEqual(r.returncode,0,r.stderr)
        x=json.loads(r.stdout)
        self.assertEqual(x['video_url'],'blob:authorized-test-video')
        self.assertFalse(x['video_hidden'])
        self.assertTrue(x['approve_disabled'])
        self.assertEqual(len(x['events']),1)
        self.assertEqual(x['events'][0]['edited_proposal']['scenes'][0]['trim_start'],2)
        self.assertFalse(x['view']['approved'])
        self.assertFalse(x['view']['renderable'])
        self.assertIn('not confirmed',x['feedback'])

    def test_panel_without_confirmation_does_not_send_approval(self):
        r=self.go(operation='ui_unconfirmed')
        self.assertEqual(r.returncode,0,r.stderr)
        self.assertEqual(json.loads(r.stdout)['events'],[])

    def test_readonly_panel_disables_all_writes(self):
        r=self.go(operation='ui_trim',role='VIEWER')
        self.assertEqual(r.returncode,0,r.stderr)
        x=json.loads(r.stdout)
        self.assertTrue(x['slider_disabled'])
        self.assertTrue(x['approve_disabled'])
        self.assertEqual(x['events'],[])

if __name__=="__main__":unittest.main()
