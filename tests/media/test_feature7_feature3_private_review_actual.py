"""Exact Feature3 original technical MP4 through the actual Feature7 review pipeline.

OPT-IN: Requires the real sha-pinned GitHub artifact #12879355229, staged from
an authorized test download. It is a SYNTHETIC technical geometry fixture with
silent AAC, NO recognized human speech, NO generated VTON and NO publication
rights. To satisfy Feature4's 15s storyboard, two separately identified
7.5s trims reference *identical* immutable original bytes. The mock grant
exists ONLY inside this isolated offline contract test, never in RLS/cloud.
"""
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest
from zipfile import ZipFile

ROOT=Path(__file__).resolve().parents[2]
PIN="16ceaa91a5dad57de023f45b21eee45772f361a18299801e9e27b6ae49ce9f22"
ARCHIVE=os.getenv("FEATURE7_F3_ORIGINAL_ARTIFACT_ZIP")
SCRIPT=r"""
import fs from 'node:fs';
import {preparePrivateReview} from './video-engine/feature7/private_review_pipeline.mjs';
const p=JSON.parse(fs.readFileSync(0,'utf8'));
const out=preparePrivateReview(p);
process.stdout.write(JSON.stringify({
  version:out.version,review_status:out.review_status,
  approved:out.approved,renderable:out.renderable,
  media_evidence:out.media_evidence,
  scenes:out.scenes,
  captions_advisory:out.captions_advisory,
  broll_advisory:out.broll_advisory,
  silence_jump_cut_advisory:out.silence_jump_cut_advisory,
  audio_policy:out.audio_policy,network_calls:out.network_calls,
  model_calls:out.model_calls
}));
"""
@unittest.skipUnless(ARCHIVE and all(shutil.which(x) for x in
    ("node","ffmpeg","ffprobe")), "Actual GitHub F3 ZIP not staged; no fixture substitution")
class Feature7RealF3TechnicalReviewPipeline(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory(prefix="f7-f3-actual-review-")
        self.addCleanup(self.tmp.cleanup)
        self.root=Path(self.tmp.name)
        self.files=[]
        from sys import path as module_path
        module_path.insert(0,str(ROOT/"video-engine"/"feature7"))
        from feature3_artifact_preflight import check_feature3_actual_artifact
        report=check_feature3_actual_artifact(str(Path(ARCHIVE).resolve()))
        self.assertTrue(report["feature3_original_file_integrity_verified"])
        self.assertFalse(report["retailer_rights_verified"])
        self.assertFalse(report["human_speech_transcribed"])
        with ZipFile(ARCHIVE) as z:
            raw=z.read("feature4-editor-input.mp4")
        self.assertEqual(hashlib.sha256(raw).hexdigest(),PIN)
        for n in range(2):
            file=self.root/f"f3_technical_{n}.mp4"
            file.write_bytes(raw)
            self.files.append(file)

    def payload(self):
        shop,campaign="f7-technical-test-only","f7-draft-technical-test"
        scenes=[];media=[]
        for i,file in enumerate(self.files):
            asset=f"synthetic_f3_{i}"
            scenes.append({"asset_id":asset,"asset_type":"video",
              "source_feature":"retailer","duration":7.5,"start":7.5*i})
            grant={"shop_id":shop,"asset_id":asset,
                "issued_by":"trusted_server","source":"retailer_upload",
                "active":True,"rights_status":"APPROVED","media_type":"video",
                "mime_type":"video/mp4","has_audio":True,
                "relative_path":file.name,"sha256":PIN}
            media.append({"scene_index":i,"asset_id":asset,
                "relative_path":file.name,"expected_sha256":PIN,
                "grant":grant,
                # Empty supplied transcript: this file does NOT contain
                # human speech; never invent ASR words or an inference run.
                "whisperx_json":{"segments":[{"words":[]}]}})
        return {"shop_id":shop,"campaign_id":campaign,"root":str(self.root),
                "draft":{"shop_id":shop,"campaign_id":campaign,
                  "duration_seconds":15,"scenes":scenes},
                "media":media,"broll_grants":[],"include_visual_qa":True}

    def invoke(self,p):
        return subprocess.run(["node","--input-type=module","-e",SCRIPT],
           cwd=ROOT,input=json.dumps(p),text=True,capture_output=True,timeout=110)

    def test_real_original_bytes_enter_f7_review_only_without_fake_asr(self):
        before=[hashlib.sha256(p.read_bytes()).hexdigest() for p in self.files]
        result=self.invoke(self.payload())
        self.assertEqual(result.returncode,0,result.stderr)
        parsed=json.loads(result.stdout)
        self.assertEqual(parsed["review_status"],"NEEDS_REVIEW")
        self.assertFalse(parsed["approved"])
        self.assertFalse(parsed["renderable"])
        self.assertEqual(parsed["audio_policy"],"PRESERVE_SOURCE")
        self.assertEqual(parsed["model_calls"],0)
        self.assertEqual(parsed["network_calls"],0)
        self.assertEqual(parsed["captions_advisory"],[])
        self.assertEqual(parsed["broll_advisory"],[])
        self.assertEqual(len(parsed["media_evidence"]),2)
        self.assertEqual([e["source_sha256"] for e in parsed["media_evidence"]],[PIN,PIN])
        self.assertTrue(all(e["audio_activity"]["original_audio_preserved"]
                            for e in parsed["media_evidence"]))
        self.assertTrue(all(not a["detected_speech_ranges"]
             for a in parsed["silence_jump_cut_advisory"]))
        self.assertEqual([hashlib.sha256(p.read_bytes()).hexdigest()
                          for p in self.files],before)

    def test_asset_tamper_foreign_shop_and_forged_source_denied(self):
        for case in ("foreign_shop","invalid_rights","bad_sha","fake_speech"):
            p=self.payload()
            if case=="foreign_shop":
                p["media"][0]["grant"]["shop_id"]="another-tenant"
            elif case=="invalid_rights":
                p["media"][1]["grant"]["rights_status"]="REVOKED"
            elif case=="bad_sha":
                p["media"][0]["expected_sha256"]="0"*64
            else:
                # Real downloaded F3 source is entirely silent. A supplied
                # invented ASR token must fail before captions/review output.
                p["media"][0]["whisperx_json"]["segments"][0]["words"]=[
                    {"word":"fabricated","start":1.0,"end":1.5}]
            out=self.invoke(p)
            self.assertNotEqual(out.returncode,0,out.stdout)
            self.assertEqual(out.stdout,"")

if __name__=="__main__":
    unittest.main()
