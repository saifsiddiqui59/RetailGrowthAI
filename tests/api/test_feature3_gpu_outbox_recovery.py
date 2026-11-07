"""No-GPU, no queue, no billing: outbox claim/ACK/recovery transports."""
from pathlib import Path
import sys
import unittest
from unittest.mock import Mock
from uuid import uuid4

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "azure-functions/campaign-api"))
from feature3_gpu_outbox_service import Feature3GPUOutboxService
from tenant_store import StorageUnavailable


class GPUOutboxTests(unittest.TestCase):
    def setUp(self):
        self.shop, self.job, self.token = (str(uuid4()) for _ in range(3))
        self.store = Feature3GPUOutboxService("https://example.supabase.co","sb_secret_fake")
        self.store.db.request = Mock()
        self.packet = {"shop_id":self.shop,"job_id":self.job,
                       "dispatch_token":self.token,"expires_in_seconds":120}

    def test_one_shot_claim_is_metadata_only(self):
        self.store.db.request.return_value = [dict(self.packet)]
        result = self.store.claim_dispatch(1)
        self.assertEqual(result[0]["job_id"],self.job)
        self.assertFalse(result[0]["gpu_started"])
        self.assertNotIn("image_bytes",str(result))
        self.store.db.request.assert_called_once_with(
            "rpc/feature3_claim_gpu_dispatch",method="POST",data={"p_limit":1})

    def test_empty_queue_does_nothing(self):
        self.store.db.request.return_value = []
        self.assertEqual(self.store.claim_dispatch(),[])
        self.assertEqual(self.store.db.request.call_count,1)

    def test_invalid_claim_batch_never_published(self):
        for payload in (None,{},[{},{}],
                        [{**self.packet,"job_id":"not-uuid"}],
                        [{**self.packet,"expires_in_seconds":121}],
                        [dict(self.packet),dict(self.packet)]):
            with self.subTest(payload=payload):
                self.store.db.request.reset_mock(return_value=True)
                self.store.db.request.return_value=payload
                with self.assertRaises(StorageUnavailable):
                    self.store.claim_dispatch(2)
                self.assertEqual(self.store.db.request.call_count,1)

    def test_distinct_jobs_cannot_share_one_dispatch_lease_token(self):
        # A malformed privileged SQL response must be rejected atomically
        # before any row reaches a queue publisher or ACK path.
        second = {**self.packet, "job_id": str(uuid4())}
        self.store.db.request.return_value = [dict(self.packet), second]
        with self.assertRaisesRegex(StorageUnavailable, "repeated GPU dispatch"):
            self.store.claim_dispatch(2)
        self.store.db.request.assert_called_once_with(
            "rpc/feature3_claim_gpu_dispatch", method="POST", data={"p_limit": 2})

    def test_distinct_dispatch_tokens_are_accepted_for_distinct_jobs(self):
        second = {**self.packet, "job_id": str(uuid4()),
                  "dispatch_token": str(uuid4())}
        self.store.db.request.return_value = [dict(self.packet), second]
        rows = self.store.claim_dispatch(2)
        self.assertEqual(len(rows), 2)
        self.assertNotEqual(rows[0]["dispatch_token"], rows[1]["dispatch_token"])
        self.assertTrue(all(row["gpu_started"] is False for row in rows))

    def test_queue_ack_is_separate_from_paid_worker_claim(self):
        self.store.db.request.return_value = True
        self.assertTrue(self.store.confirm_dispatch(self.job,self.token,True))
        self.store.db.request.assert_called_once_with(
            "rpc/feature3_confirm_gpu_dispatch",method="POST",
            data={"p_job_id":self.job,"p_dispatch_token":self.token,"p_sent":True})

    def test_missing_ack_is_not_safe_to_retry(self):
        for result in (False,None,{"sent":True}):
            self.store.db.request.reset_mock(return_value=True)
            self.store.db.request.return_value=result
            with self.assertRaises(StorageUnavailable):
                self.store.confirm_dispatch(self.job,self.token,True)
            self.assertEqual(self.store.db.request.call_count,1)

    def test_nonboolean_ack_and_invalid_limits_denied_before_network(self):
        for sent in (None,1,"true"):
            with self.assertRaises(ValueError):
                self.store.confirm_dispatch(self.job,self.token,sent)
        for limit in (0,11,True,"2"):
            with self.assertRaises(ValueError):
                self.store.claim_dispatch(limit)
        self.store.db.request.assert_not_called()

    def test_incident_audit_preserves_uncertain_cost(self):
        self.store.db.request.return_value = 2
        result = self.store.audit_recovery(3)
        self.assertEqual(result["events_recorded"],2)
        self.assertFalse(result["paid_retry_authorized"])
        self.assertEqual(result["financial_state"],
                         "UNDETERMINED_REQUIRES_OPERATOR_RECONCILIATION")
        self.store.db.request.assert_called_once_with(
            "rpc/feature3_audit_gpu_recovery",method="POST",data={"p_limit":3})

    def test_bad_incident_audit_does_not_estimate_charges(self):
        for invalid in (None,-1,True,1.5,9):
            self.store.db.request.reset_mock(return_value=True)
            self.store.db.request.return_value=invalid
            with self.assertRaises(StorageUnavailable):
                self.store.audit_recovery(3)
            self.assertEqual(self.store.db.request.call_count,1)

if __name__=="__main__":
    unittest.main()
