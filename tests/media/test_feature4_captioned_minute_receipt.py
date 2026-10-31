"""Fail-closed SHA-linked 60s editorial caption handoff (no auth/publishing claims)."""
import hashlib
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/"video-engine"))
from feature4_minute_quality_receipt import (
    MinuteProofError, validate_captioned_review, validate_minute_evidence
)
from feature4_subtitles import compose_approved_subtitles


def sha(contents):
    return hashlib.sha256(contents).hexdigest()


class CaptionedMinuteReceiptTests(unittest.TestCase):
    def setUp(self):
        ctx=tempfile.TemporaryDirectory()
        self.addCleanup(ctx.cleanup)
        self.root=Path(ctx.name)
        self.preview=self.root/"approved-preview.mp4"
        self.captioned=self.root/"captioned.mp4"
        self.caption_srt=self.root/"titles.srt"
        self.caption_vtt=self.root/"titles.vtt"
        self.provenance=self.root/"provenance.json"
        self.caption_proof=self.root/"proof.json"
        self.preview.write_bytes(b"original-private-reviewed-video"*100)
        self.captioned.write_bytes(b"distinct-captioned-review-mp4"*100)
        self.cues=[{"start":float(i*5),"duration":3.0,
                    "text":f"Original editorial scene {i+1}"}
                   for i in range(12)]
        srt,vtt=compose_approved_subtitles(self.cues,duration_seconds=60)
        self.caption_srt.write_text(srt,encoding="utf-8")
        self.caption_vtt.write_text(vtt,encoding="utf-8")
        self.prov={
            "editorial_subtitle_kind":"EDITORIAL_TEST_TITLES_NOT_SPOKEN_AUDIO",
            "actual_spoken_voiceover":False,
            "editorial_subtitle_cues":self.cues,
            "synced_scene_starts":[c["start"] for c in self.cues],
        }
        self.proof={
            "status":"PRIVATE_ENCODED_SUBTITLES_NOT_PUBLISHED",
            "source_sha256":sha(self.preview.read_bytes()),
            "reviewed_srt_sha256":sha(self.caption_srt.read_bytes()),
            "captioned_mp4_sha256":sha(self.captioned.read_bytes()),
            "cue_count":12,"duration_seconds":60,
            "width":540,"height":960,
            "video_codec":"h264","audio_codec":"aac",
            "actual_encoded_subtitle_filter_executed":True,
            "spoken_word_alignment_verified":False,
            "human_visual_approval":False,
            "commercial_release_eligible":False,
            "signed_download_ready":False,
            "tenant_rights_checked_here":False,
        }
        self.persist()

    def persist(self):
        self.provenance.write_text(json.dumps(self.prov),encoding="utf-8")
        self.caption_proof.write_text(json.dumps(self.proof),encoding="utf-8")

    def validate(self):
        with patch("feature4_minute_quality_receipt.inspect_mp4",return_value={
            "seconds":60.025,"width":540,"height":960,
            "bytes":len(self.captioned.read_bytes())}):
            return validate_captioned_review(
                preview=self.preview,provenance=self.provenance,
                captioned=self.captioned,caption_srt=self.caption_srt,
                caption_vtt=self.caption_vtt,caption_proof=self.caption_proof)

    def test_sha_linked_captioned_derivative_and_zero_approval(self):
        result=self.validate()
        self.assertEqual(result["status"],"CAPTIONED_60S_TECHNICAL_PROOF_ONLY")
        self.assertEqual(result["cue_count"],12)
        self.assertEqual(result["editorial_srt_sha256"],sha(self.caption_srt.read_bytes()))
        self.assertFalse(result["commercial_release_eligible"])
        self.assertFalse(result["tenant_rights_checked_here"])

    def test_altered_srt_vtt_and_stale_render_hash_denied(self):
        for file in (self.caption_srt,self.caption_vtt,self.captioned,self.preview):
            with self.subTest(file=file):
                old=file.read_bytes()
                file.write_bytes(old+b"tampered")
                with self.assertRaises(MinuteProofError):
                    self.validate()
                file.write_bytes(old)

    def test_reordered_cues_spoken_claim_and_false_rights_approval_denied(self):
        self.prov["synced_scene_starts"][1]=8.0
        self.persist()
        with self.assertRaises(MinuteProofError):
            self.validate()
        self.prov["synced_scene_starts"][1]=5.0
        self.prov["actual_spoken_voiceover"]=True
        self.persist()
        with self.assertRaises(MinuteProofError):
            self.validate()
        self.prov["actual_spoken_voiceover"]=False
        for flag in ("signed_download_ready","human_visual_approval",
                     "tenant_rights_checked_here","spoken_word_alignment_verified"):
            self.proof[flag]=True
            self.persist()
            with self.subTest(flag=flag),self.assertRaises(MinuteProofError):
                self.validate()
            self.proof[flag]=False

    def test_missing_and_unreviewed_cues_denied(self):
        self.prov["editorial_subtitle_cues"]=self.cues[:11]
        self.persist()
        with self.assertRaises(MinuteProofError):
            self.validate()
        self.prov["editorial_subtitle_cues"]=self.cues
        self.prov["editorial_subtitle_kind"]="APPROVED_HUMAN_WORDS"
        self.persist()
        with self.assertRaises(MinuteProofError):
            self.validate()

    def test_symlinked_sidecars_denied(self):
        actual=self.root/"real.srt"
        self.caption_srt.rename(actual)
        self.caption_srt.symlink_to(actual)
        with self.assertRaises(MinuteProofError):
            self.validate()

    def test_partial_captioned_chain_never_silently_skipped(self):
        # Invalid main media would fail anyway, but a partial optional receipt
        # must be rejected explicitly, not treated as "no captions" success.
        module=__import__("feature4_minute_quality_receipt")
        with patch.object(module,"_sha",return_value="f"*64),\
             patch.object(module,"_record",return_value={}),\
             patch.object(module,"inspect_mp4",return_value={
                 "seconds":60,"width":1080,"height":1920}):
            with self.assertRaises(MinuteProofError):
                validate_minute_evidence(
                    original=self.preview,master=self.preview,preview=self.preview,
                    provenance=self.provenance,motion=self.caption_proof,
                    master_proof=self.caption_proof,preview_proof=self.caption_proof,
                    contact_image=self.caption_srt,contact_proof=self.caption_proof,
                    captioned=self.captioned)


if __name__=="__main__":
    unittest.main()
