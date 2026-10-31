"""Feature7->Feature4 bounded review packet, not an executable render approval."""
import json
from pathlib import Path
import shutil
import subprocess
import unittest
ROOT=Path(__file__).resolve().parents[2]
CODE=r"""
import fs from 'node:fs';
import {createFeature4SpeechReviewHandoff}
  from './video-engine/feature7/feature4_speech_review_handoff.mjs';
const p=JSON.parse(fs.readFileSync(0,'utf8'));
process.stdout.write(JSON.stringify(createFeature4SpeechReviewHandoff(p)));
"""
IMMUTABLE_JS=r"""
import fs from 'node:fs';
import {createFeature4SpeechReviewHandoff} from './video-engine/feature7/feature4_speech_review_handoff.mjs';
const p=JSON.parse(fs.readFileSync(0,'utf8'));
const out=createFeature4SpeechReviewHandoff(p),initial=JSON.stringify(out);
const keys=['source_keep_segments','caption_projection','caption_track','music_duck_intervals'];
const frozen=Object.isFrozen(out)&&keys.every(k=>Object.isFrozen(out[k])&&out[k].every(Object.isFrozen))&&Object.isFrozen(out.objective_qa_faults);
let denied=0;
for(const change of [
 ()=>out.source_keep_segments[0].start=20,
 ()=>out.caption_projection[0].timeline_start_ms=9000,
 ()=>out.caption_track[0].text='FORGED',
 ()=>out.music_duck_intervals[0].start_ms=99,
 ()=>out.objective_qa_faults.push('FORGED'),
 ()=>out.review_payload_sha256='0'.repeat(64)]){
 try{change()}catch(e){if(e instanceof TypeError)denied++;}
}
process.stdout.write(JSON.stringify({frozen,denied,unchanged:JSON.stringify(out)===initial,
 inputMutable:!Object.isFrozen(p.autoclip_plan.keep_segments[0]),approved:out.approved}));
"""
SHA1="a"*64
SHA2="b"*64
def fixture():
    spans=[{"start":0,"end":3},{"start":5,"end":12},{"start":13,"end":18}]
    projection=[
      {"source_start_ms":0,"source_end_ms":3000,
       "visible_source_start_ms":0,"visible_source_end_ms":2985,
       "timeline_start_ms":0,"timeline_end_ms":2985},
      {"source_start_ms":5000,"source_end_ms":12000,
       "visible_source_start_ms":5015,"visible_source_end_ms":11985,
       "timeline_start_ms":2985,"timeline_end_ms":9955},
      {"source_start_ms":13000,"source_end_ms":18000,
       "visible_source_start_ms":13015,"visible_source_end_ms":18000,
       "timeline_start_ms":9955,"timeline_end_ms":14940}
    ]
    return {
      "shop_id":"test-shop","asset_id":"spoken-clip",
      "original_source_sha256":SHA1,"preview_sha256":SHA2,
      "autoclip_plan":{"engine":"branmendo/autoclip-core",
        "engine_license":"MIT","source_sha256":SHA1,
        "human_review_required":True,"approved":False,"renderable":False,
        "source_duration_seconds":18,"keep_segments":spans},
      "caption_projection":{
        "version":"feature7_autoclip_autobroll_caption_projection_v1",
        "shop_id":"test-shop","asset_id":"spoken-clip",
        "approved":False,"renderable":False,"human_review_required":True,
        "requires_rendered_av_acceptance":True,
        "requested_reel_seconds":15,
        "actual_timeline_duration_ms":14940,
        "keep_projection":projection,
        "feature4_caption_track":[
            {"start":.5,"duration":.6,"text":"Our shirts"},
            {"start":3.1,"duration":1.2,"text":"Shop now"},
            {"start":10.0,"duration":1.0,"text":"Visit today"}]},
      "music_handoff":{"version":"feature7_music_ducking_handoff_v1",
        "shop_id":"test-shop","asset_id":"spoken-clip",
        "source_sha256":SHA1,"timeline_duration_ms":14940,
        "original_dialogue_gain_db":0,"voice_preservation_required":True,
        "feature4_mixer_execution_required":True,
        "music_duck_intervals":[{"start_ms":400,"end_ms":1500}],
        "recommended_music_gain_db":-16,
        "approved":False,"renderable":False},
      "decoded_quality":{"version":"feature7_decoded_quality_v1",
        "source_sha256":SHA2,"real_decoding_performed":True,
        "source_bytes_unchanged":True,"duration_seconds":14.94,
        "objective_checks_passed":True,"faults":[],
        "commercial_quality_accepted":False,"approved":False,
        "customer_publishable":False}
    }

@unittest.skipUnless(shutil.which("node"),"Node JS required")
class Feature7F4ReviewBundleTests(unittest.TestCase):
    def call(self,p):
        return subprocess.run(["node","--input-type=module","-e",CODE],
          input=json.dumps(p),cwd=ROOT,capture_output=True,text=True,timeout=15)
    def test_complete_review_only_bundle_preserves_verified_timing_and_voice(self):
        p=fixture()
        r=self.call(p)
        self.assertEqual(r.returncode,0,r.stderr)
        o=json.loads(r.stdout)
        self.assertEqual(o["version"],"feature7_feature4_speech_review_bundle_v1")
        self.assertEqual(o["rendered_preview_duration_ms"],14940)
        self.assertEqual(o["source_keep_segments"][1]["start"],5)
        self.assertEqual(o["caption_projection"][1]["timeline_start_ms"],2985)
        self.assertEqual(o["original_dialogue_gain_db"],0)
        self.assertTrue(o["objective_qa_passed"])
        self.assertFalse(o["approved"])
        self.assertFalse(o["renderable"])
        self.assertFalse(o["customer_publishable"])
        self.assertFalse(o["full_feature4_multi_cut_contract_implemented"])
        self.assertEqual(len(o["review_payload_sha256"]),64)
        self.assertEqual(p["autoclip_plan"]["keep_segments"][0]["start"],0)
    def test_real_qa_warning_is_preserved_not_silently_overridden(self):
        p=fixture();p["decoded_quality"]["faults"]=["POSSIBLE_CLIPPING_OR_EXCESSIVE_PEAK"]
        p["decoded_quality"]["objective_checks_passed"]=False
        r=self.call(p);self.assertEqual(r.returncode,0,r.stderr)
        x=json.loads(r.stdout)
        self.assertFalse(x["objective_qa_passed"])
        self.assertEqual(x["objective_qa_faults"],["POSSIBLE_CLIPPING_OR_EXCESSIVE_PEAK"])
        self.assertFalse(x["approved"])
    def test_nested_review_evidence_is_immutable_after_digest(self):
        r=subprocess.run(["node","--input-type=module","-e",IMMUTABLE_JS],
          input=json.dumps(fixture()),cwd=ROOT,text=True,
          capture_output=True,timeout=15)
        self.assertEqual(r.returncode,0,r.stderr)
        value=json.loads(r.stdout)
        self.assertTrue(value["frozen"])
        self.assertEqual(value["denied"],6)
        self.assertTrue(value["unchanged"])
        self.assertTrue(value["inputMutable"])
        self.assertFalse(value["approved"])

    def test_empty_or_reversed_visible_cut_denied(self):
        for case in ("empty","reversed"):
            p=fixture()
            cut=p["caption_projection"]["keep_projection"][1]
            cut["visible_source_end_ms"]=cut["visible_source_start_ms"]-(case=="reversed")
            with self.subTest(case=case):
                result=self.call(p)
                self.assertNotEqual(result.returncode,0,result.stdout)

    def test_cross_shop_stale_hash_fake_approval_and_cut_tampering_denied(self):
        alterations=[
          lambda p:p.update(shop_id="foreign"),
          lambda p:p.update(preview_sha256=SHA1),
          lambda p:p["autoclip_plan"].update(approved=True),
          lambda p:p["caption_projection"].update(renderable=True),
          lambda p:p["caption_projection"]["keep_projection"][1].update(timeline_start_ms=3000),
          lambda p:p["caption_projection"]["keep_projection"][2].update(source_start_ms=12000),
          lambda p:p["caption_projection"]["feature4_caption_track"][1].update(start=.6),
          lambda p:p["music_handoff"].update(original_dialogue_gain_db=-16),
          lambda p:p["music_handoff"].update(timeline_duration_ms=15000),
          lambda p:p["music_handoff"].update(recommended_music_gain_db=0),
          lambda p:p["music_handoff"]["music_duck_intervals"][0].update(end_ms=15000),
          lambda p:p["caption_projection"].update(requested_reel_seconds=14),
          lambda p:p["caption_projection"]["feature4_caption_track"][0].update(text="<img>"),
          lambda p:p["decoded_quality"].update(faults=["<script>"]),
          lambda p:p["decoded_quality"].update(source_sha256="c"*64),
          lambda p:p["decoded_quality"].update(commercial_quality_accepted=True),
          lambda p:p["decoded_quality"].update(duration_seconds=18),
        ]
        for op in alterations:
            p=fixture();op(p)
            with self.subTest(p=p):
                r=self.call(p)
                self.assertNotEqual(r.returncode,0,r.stdout)
if __name__=="__main__":unittest.main()
