"""Offline fail-closed checks for native minute trace verification."""
import sys
import tempfile
import unittest
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
