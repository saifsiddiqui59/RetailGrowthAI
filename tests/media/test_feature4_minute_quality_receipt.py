"""Offline fail-closed checks for native minute trace verification."""
import sys
import tempfile
import unittest
from unittest.mock import patch
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/"video-engine"))
from feature4_minute_quality_receipt import MinuteProofError,validate_minute_evidence

class MinuteEvidenceTests(unittest.TestCase):
    def setUp(self):
        self.t=tempfile.TemporaryDirectory()
        self.addCleanup(self.t.cleanup)
        self.root=Path(self.t.name)
        self.paths={name:self.root/(name+('.mp4' if name in ('original','master','preview') else '.json'))
              for name in ('original','master','preview','provenance','motion','master_proof','preview_proof','contact_image','contact_proof')}
        self.paths['contact_image']=self.root/'review.jpg'
    def validate(self):
        return validate_minute_evidence(**self.paths)
    def test_every_caption_and_visibility_receipt_is_required(self):
        full={**self.paths, "captioned":self.root/"captioned.mp4",
              "caption_srt":self.root/"review.srt",
              "caption_vtt":self.root/"review.vtt",
              "caption_proof":self.root/"caption-proof.json",
              "visibility_proof":self.root/"visibility-proof.json"}
        # No media inspection is allowed before the complete acceptance
        # evidence is present; a false NOT_RUN success must be impossible.
        for missing in ("captioned","caption_srt","caption_vtt",
                        "caption_proof","visibility_proof"):
            with self.subTest(missing=missing):
                kw={**full,missing:None}
                with patch("feature4_minute_quality_receipt.inspect_mp4",
                           side_effect=AssertionError("inspected incomplete source")):
                    with self.assertRaisesRegex(MinuteProofError,
                                                "Missing mandatory 60s"):
                        validate_minute_evidence(**kw)

    def test_garbage_or_unproven_mp4_rejected(self):
        for k in ('original','master','preview'):
            self.paths[k].write_bytes(b"not media"*100)
        with self.assertRaises(MinuteProofError):
            self.validate()
    def test_symlinked_evidence_rejected(self):
        backing=self.root/'evidence.json'
        backing.write_text('{"valid": false}')
        self.paths['provenance'].symlink_to(backing)
        with self.assertRaises(MinuteProofError):
            self.validate()
    def test_oversize_source_fails_without_loading_into_memory(self):
        source=self.paths['original']
        with source.open('wb') as handle:
            handle.truncate(80_000_002)
        with self.assertRaises(MinuteProofError):
            self.validate()
