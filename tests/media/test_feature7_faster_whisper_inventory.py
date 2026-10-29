"""Model-inventory negative tests use fake bytes, never real model weights."""
import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/"video-engine"/"feature7"))
from faster_whisper_inventory import draft_actual_model_inventory
from faster_whisper_cpu import validate_local_model,LocalFasterWhisperError

class Feature7InventoryTests(unittest.TestCase):
    def setUp(self):
        self.working=tempfile.TemporaryDirectory(prefix="f7-model-inventory-")
        self.addCleanup(self.working.cleanup)
        self.folder=Path(self.working.name)
        self.model=self.folder/"model"
        self.model.mkdir()
        for name,raw in (("config.json",b"{}"),
                         ("model.bin",b"FAKE--NO_AI_WEIGHTS"),
                         ("tokenizer.json",b"{}")):
            (self.model/name).write_bytes(raw)

    def test_manifest_has_real_file_hashes_but_does_not_claim_legal_review(self):
        manifest=draft_actual_model_inventory(str(self.model))
        self.assertFalse(manifest["commercial_rights_reviewed"])
        self.assertEqual(manifest["files"]["model.bin"],
          hashlib.sha256(b"FAKE--NO_AI_WEIGHTS").hexdigest())
        path=self.folder/"candidate-manifest.json"
        path.write_text(json.dumps(manifest))
        # A draft manifest cannot be used to run a single commercial job.
        with self.assertRaises(LocalFasterWhisperError):
            validate_local_model(str(self.model),str(path))

    def test_unknown_extra_symlink_empty_or_missing_weight_denied(self):
        p=self.model/"model.bin"
        p.unlink()
        with self.assertRaises(LocalFasterWhisperError):
            draft_actual_model_inventory(str(self.model))
        p.write_bytes(b"FAKE")
        extra=self.model/"something-unknown.exe"
        extra.write_bytes(b"danger")
        with self.assertRaises(LocalFasterWhisperError):
            draft_actual_model_inventory(str(self.model))
        extra.unlink()
        p.unlink()
        p.symlink_to(self.model/"config.json")
        with self.assertRaises(LocalFasterWhisperError):
            draft_actual_model_inventory(str(self.model))
        p.unlink()
        p.write_bytes(b"")
        with self.assertRaises(LocalFasterWhisperError):
            draft_actual_model_inventory(str(self.model))

if __name__=="__main__":
    unittest.main()
