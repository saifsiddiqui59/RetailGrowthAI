"""Offline Feature4 additive HTTP handoff tests; NOT a deployed Azure endpoint."""
import copy
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "video-engine"))
from feature4_http_handoff import Feature4HTTP  # noqa: E402

SHOP = "11111111-1111-4111-8111-111111111111"
OTHER = "44444444-4444-4444-8444-444444444444"
CAMPAIGN = "22222222-2222-4222-8222-222222222222"
JOB = "33333333-3333-4333-8333-333333333333"
LEASE = "55555555-5555-4555-8555-555555555555"
ASSET = "66666666-6666-4666-8666-666666666666"
JWT = "authenticated-user-jwt"
USER = "verified-user"


def intent():
    return {
        "shop_id": SHOP, "campaign_id": CAMPAIGN, "approval_id": "feature2-approved-1",
        "draft": {
            "version": "rg_video_v2", "shop_id": SHOP,
            "duration_seconds": 30,
            "scenes": [
                {"start": 0, "duration": 15, "headline": "Diwali Sale"},
                {"start": 15, "duration": 15, "headline": "Visit Our Store"},
            ],
        },
    }


class Users:
    def __init__(self):
        self.allow_read = True
        self.allow_write = True
        self.campaign_data = {"shop_id": SHOP, "id": CAMPAIGN, "status": "DRAFT"}
        self.job = {"shop_id": SHOP, "id": JOB, "status": "QUEUED",
                    "output_asset_id": None}
        self.asset_data = {"shop_id": SHOP, "mime_type": "video/mp4",
                           "storage_bucket": "retailgrowth-media",
                           "object_path": SHOP + "/renders/" + JOB + "/" + LEASE + ".mp4"}
        self.signed = []

    def campaign(self, token, user_id, campaign_id):
        assert token == JWT and user_id == USER and campaign_id == CAMPAIGN
        return self.campaign_data

    def member(self, token, user_id, shop_id, write):
        assert token == JWT and user_id == USER and shop_id in (SHOP, OTHER)
        return self.allow_write if write else self.allow_read

    def feature4_job(self, token, user_id, job_id):
        assert token == JWT and user_id == USER and job_id == JOB
        return self.job

    def asset(self, token, shop_id, asset_id):
        assert token == JWT and shop_id == SHOP and asset_id == ASSET
        return self.asset_data

    def sign_download(self, token, shop_id, object_path):
        assert token == JWT and shop_id == SHOP
        self.signed.append(object_path)
        return "https://example.supabase.co/storage/v1/object/sign/retailgrowth-media/" + object_path + "?token=private-example"


class Admin:
    def __init__(self):
        self.calls = []
        self.jobs = {}

    def create_feature4_intent(self, item):
        self.calls.append(item)
        key = item["idempotency_key"]
        self.jobs.setdefault(key, {"id": JOB, "shop_id": SHOP, "status": "QUEUED"})
        return self.jobs[key]


class Feature4HTTPHandoffTests(unittest.TestCase):
    def setUp(self):
        self.users = Users()
        self.admin = Admin()
        self.api = Feature4HTTP(self.users, self.admin)

    def create(self, body=None):
        return self.api.create(JWT, USER, CAMPAIGN, intent() if body is None else body)

    def test_create_authorized_once_and_stable_idempotency(self):
        status, result = self.create()
        self.assertEqual((status, result), (202, {"shop_id": SHOP, "job_id": JOB, "status": "QUEUED"}))
        self.assertEqual(self.create(), (202, result))
        self.assertEqual(len(self.admin.calls), 2)
        self.assertEqual(len(self.admin.jobs), 1)  # atomic backend does one reservation
        item = self.admin.calls[0]
        self.assertEqual(item["preset"], "feature4_reel_v1")
        self.assertEqual(item["shop_id"], SHOP)
        self.assertEqual(item["requested_by"], USER)
        self.assertEqual(item["idempotency_key"], self.admin.calls[1]["idempotency_key"])
        self.assertEqual(len(item["idempotency_key"]), 64)

    def test_invalid_path_tenant_or_body_cannot_reserve(self):
        for modifier in (
            lambda b: b.update(shop_id=OTHER),
            lambda b: b.update(campaign_id=OTHER),
            lambda b: b.update(approval_id="../../unsafe"),
            lambda b: b["draft"].update(shop_id=OTHER),
            lambda b: b["draft"].update(version="creative_reel_v1"),
            lambda b: b["draft"].update(duration_seconds=1000),
            lambda b: b["draft"].update(scenes=[]),
            lambda b: b.update(asset_url="https://external.invalid/untrusted.png"),
        ):
            body = intent()
            modifier(body)
            with self.subTest(body=body):
                status, _ = self.create(body)
                self.assertIn(status, (400, 404))
        self.assertEqual(self.admin.calls, [])

    def test_missing_campaign_or_write_membership_blocks_paid_job(self):
        self.users.campaign_data = None
        self.assertEqual(self.create()[0], 404)
        self.users.campaign_data = {"shop_id": OTHER}
        self.assertEqual(self.create()[0], 404)
        self.users.campaign_data = {"shop_id": SHOP}
        self.users.allow_write = False
        self.assertEqual(self.create()[0], 403)
        self.assertEqual(self.admin.calls, [])

    def test_status_scoped_to_shop_and_verifies_job_receipt(self):
        self.assertEqual(self.api.get(JWT, USER, JOB),
                         (200, {"shop_id": SHOP, "job_id": JOB, "status": "QUEUED"}))
        self.users.allow_read = False
        self.assertEqual(self.api.get(JWT, USER, JOB)[0], 404)
        self.users.allow_read = True
        self.users.job["shop_id"] = OTHER
        self.users.allow_read = False
        self.assertEqual(self.api.get(JWT, USER, JOB)[0], 404)

    def test_download_is_only_private_same_shop_and_claim_token(self):
        self.users.job.update(status="SUCCEEDED", output_asset_id=ASSET)
        status, result = self.api.download(JWT, USER, JOB)
        self.assertEqual(status, 200)
        self.assertEqual(result["job_id"], JOB)
        self.assertEqual(result["shop_id"], SHOP)
        self.assertEqual(self.users.signed, [self.users.asset_data["object_path"]])

    def test_no_signature_on_pending_failed_foreign_media(self):
        self.assertEqual(self.api.download(JWT, USER, JOB)[0], 409)
        self.users.job.update(status="FAILED", output_asset_id=ASSET)
        self.assertEqual(self.api.download(JWT, USER, JOB)[0], 409)
        self.users.job["status"] = "SUCCEEDED"
        bad_records = [
            {"shop_id": OTHER}, {"mime_type": "image/png"},
            {"storage_bucket": "public"},
            {"object_path": OTHER + "/renders/" + JOB + "/" + LEASE + ".mp4"},
            {"object_path": SHOP + "/renders/" + OTHER + "/" + LEASE + ".mp4"},
            {"object_path": SHOP + "/renders/" + JOB + "/../replay.mp4"},
        ]
        original = copy.deepcopy(self.users.asset_data)
        for bad in bad_records:
            with self.subTest(bad=bad):
                self.users.asset_data = {**original, **bad}
                self.assertEqual(self.api.download(JWT, USER, JOB)[0], 404)
        self.assertEqual(self.users.signed, [])

    def test_wrong_job_id_from_atomic_insert_fails_closed(self):
        self.admin.create_feature4_intent = lambda item: {
            "id": "not-a-uuid", "shop_id": SHOP, "status": "QUEUED",
        }
        with self.assertRaises(ValueError):
            self.create()

    def test_excessively_large_draft_is_rejected_pre_insert(self):
        payload = intent()
        payload["draft"]["scenes"][0]["headline"] = "x" * 100_000
        self.assertEqual(self.create(payload)[0], 400)
        self.assertEqual(self.admin.calls, [])


if __name__ == "__main__":
    unittest.main()
