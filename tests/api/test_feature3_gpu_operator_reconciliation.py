"""Read-only Feature3 operator reconciliation; never rerun/settle paid work."""
from hashlib import sha256
from io import BytesIO
from pathlib import Path
from PIL import Image
import sys
import unittest
from uuid import uuid4

sys.path.insert(0,str(Path(__file__).resolve().parents[2]/"azure-functions/campaign-api"))
from feature3_gpu_operator_reconciliation import (
    Feature3GPUOperatorReconciliation,Feature3ReconciliationUnknown,
    build_verified_feature3_operator_reconciliation,
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
        self.on_evidence_read=None
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
        if self.on_evidence_read:self.on_evidence_read()
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
        expected=4 if receipt["classification"]=="TERMINAL_SUCCESS_EVIDENCE_OBSERVED" else 2
        self.assertEqual([x[2] for x in self.db.calls],["GET"]*expected)

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
        self.db.jobrow.update({"status":"SUCCEEDED","output_asset_id":self.db.asset,
                               "claim_token":None,"lease_until":None})
        self.db.spending.update({"state":"SETTLED","actual_usd":"0.011000"})
        for corrupt in ({"shop_id":str(uuid4())},
                        {"private":False},{"review_status":"APPROVED"},
                        {"attempt":2},{"attempt":True},{"attempt":1.0},
                        {"attempt":"1"},{"image_sha256":"b"*63},
                        {"media_asset_id":str(uuid4())},{"url":"public"}):
            self.db.evidence={"shop_id":self.db.shop,"job_id":self.db.job,
                "media_asset_id":self.db.asset,"image_sha256":"a"*64,
                "private":True,"attempt":1,"review_status":"UNREVIEWED",**corrupt}
            with self.subTest(corrupt=corrupt),self.assertRaises(
                Feature3ReconciliationUnknown):
                self.inspect()
        self.db.private_reads.clear()

    def test_absent_private_proof_or_settlement_denied(self):
        self.db.jobrow.update({"status":"SUCCEEDED","output_asset_id":self.db.asset,
                               "claim_token":None,"lease_until":None})
        self.db.spending.update({"state":"SETTLED","actual_usd":"0.011000"})
        self.db.evidence=None
        def missing(*args):return None
        self.inspector=Feature3GPUOperatorReconciliation(
            admin_store=self.db,read_private_evidence=missing)
        with self.assertRaises(Feature3ReconciliationUnknown):
            self.inspect()


    def test_queued_running_and_terminal_claim_state_must_match_real_sql(self):
        for changes in (
            {"status":"QUEUED","attempts":1,"claim_token":None,"lease_until":None},
            {"status":"QUEUED","attempts":0,"claim_token":str(uuid4()),"lease_until":None},
            {"status":"RUNNING","attempts":0},
            {"status":"RUNNING","claim_token":None},
            {"status":"RUNNING","lease_until":"yesterday"},
            {"status":"RUNNING","lease_until":"2026-10-29T18:00:00"},
            {"status":"FAILED","attempts":1},
            {"status":"SUCCEEDED","attempts":1},
        ):
            self.setUp()
            self.db.jobrow.update(changes)
            with self.subTest(changes=changes),self.assertRaises(Feature3ReconciliationUnknown):
                self.inspect()
            self.assertEqual(self.db.private_reads,[])

    def test_recheck_job_and_ledger_during_private_proof(self):
        for target,field,value in (
            ("jobrow","status","FAILED"),
            ("jobrow","attempts",0),
            ("spending","state","RESERVED"),
            ("spending","actual_usd","0.029000"),
        ):
            self.setUp()
            self.db.jobrow.update({"status":"SUCCEEDED","output_asset_id":self.db.asset,
                                   "claim_token":None,"lease_until":None})
            self.db.spending.update({"state":"SETTLED","actual_usd":"0.011000"})
            self.db.on_evidence_read=lambda: getattr(self.db,target).__setitem__(field,value)
            with self.subTest(target=target,field=field),self.assertRaises(
                    Feature3ReconciliationUnknown):
                self.inspect()
            self.assertEqual(self.db.private_reads,[(self.db.shop,self.db.job,self.db.asset)])
            self.assertEqual([q[2] for q in self.db.calls],["GET"]*3 if target=="jobrow" else ["GET"]*4)

    def test_private_evidence_error_never_leaks_storage_paths_or_money(self):
        self.db.jobrow.update({"status":"SUCCEEDED","output_asset_id":self.db.asset,
                               "claim_token":None,"lease_until":None})
        self.db.spending.update({"state":"SETTLED","actual_usd":"0.011000"})
        secret="shop-private/secret-storage-path?token=example"
        def inaccessible(*_):
            raise OSError(secret)
        self.inspector=Feature3GPUOperatorReconciliation(
            admin_store=self.db,read_private_evidence=inaccessible)
        with self.assertRaises(Feature3ReconciliationUnknown) as caught:
            self.inspect()
        self.assertEqual(str(caught.exception),"Private output evidence unavailable")
        self.assertNotIn(secret,str(caught.exception))
        self.assertEqual(len(self.db.calls),2)
        self.assertEqual([x[2] for x in self.db.calls],["GET"]*2)

    def test_unknown_post_evidence_sql_read_is_not_a_success_receipt(self):
        self.db.jobrow.update({"status":"SUCCEEDED","output_asset_id":self.db.asset,
                               "claim_token":None,"lease_until":None})
        self.db.spending.update({"state":"SETTLED","actual_usd":"0.011000"})
        initial=self.db.request
        secret="service-internal-key-private-do-not-expose"
        def fail_reread(table,*,query,method="GET",data=None):
            if len(self.db.calls)>=2:
                raise RuntimeError(secret)
            return initial(table,query=query,method=method,data=data)
        self.db.request=fail_reread
        with self.assertRaises(Feature3ReconciliationUnknown) as caught:
            self.inspect()
        self.assertEqual(str(caught.exception),
                         "Current job or reservation read unavailable")
        self.assertNotIn(secret,str(caught.exception))
        self.assertEqual(self.db.private_reads,[
            (self.db.shop,self.db.job,self.db.asset)])
        self.assertEqual([x[2] for x in self.db.calls],["GET"]*2)


    def test_initial_job_and_reservation_sql_errors_do_not_expose_secrets(self):
        secret="internal-database-credential-in-backend-error"
        for table,expected in (
            ("feature3_gpu_jobs","Current job read unavailable"),
            ("shop_ai_spend_reservations","Current reservation read unavailable"),
        ):
            self.setUp()
            original=self.db.request
            def unavailable(path,*,query,method="GET",data=None):
                if path==table:
                    raise RuntimeError(secret)
                return original(path,query=query,method=method,data=data)
            self.db.request=unavailable
            with self.subTest(table=table),self.assertRaises(
                    Feature3ReconciliationUnknown) as caught:
                self.inspect()
            self.assertEqual(str(caught.exception),expected)
            self.assertNotIn(secret,str(caught.exception))
            self.assertTrue(caught.exception.__suppress_context__)
            self.assertEqual(self.db.private_reads,[])
            self.assertTrue(all(method=="GET" for _,__,method in self.db.calls))

    def test_actual_private_png_reader_composed_with_service_sql_reconciliation(self):
        image=BytesIO()
        Image.new("RGB",(320,400),"#446688").save(image,format="PNG")
        original=image.getvalue()
        digest=sha256(original).hexdigest()
        db=self.db
        db.origin="https://fixture.supabase.co"
        db.secret="sb_secret_"+"p"*40
        db.jobrow.update({"status":"SUCCEEDED","output_asset_id":db.asset,
                          "claim_token":None,"lease_until":None})
        db.spending.update({"state":"SETTLED","actual_usd":"0.011000"})
        real_path=f"{db.shop}/feature3/gpu/{db.job}/{digest}.png"
        prior_request=db.request
        def authoritative_request(path,*,query=None,method="GET",data=None):
            if path=="rpc/feature3_read_gpu_private_evidence":
                self.assertEqual(method,"POST")
                self.assertEqual(data,{"p_shop_id":db.shop,"p_job_id":db.job,
                                       "p_media_asset_id":db.asset})
                return {"shop_id":db.shop,"job_id":db.job,"media_asset_id":db.asset,
                        "image_sha256":digest,"object_path":real_path,
                        "object_bytes":len(original),"private":True,
                        "attempt":1,"review_status":"UNREVIEWED"}
            return prior_request(path,query=query,method=method,data=data)
        db.request=authoritative_request
        calls=[]
        class RealResponse:
            headers={"Content-Type":"image/png","Content-Length":str(len(original))}
            def __init__(self,url):self.url=url
            def __enter__(self):return self
            def __exit__(self,*_):return False
            def geturl(self):return self.url
            def getcode(self):return 200
            def read(self,max_bytes):return original[:max_bytes]
        def private_https(request,*,timeout):
            calls.append(request)
            self.assertEqual(timeout,15)
            self.assertEqual(request.get_method(),"GET")
            self.assertEqual(request.get_header("Apikey"),db.secret)
            self.assertIn(real_path,request.full_url)
            return RealResponse(request.full_url)
        inspected=build_verified_feature3_operator_reconciliation(
            admin_store=db,storage_transport=private_https).inspect(
                shop_id=db.shop,job_id=db.job)
        self.assertEqual(inspected["classification"],"TERMINAL_SUCCESS_EVIDENCE_OBSERVED")
        self.assertEqual(len(calls),1)
        self.assert_no_money_or_retry(inspected)
        self.assertEqual(len(db.calls),4)
        self.assertNotIn("object_path",inspected)

if __name__=="__main__":
    unittest.main()
