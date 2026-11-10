"""Feature3 service-only GPU SQL adapter; mocked PostgREST, no GPU/cloud spend."""
from datetime import datetime, timedelta, timezone
from pathlib import Path
import sys
import unittest
from unittest.mock import Mock
from uuid import uuid4
from urllib.error import URLError

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "azure-functions/campaign-api"))
from feature3_gpu_service import Feature3GPUServiceStore
from tenant_store import StorageUnavailable

class GPUServiceTransportTests(unittest.TestCase):
    def setUp(self):
        self.shop, self.actor, self.design, self.request_id = [str(uuid4()) for _ in range(4)]
        self.job, self.reservation, self.token, self.asset = [str(uuid4()) for _ in range(4)]
        self.store = Feature3GPUServiceStore("https://example.supabase.co",
                                               "sb_secret_example")
        self.store.db.request = Mock()

    def _reserve(self, **overrides):
        args = dict(shop_id=self.shop, actor_id=self.actor, design_id=self.design,
                    revision=3, design_sha256="a"*64, request_id=self.request_id,
                    upper_cost_usd="0.050000")
        args.update(overrides)
        return self.store.reserve(**args)

    def test_reserve_exact_sql_and_no_duplicate_wallet(self):
        self.store.db.request.return_value = {
            "shop_id": self.shop, "job_id": self.job,
            "reservation_id": self.reservation, "reserved_usd": "0.050000",
            "status": "QUEUED", "gpu_started": False,
        }
        receipt = self._reserve()
        self.assertEqual(receipt["job_id"], self.job)
        self.store.db.request.assert_called_once_with(
            "rpc/feature3_reserve_gpu_job", method="POST",
            data={"p_shop_id":self.shop,"p_actor_id":self.actor,
                  "p_design_id":self.design,"p_expected_revision":3,
                  "p_expected_sha256":"a"*64,"p_request_id":self.request_id,
                  "p_upper_cost_usd":"0.050000"})
        self.assertFalse(receipt["gpu_started"])

    def test_invalid_or_ambiguous_reservation_never_retried(self):
        for invalid in (None, [], {"status":"QUEUED"}, {
            "shop_id":self.shop,"job_id":self.job,"reservation_id":self.reservation,
            "reserved_usd":"0.01","status":"QUEUED","gpu_started":False}):
            with self.subTest(invalid=invalid):
                self.store.db.request.reset_mock(return_value=True)
                self.store.db.request.return_value=invalid
                with self.assertRaises(StorageUnavailable):
                    self._reserve()
                self.assertEqual(self.store.db.request.call_count,1)
        for cost in ("NaN", "-0.1", "2.500001", "0", 0.1_0000001):
            self.store.db.request.reset_mock()
            with self.assertRaises(ValueError):
                self._reserve(upper_cost_usd=cost)
            self.store.db.request.assert_not_called()

    def test_claim_first_attempt_and_fencing(self):
        self.store.db.request.return_value = {
            "shop_id":self.shop,"job_id":self.job,"attempt":1,
            "claim_token":self.token}
        self.assertEqual(self.store.claim(self.job,self.token)["attempt"],1)
        self.store.db.request.assert_called_once_with(
            "rpc/feature3_claim_gpu_job",method="POST",
            data={"p_job_id":self.job,"p_claim_token":self.token})
        self.store.db.request.reset_mock()
        self.store.db.request.return_value=None
        self.assertIsNone(self.store.claim(self.job,self.token))
        self.assertEqual(self.store.db.request.call_count,1)
        self.store.db.request.reset_mock()
        self.store.db.request.return_value={
            "shop_id":self.shop,"job_id":self.job,"attempt":2,
            "claim_token":self.token}
        with self.assertRaises(StorageUnavailable):
            self.store.claim(self.job,self.token)

    def test_read_prepaid_two_same_shop_rows_and_active_lease(self):
        lease=(datetime.now(timezone.utc)+timedelta(minutes=8)).isoformat()
        self.store.db.request.side_effect=[
            {"UNUSED":"not a list"}] # malformed response fails closed first
        with self.assertRaises(StorageUnavailable):
            self.store.read_prepaid_reservation(self.shop,self.job,1,self.token)
        self.store.db.request.reset_mock(side_effect=True)
        self.store.db.request.side_effect=[
            [{"id":self.job,"shop_id":self.shop,"reservation_id":self.reservation,
              "status":"RUNNING","attempts":1,"claim_token":self.token,
              "lease_until":lease}],
            [{"id":self.reservation,"shop_id":self.shop,"operation":"image_generation",
              "state":"RESERVED","reserved_usd":"0.050000"}],
        ]
        proof=self.store.read_prepaid_reservation(self.shop,self.job,1,self.token)
        self.assertEqual(proof["reservation_id"],self.reservation)
        self.assertEqual(self.store.db.request.call_count,2)
        self.assertEqual(proof["claim_token"],self.token)

    def test_denies_foreign_stale_and_expired_lease(self):
        for overrides in (
            {"shop_id":str(uuid4())},
            {"claim_token":str(uuid4())},
            {"status":"FAILED"},
            {"lease_until":(datetime.now(timezone.utc)-timedelta(seconds=1)).isoformat()},
        ):
            row={"id":self.job,"shop_id":self.shop,"reservation_id":self.reservation,
                 "status":"RUNNING","attempts":1,"claim_token":self.token,
                 "lease_until":(datetime.now(timezone.utc)+timedelta(minutes=5)).isoformat()}
            row.update(overrides)
            self.store.db.request.reset_mock(side_effect=True)
            self.store.db.request.return_value=[row]
            with self.assertRaises(StorageUnavailable):
                self.store.read_prepaid_reservation(self.shop,self.job,1,self.token)
            self.assertEqual(self.store.db.request.call_count,1)

    def test_finish_requires_explicit_sql_boolean_ack(self):
        self.store.db.request.return_value=True
        self.assertTrue(self.store.finish(self.job,self.token,"0.012500",self.asset))
        self.store.db.request.assert_called_once_with(
            "rpc/feature3_finish_gpu_job",method="POST",
            data={"p_job_id":self.job,"p_claim_token":self.token,
                  "p_actual_usd":"0.012500","p_asset_id":self.asset})
        self.store.db.request.reset_mock()
        self.store.db.request.return_value=None
        with self.assertRaises(StorageUnavailable):
            self.store.finish(self.job,self.token,"0.012500",self.asset)
        self.assertEqual(self.store.db.request.call_count,1)

    def test_service_key_not_bearer_client_and_transport_not_retried(self):
        calls=[]
        def network(req,timeout):
            calls.append(req)
            raise URLError("unknown ack")
        actual=Feature3GPUServiceStore("https://example.supabase.co",
                                          "sb_secret_example",transport=network)
        with self.assertRaises(StorageUnavailable):
            actual.claim(self.job,self.token)
        self.assertEqual(len(calls),1)
        self.assertEqual(calls[0].get_header("Apikey"),"sb_secret_example")
        self.assertIsNone(calls[0].get_header("Authorization"))
        self.assertIn("/rest/v1/rpc/feature3_claim_gpu_job",calls[0].full_url)

if __name__=="__main__":
    unittest.main()
