"""Read-only Feature3 operator reconciliation; never rerun/settle paid work."""
from pathlib import Path
import sys
import unittest
from uuid import uuid4

sys.path.insert(0,str(Path(__file__).resolve().parents[2]/"azure-functions/campaign-api"))
from feature3_gpu_operator_reconciliation import (
    Feature3GPUOperatorReconciliation,Feature3ReconciliationUnknown,
)

class FakeDB:
    def __init__(self):
        self.shop,self.job,self.rid,self.asset=[str(uuid4()) for _ in range(4)]
        self.jobrow={"id":self.job,"shop_id":self.shop,"status":"RUNNING",
                     "reservation_id":self.rid,"attempts":1,
                     "claim_token":str(uuid4()),"lease_until":"2026-10-28T00:00:00Z",
                     "output_asset_id":None}
        self.spending={"id":self.rid,"shop_id":self.shop,
                       "operation":"image_generation","state":"RESERVED",
                       "reserved_usd":"0.050000","actual_usd":None}
        self.calls=[]
        self.private_reads=[]
        self.evidence={"shop_id":self.shop,"job_id":self.job,
                       "media_asset_id":self.asset,"image_sha256":"a"*64,
                       "private":True,"attempt":1,"review_status":"UNREVIEWED"}
    def request(self,table,*,query,method="GET",data=None):
        self.calls.append((table,query,method))
        if method!="GET" or data is not None:
            raise AssertionError("Reconciliation cannot mutate database")
        if table=="feature3_gpu_jobs":return [dict(self.jobrow)]
        if table=="shop_ai_spend_reservations":return [dict(self.spending)]
        raise AssertionError("Unexpected backend access")
    def evidence_read(self,shop,job,asset):
        self.private_reads.append((shop,job,asset))
        return dict(self.evidence)

class ReconciliationTests(unittest.TestCase):
    def setUp(self):
        self.db=FakeDB()
        self.inspector=Feature3GPUOperatorReconciliation(
            admin_store=self.db,read_private_evidence=self.db.evidence_read)
    def inspect(self):
        return self.inspector.inspect(shop_id=self.db.shop,job_id=self.db.job)
    def assert_no_money_or_retry(self,receipt):
        for k in ("automatic_retry_permitted","automatic_refund_permitted",
                  "automatic_finalize_permitted","automatic_storage_delete_permitted",
                  "gpu_invoked"):
            self.assertIs(receipt[k],False)
        self.assertTrue(receipt["operator_review_required"])
        self.assertEqual(receipt["charged_now_usd"],"0.00")
        self.assertEqual([x[2] for x in self.db.calls],["GET","GET"])

    def test_stale_running_is_held_without_charge_refund_delete(self):
        result=self.inspect()
        self.assertEqual(result["classification"],"PENDING_OR_UNCERTAIN_HOLD")
        self.assert_no_money_or_retry(result)
        self.assertEqual(self.db.private_reads,[])

    def test_queued_does_not_trigger_claim_or_publisher_replay(self):
        self.db.jobrow.update({"status":"QUEUED","attempts":0,
                               "claim_token":None,"lease_until":None})
        result=self.inspect()
        self.assertEqual(result["classification"],"PENDING_OR_UNCERTAIN_HOLD")
        self.assert_no_money_or_retry(result)

    def test_measured_terminal_failure_is_observed_only(self):
        self.db.jobrow.update({"status":"FAILED","claim_token":None,
                               "lease_until":None})
        self.db.spending.update({"state":"SETTLED","actual_usd":"0.011000"})
        result=self.inspect()
        self.assertEqual(result["classification"],"TERMINAL_FAILURE_OBSERVED")
        self.assert_no_money_or_retry(result)
        self.assertEqual(self.db.private_reads,[])

    def test_success_requires_immutable_private_evidence_and_settlement(self):
        self.db.jobrow.update({"status":"SUCCEEDED","output_asset_id":self.db.asset,
                               "claim_token":None,"lease_until":None})
        self.db.spending.update({"state":"SETTLED","actual_usd":"0.011000"})
        result=self.inspect()
        self.assertEqual(result["classification"],"TERMINAL_SUCCESS_EVIDENCE_OBSERVED")
        self.assertEqual(self.db.private_reads,[(self.db.shop,self.db.job,self.db.asset)])
        self.assert_no_money_or_retry(result)

    def test_bogus_or_incomplete_settlement_stays_untrusted(self):
        for state,actual in (("SETTLED","0.100000"),
                             ("RESERVED","0.001000"),
                             ("SETTLED","NaN"),
                             ("SETTLED","-0.01"),
                             ("SETTLED",True),
                             ("REFUNDED",None)):
            self.setUp()
            self.db.spending.update({"state":state,"actual_usd":actual})
            with self.subTest(state=state,actual=actual),self.assertRaises(
                Feature3ReconciliationUnknown):
                self.inspect()

    def test_cross_tenant_forged_job_or_reservation_is_untrusted(self):
        for table in ("jobrow","spending"):
            self.setUp()
            getattr(self.db,table)["shop_id"]=str(uuid4())
            with self.subTest(table=table),self.assertRaises(Feature3ReconciliationUnknown):
                self.inspect()

    def test_output_evidence_must_be_exact_and_human_unapproved(self):
        self.db.jobrow.update({"status":"SUCCEEDED","output_asset_id":self.db.asset})
        self.db.spending.update({"state":"SETTLED","actual_usd":"0.011000"})
        for corrupt in ({"shop_id":str(uuid4())},
                        {"private":False},{"review_status":"APPROVED"},
                        {"attempt":2},{"image_sha256":"b"*63},
                        {"media_asset_id":str(uuid4())},{"url":"public"}):
            self.db.evidence={"shop_id":self.db.shop,"job_id":self.db.job,
                "media_asset_id":self.db.asset,"image_sha256":"a"*64,
                "private":True,"attempt":1,"review_status":"UNREVIEWED",**corrupt}
            with self.subTest(corrupt=corrupt),self.assertRaises(
                Feature3ReconciliationUnknown):
                self.inspect()
        self.db.private_reads.clear()

    def test_absent_private_proof_or_settlement_denied(self):
        self.db.jobrow.update({"status":"SUCCEEDED","output_asset_id":self.db.asset})
        self.db.spending.update({"state":"SETTLED","actual_usd":"0.011000"})
        self.db.evidence=None
        def missing(*args):return None
        self.inspector=Feature3GPUOperatorReconciliation(
            admin_store=self.db,read_private_evidence=missing)
        with self.assertRaises(Feature3ReconciliationUnknown):
            self.inspect()

if __name__=="__main__":
    unittest.main()
