"""SHA-linked source-only encoded endcard receipt; explicitly not commercial QA."""
import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/"video-engine"))
from feature4_minute_quality_receipt import (
    MinuteProofError, validate_endcard_evidence)


class EndcardReceiptTests(unittest.TestCase):
    def setUp(self):
        context=tempfile.TemporaryDirectory(prefix="f4-endcard-receipt-")
        self.addCleanup(context.cleanup)
        self.root=Path(context.name)
        self.original=self.root/"real.mp4"
        self.source=self.root/"provenance.json"
        self.proof=self.root/"endcard-proof.json"
        self.original.write_bytes(b"sha-pinned-real-encoded-test-bytes"*100)
        self.p={"scene_windows":[{"start":i*5.0,"duration":5.0}
                                 for i in range(12)]}
        self.e={
            "schema":"feature4_stock_endcard_pixel_v1",
            "status":"ENCODED_OUTRO_VISUALLY_CHANGED_NOT_TEXT_APPROVAL",
            "source_sha256":hashlib.sha256(self.original.read_bytes()).hexdigest(),
            "duration_seconds":60,"outro_start_seconds":55.0,
            "pre_outro_sample_seconds":53.0,
            "outro_sample_seconds":57.5,"outro_tail_sample_seconds":59.3,
            "scene_delta_mean_luma":60.0,
            "outro_stability_delta_mean_luma":.01,
            "commercial_release_eligible":False,
            "human_visual_approval":False,"retailer_garment_verified":False,
            "text_legibility_verified":False,
            "spoken_caption_sync_verified":False}
        self.persist()

    def persist(self):
        self.source.write_text(json.dumps(self.p))
        self.proof.write_text(json.dumps(self.e))

    def verify(self):
        return validate_endcard_evidence(original=self.original,
                                         provenance=self.source,
                                         endcard_proof=self.proof)

    def test_source_linked_noncommercial_report(self):
        report=self.verify()
        self.assertEqual(report["status"],"ENCODED_STOCK_OUTRO_CHANGED_NOT_AD_APPROVAL")
        self.assertEqual(report["scene_delta_mean_luma"],60.0)
        self.assertFalse(report["commercial_release_eligible"])
        self.assertFalse(report["text_legibility_verified"])

    def test_tampered_encoded_bytes_or_missing_report_rejected(self):
        self.original.write_bytes(self.original.read_bytes()+b"changed")
        with self.assertRaises(MinuteProofError):
            self.verify()
        self.original.write_bytes(b"sha-pinned-real-encoded-test-bytes"*100)
        self.proof.unlink()
        with self.assertRaises(MinuteProofError):
            self.verify()

    def test_forged_old_short_endcard_or_pixel_measures_rejected(self):
        self.p["scene_windows"][-1]["start"]=58.0
        self.persist()
        with self.assertRaises(MinuteProofError):
            self.verify()
        self.p["scene_windows"][-1]["start"]=55.0
        for key,value in (
            ("scene_delta_mean_luma",16.0),
            ("outro_stability_delta_mean_luma",24.0),
            ("scene_delta_mean_luma","large"),
            ("outro_sample_seconds",52.5)):
            original=self.e[key]
            self.e[key]=value
            self.persist()
            with self.subTest(key=key),self.assertRaises(MinuteProofError):
                self.verify()
            self.e[key]=original

    def test_forged_approval_flags_and_symlink_rejected(self):
        for flag in ("commercial_release_eligible","human_visual_approval",
                     "retailer_garment_verified","text_legibility_verified",
                     "spoken_caption_sync_verified"):
            self.e[flag]=True
            self.persist()
            with self.subTest(flag=flag),self.assertRaises(MinuteProofError):
                self.verify()
            self.e[flag]=False
        self.persist()
        real=self.root/"real-proof.json"
        self.proof.rename(real)
        self.proof.symlink_to(real)
        with self.assertRaises(MinuteProofError):
            self.verify()


if __name__=="__main__":
    unittest.main()
