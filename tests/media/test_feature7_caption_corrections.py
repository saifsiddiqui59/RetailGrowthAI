"""Human caption correction suggestions in existing Feature7 reviewer, not F4 publish."""
import json
from pathlib import Path
import shutil
import subprocess
import unittest
from test_feature7_semantic import sample

ROOT=Path(__file__).resolve().parents[2]
JS=r"""
import fs from 'node:fs';
import {proposeUploadedFootageEdits}
 from './video-engine/feature7/autobroll_semantics.mjs';
import {createCaptionCorrectionSession,editCaptionCorrection,
 requestCaptionCorrectionReview} from './video-engine/feature7/caption_corrections.mjs';
import {mountFeature7ReviewPanel} from './video-engine/feature7/reviewer_panel.mjs';
const p=JSON.parse(fs.readFileSync(0,'utf8'));
const draft=p.input.draft;
const shop=p.input.shop_id,asset=draft.scenes[0].asset_id;
const reviewer={shop_id:shop,campaign_id:p.input.campaign_id,
 reviewer_id:'human-test-editor',role:p.role??'EDITOR',
 active_membership:true,revision:3};
const projection={
 version:'feature7_autoclip_autobroll_caption_projection_v1',
 shop_id:shop,asset_id:asset,approved:false,renderable:false,
 human_review_required:true,actual_timeline_duration_ms:14940,
 feature4_caption_track:[
  {start:.55,duration:1.05,text:'Our red shirts'},
  {start:3.15,duration:.80,text:'are in the shop'},
  {start:8.40,duration:.95,text:'Browse today'}
 ]};
const correctionInput={shop_id:shop,asset_id:asset,
 source_sha256:'a'.repeat(64),preview_sha256:'b'.repeat(64),
 caption_projection:projection};
if(p.bad==='foreign')correctionInput.shop_id='outside-shop';
if(p.bad==='unsafecue')projection.feature4_caption_track[0].text='<b>words</b>';
if(p.bad==='overlap')projection.feature4_caption_track[1].start=.8;
if(p.bad==='late')projection.feature4_caption_track[2].start=15;
if(p.bad==='approved')projection.approved=true;
if(p.bad==='samesha')correctionInput.preview_sha256=correctionInput.source_sha256;
if(p.operation==='pure'){
 let s=createCaptionCorrectionSession({...correctionInput,reviewer_view:reviewer});
 const original=s;
 if(p.bad==='wrong_index')s=editCaptionCorrection(s,8,'Different words');
 else s=editCaptionCorrection(s,0,p.edit??'Our blue shirts');
 if(p.reset)s=editCaptionCorrection(s,0,'Our red shirts');
 const result=p.bad==='unconfirmed'
  ? requestCaptionCorrectionReview(s,{confirmed:false})
  : p.emit===false?null:requestCaptionCorrectionReview(s,{confirmed:true});
 process.stdout.write(JSON.stringify({original:original.corrections,
  session:s,request:result}));
}else{
 const plan=proposeUploadedFootageEdits(p.input);
 const evidence=[{asset_id:asset,local_media_verified:'LOCAL_BYTES_VERIFIED',
  source_sha256:'a'.repeat(64),source_duration_seconds:20}];
 class FakeNode{
  constructor(tag,doc){this.tag=tag;this.ownerDocument=doc;this.children=[];
   this.handlers={};this.attributes={};this.value='';this.textContent='';
   this.checked=false;this.disabled=false;this.hidden=false;}
  setAttribute(k,v){this.attributes[k]=v;}
  removeAttribute(k){delete this.attributes[k];}
  replaceChildren(...n){this.children=n;}
  append(...n){this.children.push(...n);}
  appendChild(n){this.children.push(n);}
  prepend(n){this.children.unshift(n);}
  addEventListener(k,f){this.handlers[k]=f;}
 }
 const doc={createElement(t){return new FakeNode(t,doc)}};
 const target=new FakeNode('main',doc);
 const events=[];
 const callbacks={
  target,draft,proposal:plan,media_evidence:evidence,
  reviewer_view:reviewer,
  caption_correction_input:correctionInput,
  onReviewRequest(){throw Error('No scene approval was requested')},
 };
 if(p.bad!=='no_callback')callbacks.onCaptionReviewRequest=
   (packet)=>{events.push(packet)};
 const mounted=mountFeature7ReviewPanel(callbacks);
 const nodes=n=>[n,...n.children.flatMap(nodes)];
 const all=nodes(target);
 const textarea=all.find(n=>n.tag==='textarea');
 const buttons=all.filter(n=>n.tag==='button');
 const save=buttons.find(n=>n.textContent==='Save caption suggestion');
 const submit=buttons.find(n=>n.textContent==='Request caption correction review');
 const captionField=all.find(n=>n.className==='rgai-f7-caption-correction');
 const confirm=nodes(captionField).find(n=>n.tag==='input'&&n.type==='checkbox');
 const feedback=nodes(captionField).find(n=>n.tag==='p'&&n.attributes['aria-live']==='polite');
 textarea.value=p.edit??'Our blue shirts';
 save.handlers.click();
 if(p.operation==='ui_confirmed')confirm.checked=true;
 submit.handlers.click();
 process.stdout.write(JSON.stringify({
  editor_disabled:textarea.disabled,save_disabled:save.disabled,
  submit_disabled:submit.disabled,events,
  caption_review_count:mounted.getReviewSnapshot().caption_correction_count,
  feedback:feedback.textContent
 }));
}
"""
@unittest.skipUnless(shutil.which("node"),"Requires Node.js")
class Feature7CaptionCorrectionTests(unittest.TestCase):
    def run_case(self,**options):
        return subprocess.run(["node","--input-type=module","-e",JS],
            input=json.dumps({"input":sample(),**options}),
            cwd=ROOT,text=True,capture_output=True,timeout=20)

    def test_correction_never_changes_source_timing_or_approves_output(self):
        r=self.run_case(operation="pure")
        self.assertEqual(r.returncode,0,r.stderr)
        out=json.loads(r.stdout)
        self.assertEqual(out["original"],[])
        session=out["session"]
        self.assertFalse(session["approved"])
        self.assertFalse(session["renderable"])
        self.assertEqual(session["cues"][0]["text"],"Our red shirts")
        request=out["request"]
        self.assertEqual(request["corrections"][0]["corrected_text"],"Our blue shirts")
        self.assertEqual(request["corrections"][0]["start_ms"],550)
        self.assertEqual(request["corrections"][0]["end_ms"],1600)
        self.assertEqual(request["expected_revision"],3)
        self.assertTrue(request["source_word_times_preserved"])
        self.assertTrue(request["unmodified_original_audio_required"])
        self.assertFalse(request["approved"])
        self.assertFalse(request["renderable"])
        self.assertFalse(request["customer_publishable"])
        self.assertTrue(request["requires_authoritative_server_transaction"])
        self.assertEqual(len(request["request_sha256_hint"]),64)

    def test_reset_to_source_removes_change_and_blocks_empty_request(self):
        r=self.run_case(operation="pure",reset=True,emit=False)
        self.assertEqual(r.returncode,0,r.stderr)
        self.assertEqual(json.loads(r.stdout)["session"]["corrections"],[])
        r=self.run_case(operation="pure",reset=True)
        self.assertNotEqual(r.returncode,0,r.stdout)

    def test_foreign_scope_unsafe_markup_bidi_and_time_change_denied(self):
        cases=[
          {"bad":"foreign"},{"bad":"unsafecue"},{"bad":"overlap"},
          {"bad":"late"},{"bad":"approved"},{"bad":"samesha"},
          {"bad":"wrong_index"},
          {"edit":"\\N{RIGHT-TO-LEFT OVERRIDE}danger"},
          {"edit":"<img onerror=alert(1)>"},
          {"edit":"New\\nline"},
          {"edit":"Bad {ASS}"}]
        for opts in cases:
            with self.subTest(case=opts):
                r=self.run_case(operation="pure",**opts)
                self.assertNotEqual(r.returncode,0,r.stdout)

    def test_viewer_and_unconfirmed_reviewer_cannot_submit(self):
        for opts in [
          {"operation":"pure","role":"VIEWER"},
          {"operation":"pure","bad":"unconfirmed"}
        ]:
            r=self.run_case(**opts)
            self.assertNotEqual(r.returncode,0,r.stdout)

    def test_existing_reviewer_panel_submits_correction_without_scene_approval(self):
        r=self.run_case(operation="ui_confirmed")
        self.assertEqual(r.returncode,0,r.stderr)
        out=json.loads(r.stdout)
        self.assertFalse(out["editor_disabled"])
        self.assertFalse(out["submit_disabled"])
        self.assertEqual(out["caption_review_count"],1)
        self.assertEqual(len(out["events"]),1)
        self.assertEqual(out["events"][0]["corrections"][0]["corrected_text"],
                         "Our blue shirts")
        self.assertFalse(out["events"][0]["approved"])
        self.assertIn("not confirmed",out["feedback"])

    def test_ui_without_separate_confirmation_cannot_submit(self):
        r=self.run_case(operation="ui_unconfirmed")
        self.assertEqual(r.returncode,0,r.stderr)
        out=json.loads(r.stdout)
        self.assertEqual(out["events"],[])
        self.assertIn("denied",out["feedback"])

    def test_panel_viewer_read_only_and_callback_mandatory(self):
        r=self.run_case(operation="ui_confirmed",role="VIEWER")
        self.assertEqual(r.returncode,0,r.stderr)
        out=json.loads(r.stdout)
        self.assertTrue(out["editor_disabled"])
        self.assertTrue(out["submit_disabled"])
        self.assertEqual(out["events"],[])
        r=self.run_case(operation="ui_confirmed",bad="no_callback")
        self.assertNotEqual(r.returncode,0,r.stdout)

if __name__=="__main__":unittest.main()
