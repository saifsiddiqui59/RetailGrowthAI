"""Exact Feature7 original-WAV -> Feature2 Python consumer integration gate.

Feature2 is currently unmerged on separate PR #551. This test MUST NOT copy
or invent Feature2's source. It calls the real Feature2 function after the
coordinator integrates both branches. Until then this test is an explicit
skip, not a pass or a substitute local mock consumer.
"""
import json
from pathlib import Path
import sys
import unittest

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/"ai-agents"/"src"))
try:
    from ai_agents.feature2_voice_quality import (
       review_signed_audio_transcript, Feature7AudioEvidenceDenied)
except (ImportError,AttributeError):
    review_signed_audio_transcript=None
    Feature7AudioEvidenceDenied=ValueError

from test_feature7_original_wav_cpu import Feature7OriginalWavCpuTests as F7

@unittest.skipUnless(review_signed_audio_transcript is not None,
     "Feature2 PR #551 signed audio Python consumer not integrated into this branch")
class Feature7Feature2ActualConsumerIntegration(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        F7.setUpClass()

    @classmethod
    def tearDownClass(cls):
        F7.tearDownClass()

    def test_actual_feature2_consumer_accepts_only_rechecked_signed_wav(self):
        worker=F7()
        run=worker.call()
        self.assertEqual(run.returncode,0,run.stderr)
        packet=json.loads(run.stdout)
        receipt=packet["receipt"]
        req=F7.req()
        calls=[]
        def authoritative(*scope):
            calls.append(scope)
            return scope==(req["shop_id"],req["campaign_id"],
              req["asset_id"],req["creative_plan_sha256"],
              req["expected_sha256"],req["job_id"])
        result=review_signed_audio_transcript(
          receipt=receipt,shop_id=req["shop_id"],
          campaign_id=req["campaign_id"],
          audio_asset_id=req["asset_id"],
          creative_plan_sha256=req["creative_plan_sha256"],
          original_audio_sha256=req["expected_sha256"],
          audio_duration_seconds=1.0,
          expected_script="Diwali fashion",
          evidence_key=bytes.fromhex("ab"*32),
          now_ms=req["now_ms"],expected_job_id=req["job_id"],
          assert_current_source=authoritative)
        self.assertEqual(len(calls),2)
        self.assertTrue(result["evidence_mac_verified"])
        self.assertTrue(result["transcript_matches_script"])
        self.assertFalse(result["publish_approved"])
        self.assertTrue(result["human_listen_required"])

    def test_real_feature2_consumer_rejects_changed_job_and_source(self):
        worker=F7()
        run=worker.call()
        self.assertEqual(run.returncode,0,run.stderr)
        receipt=json.loads(run.stdout)["receipt"]
        p=F7.req()
        def check(*_):return True
        common=dict(receipt=receipt,shop_id=p["shop_id"],
           campaign_id=p["campaign_id"],audio_asset_id=p["asset_id"],
           creative_plan_sha256=p["creative_plan_sha256"],
           original_audio_sha256=p["expected_sha256"],
           audio_duration_seconds=1.0,expected_script="Diwali fashion",
           evidence_key=bytes.fromhex("ab"*32),now_ms=p["now_ms"],
           expected_job_id=p["job_id"],assert_current_source=check)
        for alter in ({"expected_job_id":"stale"},
                      {"original_audio_sha256":"e"*64},
                      {"campaign_id":"foreign"}):
            with self.subTest(alter=alter):
                with self.assertRaises(Feature7AudioEvidenceDenied):
                    review_signed_audio_transcript(**(common|alter))

    def test_source_revoked_between_authoritative_checks_denied(self):
        worker=F7()
        run=worker.call()
        self.assertEqual(run.returncode,0,run.stderr)
        receipt=json.loads(run.stdout)["receipt"]
        q=F7.req()
        calls=[]
        def current(*scope):
            calls.append(scope)
            return len(calls)==1
        with self.assertRaises(Feature7AudioEvidenceDenied):
            review_signed_audio_transcript(
              receipt=receipt,shop_id=q["shop_id"],
              campaign_id=q["campaign_id"],audio_asset_id=q["asset_id"],
              creative_plan_sha256=q["creative_plan_sha256"],
              original_audio_sha256=q["expected_sha256"],
              audio_duration_seconds=1.0,expected_script="Diwali fashion",
              evidence_key=bytes.fromhex("ab"*32),now_ms=q["now_ms"],
              expected_job_id=q["job_id"],assert_current_source=current)
        self.assertEqual(len(calls),2)

if __name__=="__main__":
    unittest.main()
