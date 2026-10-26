"""Feature5 interop tests: no hosted ledger, tenant data, Azure, or GPU."""
import sys
import unittest
from pathlib import Path
from unittest.mock import Mock
from uuid import uuid4

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from feature5_motion.contracts import MotionError
from feature5_motion.interop import (
    ApprovedMotionClip, FEATURE4_VERSION, HUNYUAN_MODEL,
    Part3MotionStoreAdapter, feature4_asset_entry, feature4_scene,
    planned_motion_key, verified_claim_to_motion,
)


def uid():
    return str(uuid4())


class TestPart3Bridge(unittest.TestCase):
    def setUp(self):
        self.shop = uid()
        self.job = uid()
        self.source = uid()
        self.token = uid()
        self.reservation = uid()
        self.row = {
            "id": self.job, "shop_id": self.shop, "attempt_token": self.token,
            "model_id": HUNYUAN_MODEL, "mode": "image",
            "prompt": "Adult model walks through boutique", "source_asset_id": self.source,
            "resolution": "480p", "seconds": 5, "status": "RUNNING",
            "review_status": "APPROVED", "rights_approved": True,
            "user_approved": True, "subscription_active": True,
            "reserved_usd": "0.80", "reservation_id": self.reservation,
            "idempotency_key": "a" * 64, "prompt_version": "feature5-v1",
        }

    def test_existing_ledger_authoritative_claim(self):
        ledger = Mock()
        ledger.claim_authorized_motion.return_value = self.row.copy()
        adapter = Part3MotionStoreAdapter(ledger)
        claim = adapter.claim(self.job)
        self.assertEqual(claim["spec"].mode, "image")
        self.assertEqual(str(claim["reserved_usd"]), "0.80")
        self.assertEqual(claim["reservation_id"], self.reservation)
        ledger.claim_authorized_motion.assert_called_once_with(self.job)
        self.assertTrue(adapter.mark_unknown(self.job, self.token, "PRIVATE_UPLOAD_UNCERTAIN"))
        ledger.unknown_motion.assert_called_once_with(self.job, self.token, "PRIVATE_UPLOAD_UNCERTAIN")
        adapter.complete(self.job, self.token, {"private": True})
        ledger.complete_motion.assert_called_once()

    def test_quota_and_other_tenant_denied(self):
        bads = [
            {"status": "QUEUED"}, {"model_id": "wan2.7-i2v-2026-04-25"},
            {"subscription_active": False}, {"user_approved": False},
            {"rights_approved": False}, {"review_status": "DRAFT"},
            {"reserved_usd": float("NaN")}, {"reserved_usd": "0"},
            {"reserved_usd": True}, {"reserved_usd": "-1"},
            {"resolution": "720P"}, {"seconds": 10},
            {"attempt_token": "forged/lease"}, {"reservation_id": None},
            {"idempotency_key": "bad"}, {"source_asset_id": "https://evil.invalid"},
        ]
        for changes in bads:
            with self.subTest(changes=changes):
                row = dict(self.row, **changes)
                with self.assertRaises(MotionError):
                    verified_claim_to_motion(row)

    def test_foreign_job_from_ledger_denied(self):
        ledger = Mock()
        ledger.claim_authorized_motion.return_value = dict(self.row, id=uid())
        with self.assertRaises(MotionError):
            Part3MotionStoreAdapter(ledger).claim(self.job)

    def test_duplicate_key_for_same_request_and_separate_tenants(self):
        one = planned_motion_key(self.shop, uid(), self.source, "feature5-v1", "image", HUNYUAN_MODEL)
        # same inputs deterministic
        day = uid()
        a = planned_motion_key(self.shop, day, self.source, "feature5-v1", "image", HUNYUAN_MODEL)
        b = planned_motion_key(self.shop, day, self.source, "feature5-v1", "image", HUNYUAN_MODEL)
        c = planned_motion_key(uid(), day, self.source, "feature5-v1", "image", HUNYUAN_MODEL)
        self.assertNotEqual(one, a)
        self.assertEqual(a, b)
        self.assertNotEqual(a, c)
        with self.assertRaises(MotionError):
            planned_motion_key(self.shop, day, self.source, "feature5-v1", "image", "unknown-model")

    def test_text_claim_rejects_image_attachment(self):
        row = dict(self.row, mode="text", source_asset_id=None)
        spec, _ = verified_claim_to_motion(row)
        self.assertIsNone(spec.source_asset_id)
        with self.assertRaises(MotionError):
            verified_claim_to_motion(dict(row, source_asset_id=self.source))


class TestFeature4Handoff(unittest.TestCase):
    def setUp(self):
        self.shop = uid()
        self.job = uid()
        self.token = uid()
        self.clip = uid()
        self.path = f"{self.shop}/renders/{self.job}/{self.token}.mp4"
        self.rights = {"commercial_use": True, "license": "owned", "evidence": "Approved retailer-owned licensed footage", "source": "RetailGrowthAI generated motion"}
        self.row = {
            "job_id": self.job, "shop_id": self.shop, "clip_asset_id": self.clip,
            "attempt_token": self.token, "storage_path": self.path,
            "status": "SUCCEEDED", "provenance": HUNYUAN_MODEL,
            "quality_status": "APPROVED", "output_codec": "h264",
            "rights_approved": True, "duration_seconds": 5.0,
        }

    def ready(self, **overrides):
        return ApprovedMotionClip(**dict(self.row, **overrides))

    def test_feature4_trusted_video_manifest(self):
        asset_id, entry = feature4_asset_entry(
            self.ready(), shop_id=self.shop, local_staged_path="clips/fashion.mp4",
            rights=self.rights)
        self.assertEqual(asset_id, self.clip)
        self.assertEqual(FEATURE4_VERSION, "creative_reel_v1")
        self.assertEqual(entry["source_feature"], "feature5")
        self.assertEqual(entry["kind"], "video")
        self.assertEqual(entry["path"], "clips/fashion.mp4")
        scene = feature4_scene(asset_id, order=1, start_time=3,
                               headline="Luxury Boutique")
        self.assertEqual(scene["motion_status"], "ready")
        self.assertEqual(scene["source_feature"], "feature5")
        self.assertNotIn("text_overlay", scene)

    def test_foreign_or_unreviewed_motion_denied(self):
        for value in [
            {"shop_id": uid()}, {"storage_path": self.path + ".bak"},
            {"attempt_token": uid()}, {"status": "FAILED"},
            {"quality_status": "PENDING"}, {"provenance": "synthetic-fixture"},
            {"rights_approved": False}, {"output_codec": "av1"},
            {"duration_seconds": 30},
        ]:
            with self.subTest(value=value), self.assertRaises(MotionError):
                feature4_asset_entry(self.ready(**value), shop_id=self.shop,
                                     local_staged_path="clips/fashion.mp4", rights=self.rights)

    def test_foreign_path_or_unlicensed_clips_denied(self):
        for staged in ("/tmp/secret.mp4", "../escape.mp4", "http://host/video.mp4",
                       "clips/../escape.mp4", "clips\\evil.mp4"):
            with self.subTest(path=staged), self.assertRaises(MotionError):
                feature4_asset_entry(self.ready(), shop_id=self.shop, local_staged_path=staged,
                                     rights=self.rights)
        with self.assertRaises(MotionError):
            feature4_asset_entry(self.ready(), shop_id=self.shop,
                                 local_staged_path="clips/fashion.mp4",
                                 rights={"commercial_use": True, "license": "unreviewed", "source": "retailer", "evidence": "none"})


if __name__ == "__main__":
    unittest.main()
