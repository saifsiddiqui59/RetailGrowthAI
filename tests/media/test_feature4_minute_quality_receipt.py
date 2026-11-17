"""Offline fail-closed checks for native minute trace verification."""
import sys
import tempfile
import unittest
from unittest.mock import patch
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/"video-engine"))
from feature4_minute_quality_receipt import (MinuteProofError, validate_minute_evidence,
    _require_distinct_render_stages, _require_changed_render_bytes)

class MinuteEvidenceTests(unittest.TestCase):
    def setUp(self):
        self.t=tempfile.TemporaryDirectory()
        self.addCleanup(self.t.cleanup)
        self.root=Path(self.t.name)
        self.paths={name:self.root/(name+('.mp4' if name in ('original','master','preview') else '.json'))
              for name in ('original','master','preview','provenance','motion','master_proof','preview_proof','contact_image','contact_proof')}
        self.paths['contact_image']=self.root/'review.jpg'
        self.paths.update({
            "captioned":self.root/"captioned.mp4",
            "caption_srt":self.root/"review.srt",
            "caption_vtt":self.root/"review.vtt",
            "caption_proof":self.root/"caption-proof.json",
            "visibility_proof":self.root/"visibility-proof.json",
            "endcard_proof":self.root/"endcard-proof.json",
        })
    def fill_test_records(self):
        # Ensure malformed media/symlinks are reached AFTER the mandatory
        # evidence-present gate, instead of testing only missing arguments.
        for key in ("provenance","motion","master_proof",
                    "preview_proof","contact_proof"):
            self.paths[key].write_text('{"probe": true}\n',encoding="utf-8")
    def validate(self):
        return validate_minute_evidence(**self.paths)
    def test_every_caption_and_visibility_receipt_is_required(self):
        full={**self.paths, "captioned":self.root/"captioned.mp4",
              "caption_srt":self.root/"review.srt",
              "caption_vtt":self.root/"review.vtt",
              "caption_proof":self.root/"caption-proof.json",
              "visibility_proof":self.root/"visibility-proof.json",
              "endcard_proof":self.root/"endcard-proof.json"}
        # No media inspection is allowed before the complete acceptance
        # evidence is present; a false NOT_RUN success must be impossible.
        for missing in ("captioned","caption_srt","caption_vtt",
                        "caption_proof","visibility_proof","endcard_proof"):
            with self.subTest(missing=missing):
                kw={**full,missing:None}
                with patch("feature4_minute_quality_receipt.inspect_mp4",
                           side_effect=AssertionError("inspected incomplete source")):
                    with self.assertRaisesRegex(MinuteProofError,
                                                "Missing mandatory 60s"):
                        validate_minute_evidence(**kw)

    def test_same_path_cannot_be_source_and_master(self):
        self.paths["original"].write_bytes(b"fake mp4 bytes"*8)
        self.paths["master"]=self.paths["original"]
        with patch("feature4_minute_quality_receipt.inspect_mp4",
                   side_effect=AssertionError("alias must fail before media probe")):
            with self.assertRaisesRegex(MinuteProofError,"distinct files"):
                self.validate()

    def test_hardlink_cannot_masquerade_as_new_master(self):
        self.paths["original"].write_bytes(b"fake mp4 bytes"*8)
        self.paths["master"].hardlink_to(self.paths["original"])
        with patch("feature4_minute_quality_receipt.inspect_mp4",
                   side_effect=AssertionError("hardlink must fail before media probe")):
            with self.assertRaisesRegex(MinuteProofError,"distinct files"):
                self.validate()

    def test_all_four_stages_require_distinct_paths(self):
        files=[self.root/name for name in ("source.mp4","master.mp4","preview.mp4")]
        with self.assertRaisesRegex(MinuteProofError,"distinct files"):
            _require_distinct_render_stages(*files,files[2])

    def test_copy_without_mastering_or_reencode_is_not_evidence(self):
        a,b,c=("a"*64,"b"*64,"c"*64)
        _require_changed_render_bytes(a,b,c)
        for stages in ((a,a,c),(a,b,b),(a,b,a)):
            with self.subTest(stages=stages):
                with self.assertRaisesRegex(MinuteProofError,"distinct encoded bytes"):
                    _require_changed_render_bytes(*stages)

    def test_garbage_or_unproven_mp4_rejected(self):
        self.fill_test_records()
        for k in ('original','master','preview'):
            self.paths[k].write_bytes(b"not media"*100)
        with self.assertRaisesRegex(MinuteProofError,"media/codec preflight"):
            self.validate()
    def test_symlinked_evidence_rejected(self):
        self.fill_test_records()
        for k in ("original","master","preview"):
            self.paths[k].write_bytes(b"not media"*100)
        backing=self.root/'evidence.json'
        backing.write_text('{"valid": false}')
        self.paths['provenance'].unlink()
        self.paths['provenance'].symlink_to(backing)
        with self.assertRaisesRegex(MinuteProofError,"Unsafe"):
            self.validate()
    def test_oversize_source_fails_without_loading_into_memory(self):
        source=self.paths['original']
        with source.open('wb') as handle:
            handle.truncate(80_000_002)
        with self.assertRaisesRegex(MinuteProofError,"Unsafe"):
            self.validate()
