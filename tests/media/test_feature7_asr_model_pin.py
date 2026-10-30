"""Feature7 signed offline ASR evidence can be bound to a trusted model ID.

Synthetic HMAC fixtures only; no real speech model or approved media.
"""
import json
import shutil
import subprocess
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = """
import fs from 'node:fs';
import {sealTranscriptEvidence,verifyTranscriptEvidence} from './video-engine/feature7/transcript_evidence.mjs';
const input=JSON.parse(fs.readFileSync(0,'utf8'));
const key=Buffer.alloc(32,0x42); // isolated deterministic test-only secret
const now_ms=1700000000000;
const evidence=sealTranscriptEvidence({key,now_ms,data:{
  shop_id:'shop7',asset_id:'asset7',job_id:'job7',
  source_sha256:'a'.repeat(64),transcript_sha256:'b'.repeat(64),
  model_id:'approved_cpu_asr_v1',issued_at_ms:now_ms,
  expires_at_ms:now_ms+60000}});
if(input.tamper) evidence.model_id='other_cpu_model';
const expect={shop_id:'shop7',asset_id:'asset7',job_id:'job7',
  source_sha256:'a'.repeat(64),transcript_sha256:'b'.repeat(64)};
if(Object.hasOwn(input,'model_id'))expect.model_id=input.model_id;
const verified=verifyTranscriptEvidence({evidence,key,expect,now_ms});
process.stdout.write(JSON.stringify({verified:verified.verified,model_id:verified.model_id}));
"""


@unittest.skipUnless(shutil.which("node"), "Node runtime required")
class Feature7AsrModelPinTests(unittest.TestCase):
    def invoke(self, payload):
        return subprocess.run(
            ["node", "--input-type=module", "-e", SCRIPT],
            cwd=ROOT, input=json.dumps(payload), text=True,
            capture_output=True, timeout=10,
        )

    def test_expected_approved_cpu_model_passes(self):
        run = self.invoke({"model_id": "approved_cpu_asr_v1"})
        self.assertEqual(run.returncode, 0, run.stderr)
        result = json.loads(run.stdout)
        self.assertTrue(result["verified"])
        self.assertEqual(result["model_id"], "approved_cpu_asr_v1")

    def test_wrong_or_malformed_model_expectation_fails_closed(self):
        for model_id in ("other_cpu_model", "", None, 7):
            with self.subTest(model_id=model_id):
                run = self.invoke({"model_id": model_id})
                self.assertNotEqual(run.returncode, 0, run.stdout)
                self.assertEqual(run.stdout, "")

    def test_signed_model_id_cannot_be_tampered(self):
        run = self.invoke({"model_id": "approved_cpu_asr_v1", "tamper": True})
        self.assertNotEqual(run.returncode, 0, run.stdout)

    def test_legacy_offline_fixture_without_model_expectation_still_valid(self):
        run = self.invoke({})
        self.assertEqual(run.returncode, 0, run.stderr)
        self.assertTrue(json.loads(run.stdout)["verified"])


if __name__ == "__main__":
    unittest.main()
