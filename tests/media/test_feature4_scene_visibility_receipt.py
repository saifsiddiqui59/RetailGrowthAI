"""Strict evidence validation for 12 encoded stock Reel scene samples."""
import hashlib
import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/"video-engine"))
from feature4_minute_quality_receipt import (
    MinuteProofError, validate_visibility_evidence
)


class VisibilityReceiptTests(unittest.TestCase):
    def setUp(self):
        ctx=tempfile.TemporaryDirectory()
        self.addCleanup(ctx.cleanup)
        self.root=Path(ctx.name)
        self.original=self.root/"real-encoded.mp4"
        self.provenance=self.root/"source.json"
        self.visibility_proof=self.root/"scene-visibility.json"
        self.original.write_bytes(b"private-original-encoded-media"*100)
        self.windows=[{"start":i*5.0,"duration":5.0} for i in range(12)]
        self.prov={"scene_windows":self.windows}
        self.report={
            "schema":"feature4_scene_visibility_v1",
            "status":"SAMPLED_SCENES_NOT_BLANK_NOT_CONTENT_APPROVAL",
            "source_sha256":hashlib.sha256(self.original.read_bytes()).hexdigest(),
            "seconds":60,"checked_scene_count":12,
            "sustained_near_black_count":0,
            "commercial_release_eligible":False,
            "garment_identity_verified":False,
            "unexpected_overlay_absence_verified":False,
            "checked_scenes":[{
                "scene_start":i*5.0,"duration":5.0,
                "sustained_near_black":False,
                "samples":[{"time_seconds":i*5.0+1.5,"mean_luma":87,
                            "near_black_fraction":0.03},
                           {"time_seconds":i*5.0+3.5,"mean_luma":80,
                            "near_black_fraction":0.05}]
            } for i in range(12)],
        }
        self.persist()
    def persist(self):
        self.provenance.write_text(json.dumps(self.prov))
        self.visibility_proof.write_text(json.dumps(self.report))
    def verify(self):
        return validate_visibility_evidence(
            original=self.original,provenance=self.provenance,
            visibility_proof=self.visibility_proof)
    def test_sha_linked_sampled_scans_are_not_artistic_approval(self):
        result=self.verify()
        self.assertEqual(result["checked_scene_count"],12)
        self.assertFalse(result["commercial_release_eligible"])
        self.assertFalse(result["unexpected_overlay_absence_verified"])
    def test_suspicious_black_sample_or_forged_human_approval_rejected(self):
        self.report["checked_scenes"][3]["sustained_near_black"]=True
        self.persist()
        with self.assertRaises(MinuteProofError):
            self.verify()
        self.report["checked_scenes"][3]["sustained_near_black"]=False
        for key in ("commercial_release_eligible","garment_identity_verified",
                    "unexpected_overlay_absence_verified"):
            self.report[key]=True
            self.persist()
            with self.subTest(key=key),self.assertRaises(MinuteProofError):
                self.verify()
            self.report[key]=False
    def test_altered_video_bytes_or_out_of_scene_sample_rejected(self):
        self.original.write_bytes(self.original.read_bytes()+b"changed")
        with self.assertRaises(MinuteProofError):
            self.verify()
        self.report["source_sha256"]=hashlib.sha256(self.original.read_bytes()).hexdigest()
        self.report["checked_scenes"][0]["samples"][0]["time_seconds"]=20
        self.persist()
        with self.assertRaises(MinuteProofError):
            self.verify()
    def test_mismatched_scene_claim_and_symlinked_receipt_rejected(self):
        self.report["checked_scenes"][7]["scene_start"]=1
        self.persist()
        with self.assertRaises(MinuteProofError):
            self.verify()
        self.report["checked_scenes"][7]["scene_start"]=35
        self.persist()
        actual=self.root/"real-report.json"
        self.visibility_proof.rename(actual)
        self.visibility_proof.symlink_to(actual)
        with self.assertRaises(MinuteProofError):
            self.verify()


if __name__=="__main__":
    unittest.main()
