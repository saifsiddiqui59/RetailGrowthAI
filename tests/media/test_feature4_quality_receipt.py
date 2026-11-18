"""Cross-feature QA receipt is transparent and enforces source-to-export linkage."""
import hashlib
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/"video-engine"))
from feature4_quality_receipt import QualityReceiptError, validate_stock_receipt

class ReceiptTests(unittest.TestCase):
    def setUp(self):
        ctx=tempfile.TemporaryDirectory()
        self.addCleanup(ctx.cleanup)
        self.root=Path(ctx.name)
        self.files=[self.root/f"{i}.mp4" for i in range(3)]
        for i,x in enumerate(self.files):
            x.write_bytes(bytes([i+1])*20000)
        self.hashes=[hashlib.sha256(x.read_bytes()).hexdigest() for x in self.files]
        self.provenance={"duration_seconds":30,"scene_count":7,
            "status":"OFFLINE_CROSS_FEATURE_STOCK_TEST_ONLY",
            "commercial_release_eligible":False,
            "model_garment_match_verified":False,"actual_spoken_voiceover":False,
            "showcase_eligible":False,
            "source_media":[{"source_feature":("feature3_garment_proxy" if i<2 else "feature5_stock_proxy"),
               "source_id":str(i),"page":"https://www.pexels.com/video/example"} for i in range(5)]}
        self.motion={"status":"MOVING_PIXELS_VERIFIED_NOT_CONTENT_APPROVAL",
            "source_sha256":self.hashes[0],"commercial_release_eligible":False,
            "threshold_luma_difference":5,
            "checked_moving_scenes":[{"luma_difference":6.1}]*3}
        self.master={"status":"PRIVATE_AUDIO_MASTERED_NOT_PUBLISHED",
            "source_sha256":self.hashes[0],"master_sha256":self.hashes[1],
            "signed_download_ready":False,"commercial_release_eligible":False,
            "source_audio_mean_db":-28,"mastered_audio_mean_db":-18}
        self.preview={"status":"PRIVATE_PREVIEW_ENCODED_NOT_PUBLISHED",
            "source_sha256":self.hashes[1],"preview_sha256":self.hashes[2],
            "signed_download_ready":False,"commercial_release_eligible":False}
        self.editorial={"caption_kind":"EDITORIAL_TEST_TITLES_NOT_SPOKEN_AUDIO",
            "speech_text_alignment_verified_here":False,
            "signed_download_ready":False,"cue_count":7}
        self.keys=("provenance","motion_proof","master_proof","preview_proof","editorial_proof")
        self.data=[self.provenance,self.motion,self.master,self.preview,self.editorial]
        for key,val in zip(self.keys,self.data):
            (self.root/(key+".json")).write_text(json.dumps(val))
    def validate(self):
        kwargs={"original":self.files[0],"master":self.files[1],"preview":self.files[2]}
        kwargs.update({k:self.root/(k+".json") for k in self.keys})
        return validate_stock_receipt(**kwargs)
    def test_report_lists_every_feature_and_never_grants_release(self):
        with patch("feature4_quality_receipt.inspect_mp4",
                   side_effect=[{"seconds":30,"width":1080,"height":1920},
                                {"seconds":30,"width":1080,"height":1920},
                                {"seconds":30,"width":540,"height":960}]):
            report=self.validate()
        self.assertEqual(set(report["features"]),{"feature2","feature3","feature4","feature5","feature7"})
        self.assertEqual(report["features"]["feature4"]["status"],"OFFLINE_MEDIA_TECHNICAL_PASS")
        self.assertFalse(report["commercial_release_eligible"])
        self.assertFalse(report["signed_download_ready"])
        self.assertEqual(len(report["blockers"]),6)
    def test_fake_motion_or_cross_source_hashes_never_pass(self):
        self.motion["checked_moving_scenes"][0]["luma_difference"]=0
        (self.root/"motion_proof.json").write_text(json.dumps(self.motion))
        with patch("feature4_quality_receipt.inspect_mp4",
                   side_effect=[{"seconds":30,"width":1080,"height":1920}]*2+
                              [{"seconds":30,"width":540,"height":960}]):
            with self.assertRaisesRegex(QualityReceiptError,"moving actor"):
                self.validate()
        self.motion["checked_moving_scenes"][0]["luma_difference"]=6.1
        (self.root/"motion_proof.json").write_text(json.dumps(self.motion))
        self.preview["source_sha256"]="0"*64
        (self.root/"preview_proof.json").write_text(json.dumps(self.preview))
        with patch("feature4_quality_receipt.inspect_mp4",
                   side_effect=[{"seconds":30,"width":1080,"height":1920}]*2+
                              [{"seconds":30,"width":540,"height":960}]):
            with self.assertRaisesRegex(QualityReceiptError,"hashes"):
                self.validate()
    def test_no_spoken_approval_and_media_permissions(self):
        self.editorial["speech_text_alignment_verified_here"]=True
        (self.root/"editorial_proof.json").write_text(json.dumps(self.editorial))
        with patch("feature4_quality_receipt.inspect_mp4",
                   side_effect=[{"seconds":30,"width":1080,"height":1920}]*2+
                              [{"seconds":30,"width":540,"height":960}]):
            with self.assertRaisesRegex(QualityReceiptError,"caption"):
                self.validate()
