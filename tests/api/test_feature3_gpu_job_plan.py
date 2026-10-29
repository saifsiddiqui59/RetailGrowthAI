"""Feature3 read-only actual job/design/media rights planning, zero GPU.

Synthetic source-proofs are trusted TEST DOUBLE ONLY and explicitly do not
authorize spending. The production source-proof must independently verify
real private source bytes, legal evidence, human approval and current grants.
"""
import copy
from hashlib import sha256
from io import BytesIO
from PIL import Image
from datetime import datetime, timedelta, timezone
from pathlib import Path
import sys
import unittest
from unittest.mock import patch
from uuid import uuid4

sys.path.insert(0,str(Path(__file__).resolve().parents[2]/"azure-functions/campaign-api"))
from feature3_gpu_job_plan import (Feature3GPUJobPlanPreflight, Feature3PlanDenied,
    make_claimed_gpu_off_rights_callback)
from feature3_private_source_proof import Feature3TrustedPrivateSourceProof
from admin_store import AdminStore


class FakeCurrentDB:
    def __init__(self):
        self.shop,self.job,self.actor,self.design,self.media,self.model=(
            str(uuid4()) for _ in range(6))
        self.sha="a"*64
        self.start=(datetime.now(timezone.utc)-timedelta(days=3)).isoformat()
        self.end=(datetime.now(timezone.utc)+timedelta(days=3)).isoformat()
        self.job_row={"id":self.job,"shop_id":self.shop,
            "requested_by":self.actor,"design_id":self.design,
            "design_revision":1,"design_server_sha256":self.sha,
            "status":"QUEUED","attempts":0,"claim_token":None,
            "output_asset_id":None}
        self.member_row={"shop_id":self.shop,"user_id":self.actor,
                         "role":"EDITOR","active":True}
        self.sub_row={"shop_id":self.shop,"status":"ACTIVE",
                      "valid_from":self.start,"valid_until":self.end,
                      "period_start":self.start,"period_end":self.end}
        self.design_row={"id":self.design,"shop_id":self.shop,
            "revision":1,"status":"DRAFT","server_document_sha256":self.sha,
            "design":{"schema":"retailgrowth.poster.v2",
                      "shop_id":self.shop,
                      "format":"portrait","template":"fashion",
                      "background":"#FFFFFF",
                      "layers":[{"type":"image","asset_id":self.media,"id":"image1"}]}}
        self.asset_row={"id":self.media,"shop_id":self.shop,
                        "storage_bucket":"retailgrowth-media",
                        "object_path":f"{self.shop}/model-library/{self.model}/{self.sha}.png",
                        "mime_type":"image/png","source":"UPLOAD",
                        "license_name":"owned","license_url":None,
                        "attribution":"Synthetic model image, reviewed."}
        self.model_row={"owner_shop_id":self.shop,"model_id":self.model,
                        "media_asset_id":self.media,"status":"APPROVED",
                        "rights_verified":True,"synthetic_adult":True,
                        "approved_uses":["poster","try_on"],
                        "rights_revision":2,"image_sha256":self.sha}
        self.calls=[]
        self.changed_after_proof=False
        self.proofs=0
        self.proof_ok=True
        self.revoke_second_proof=False

    def request(self,table,*,query=None,data=None,method="GET"):
        self.calls.append((table,copy.deepcopy(query),method))
        if method!="GET" or data is not None:
            raise AssertionError("No paid SQL mutation/claim permitted")
        if table=="feature3_gpu_jobs":result=self.job_row
        elif table=="shop_memberships":result=self.member_row
        elif table=="shop_subscriptions":result=self.sub_row
        elif table=="feature3_poster_designs":result=self.design_row
        elif table=="media_assets":result=self.asset_row
        elif table=="feature3_models":result=self.model_row
        else:raise AssertionError("Unexpected service-only read: "+table)
        if table in ("feature3_models","media_assets"):
            return [copy.deepcopy(result)]
        return [copy.deepcopy(result)]

    def proof(self,shop,media):
        self.proofs+=1
        if shop!=self.shop or media!=self.asset_row:
            raise AssertionError("Source proof received untrusted media")
        if self.changed_after_proof:
            self.member_row["active"]=False
        allowed=self.proof_ok and not (self.revoke_second_proof and self.proofs>=2)
        return {"shop_id":shop,"asset_id":media["id"],
                "image_sha256":self.sha,"rights_revision":2,
                "private_bytes_verified":allowed,
                "independent_license_verified":allowed,
                "current_customer_approval":allowed,
                "rights_revoked":not allowed}


class CurrentGPUPlanTests(unittest.TestCase):
    def setUp(self):
        self.db=FakeCurrentDB()
        self.preflight=Feature3GPUJobPlanPreflight(
            admin_store=self.db,source_proof=self.db.proof)

    def run_plan(self):
        return self.preflight.check(self.db.shop,self.db.job)

    def test_actual_store_job_design_media_member_and_approval_reads(self):
        result=self.run_plan()
        self.assertTrue(result["preflight_verified"])
        self.assertEqual(result["source_asset_ids"],(self.db.media,))
        self.assertEqual(result["source_sha256s"],(self.db.sha,))
        self.assertEqual(result["rights_revisions"],(2,))
        self.assertFalse(result["provider_call_permitted"])
        self.assertFalse(result["claim_performed"])
        self.assertFalse(result["paid_retry_authorized"])
        self.assertFalse(result["gpu_started"])
        self.assertFalse(any("object" in k or "token" in k for k in result))
        self.assertEqual(self.db.proofs,2)
        # Exactly 6 persisted read paths, twice; no submit, fee or claim.
        self.assertEqual(len(self.db.calls),12)
        self.assertEqual(set(x[0] for x in self.db.calls),
            {"feature3_gpu_jobs","feature3_poster_designs","shop_memberships",
             "shop_subscriptions","media_assets","feature3_models"})
        self.assertTrue(all(x[2]=="GET" for x in self.db.calls))

    def test_bad_foreign_or_changed_claim_status_denied_before_source(self):
        for change,value in (
            ("shop_id",str(uuid4())),("status","RUNNING"),
            ("status","SUCCEEDED"),("attempts",1),
            ("claim_token",str(uuid4())),("output_asset_id",str(uuid4())),
            ("design_server_sha256","Z"*64)):
            self.setUp()
            self.db.job_row[change]=value
            with self.subTest(key=change,value=value),self.assertRaises(Feature3PlanDenied):
                self.run_plan()
            self.assertEqual(self.db.proofs,0)

    def test_source_media_and_shop_subscription_denials(self):
        edits=(
            ("member_row","role","VIEWER"),
            ("member_row","active",False),
            ("sub_row","status","EXPIRED"),
            ("sub_row","valid_until","2020-01-01T00:00:00Z"),
            ("design_row","revision",2),
            ("design_row","status","APPROVED"),
            ("asset_row","shop_id",str(uuid4())),
            ("asset_row","storage_bucket","public"),
            ("asset_row","object_path","https://evil.test/private.png"),
            ("asset_row","source","STOCK"),
            ("asset_row","mime_type","text/html"),
            ("asset_row","attribution",""),
            ("model_row","status","REVOKED"),
            ("model_row","rights_verified",False),
            ("model_row","synthetic_adult",False),
            ("model_row","approved_uses",["video_reference"]),
            ("model_row","rights_revision",1),
        )
        for field,key,value in edits:
            self.setUp()
            getattr(self.db,field)[key]=value
            with self.subTest(field=field,key=key),self.assertRaises(Feature3PlanDenied):
                self.run_plan()
            self.assertEqual(self.db.proofs,0)

    def test_expired_or_wrong_design_source_rejected(self):
        self.db.design_row["design"]["layers"]=[{"type":"text","text":"No source"}]
        with self.assertRaisesRegex(Feature3PlanDenied,"No bounded"):
            self.run_plan()
        self.db.design_row["design"]["layers"]=[
            {"type":"image","asset_id":str(uuid4())}]
        with self.assertRaises(Feature3PlanDenied):
            self.run_plan()

    def test_disallow_fake_claim_of_private_license_approval(self):
        self.db.proof_ok=False
        with self.assertRaises(Feature3PlanDenied):
            self.run_plan()
        self.assertEqual(self.db.proofs,1)

    def test_legal_rights_revoked_after_stable_sql_rows_deny(self):
        self.db.revoke_second_proof=True
        with self.assertRaisesRegex(Feature3PlanDenied,"changed after DB read"):
            self.run_plan()
        self.assertEqual(self.db.proofs,2)
        self.assertEqual(len(self.db.calls),12)

    def test_revocation_mid_proof_denies_changed_authority_snapshot(self):
        self.db.changed_after_proof=True
        with self.assertRaises(Feature3PlanDenied):
            self.run_plan()
        self.assertEqual(self.db.proofs,1)
        self.assertEqual(len(self.db.calls),8)

    def test_forbidden_implicit_source_recognition_not_production_proof(self):
        self.db.model_row["image_sha256"]="b"*64
        with self.assertRaises(Feature3PlanDenied):
            self.run_plan()
        self.assertEqual(self.db.proofs,1)

    def test_only_read_access_for_new_gpu_preflight_tables(self):
        class NoTransport:
            def __call__(self,request,*,timeout):
                raise AssertionError("Unapproved service-role mutation reached HTTP")
        svc=AdminStore("https://fixture.supabase.co",
                       "sb_secret_FAKE_LOCAL_TEST_ONLY",transport=NoTransport())
        read_only=("feature3_gpu_jobs","shop_ai_spend_reservations",
                   "feature3_poster_designs","feature3_models",
                   "shop_subscriptions")
        for table in read_only:
            for method in ("POST","PATCH","PUT","DELETE"):
                with self.subTest(table=table,method=method),self.assertRaises(ValueError):
                    svc.request(table,method=method,data={"status":"APPROVED"})
        with self.assertRaises(ValueError):
            svc.request("feature3_enable_gpu",method="POST",data={})



    def make_claimed(self):
        self.token=str(uuid4())
        self.db.job_row.update({"status":"RUNNING","attempts":1,
                               "claim_token":self.token,
                               "lease_until":(datetime.now(timezone.utc)+
                                   timedelta(minutes=15)).isoformat()})
        self.lease_reads=[]
        self.fail_second_lease=False
        def lease(shop,job,attempt,token):
            self.lease_reads.append((shop,job,attempt,token))
            if self.fail_second_lease and len(self.lease_reads)>=2:
                raise OSError("Lease expired or financial state changed")
            return {"shop_id":self.db.shop,"job_id":self.db.job,
                    "attempt":1,"claim_token":self.token,
                    "reservation_id":self.db.actor,"reserved_usd":"0.050000"}
        return lease

    def test_claimed_worker_uses_existing_one_shot_lease_and_rechecks_rights(self):
        lease=self.make_claimed()
        result=self.preflight.check_claimed(
            self.db.shop,self.db.job,self.token,(self.db.media,),lease)
        self.assertTrue(result["claim_observed"])
        self.assertTrue(result["current_lease_verified"])
        self.assertFalse(result["provider_call_permitted"])
        self.assertFalse(result["gpu_started"])
        self.assertFalse(result["paid_retry_authorized"])
        self.assertFalse(result["claim_performed"])
        self.assertEqual(result["source_sha256s"],(self.db.sha,))
        self.assertEqual(self.db.proofs,2)
        self.assertEqual(len(self.db.calls),12)
        self.assertEqual(len(self.lease_reads),2)
        class Service:
            read_prepaid_reservation=staticmethod(lease)
        callback=make_claimed_gpu_off_rights_callback(
            plan_reader=self.preflight,service=Service())
        self.assertTrue(callback(self.db.shop,self.db.job,self.token,(self.db.media,)))
        self.assertEqual(len(self.lease_reads),4)

    def test_claimed_sources_lease_or_approvals_change_fail_closed(self):
        for bad in ("wrong_token","wrong_source","duplicate_source",
                    "source_revoked","lease_lost","job_requeued",
                    "viewer","expired"):
            self.setUp()
            lease=self.make_claimed()
            args=[self.db.shop,self.db.job,self.token,(self.db.media,),lease]
            if bad=="wrong_token":args[2]=str(uuid4())
            if bad=="wrong_source":args[3]=(str(uuid4()),)
            if bad=="duplicate_source":args[3]=(self.db.media,self.db.media)
            if bad=="source_revoked":self.db.revoke_second_proof=True
            if bad=="lease_lost":self.fail_second_lease=True
            if bad=="job_requeued":self.db.job_row["status"]="QUEUED"
            if bad=="viewer":self.db.member_row["role"]="VIEWER"
            if bad=="expired":self.db.sub_row["valid_until"]="2020-01-01T00:00:00Z"
            with self.subTest(bad=bad),self.assertRaises(Feature3PlanDenied):
                self.preflight.check_claimed(*args)
            self.assertFalse(any(x[2]!="GET" for x in self.db.calls))

    def test_claimed_lease_must_be_live_timezone_aware_before_private_byte_proof(self):
        now=datetime.now(timezone.utc)
        invalid=(
            (now-timedelta(seconds=5)).isoformat(),
            "2020-01-01T00:00:00Z",
            now.replace(tzinfo=None).isoformat(),
            "yesterday",
            "",
        )
        for expires in invalid:
            self.setUp()
            lease=self.make_claimed()
            self.db.job_row["lease_until"]=expires
            with self.subTest(expires=expires),self.assertRaises(Feature3PlanDenied):
                self.preflight.check_claimed(
                    self.db.shop,self.db.job,self.token,(self.db.media,),lease)
            self.assertEqual(self.db.proofs,0)
            self.assertEqual(len(self.lease_reads),1)
            self.assertTrue(all(method=="GET" for _,__,method in self.db.calls))

    def test_claimed_lease_expiring_during_private_rights_read_denies(self):
        lease=self.make_claimed()
        original=self.db.proof
        def expired_during_source(shop,media):
            result=original(shop,media)
            self.db.job_row["lease_until"]=(
                datetime.now(timezone.utc)-timedelta(seconds=1)).isoformat()
            return result
        self.preflight=Feature3GPUJobPlanPreflight(
            admin_store=self.db,source_proof=expired_during_source)
        with self.assertRaises(Feature3PlanDenied):
            self.preflight.check_claimed(
                self.db.shop,self.db.job,self.token,(self.db.media,),lease)
        self.assertEqual(self.db.proofs,1)
        self.assertEqual(len(self.lease_reads),1)

    def test_claimed_lease_expiring_after_final_rights_proof_denies(self):
        lease=self.make_claimed()
        original=self.db.proof
        clock={"later":False}
        # Model the real deadline passing without modifying SQL. The job
        # row's immutable lease_until stays constant as time advances.
        class VirtualClock(datetime):
            @classmethod
            def now(cls,tz=None):
                return datetime.now(tz)+(timedelta(minutes=30)
                                          if clock["later"] else timedelta())
        def slow_last_proof(shop,media):
            result=original(shop,media)
            if self.db.proofs==2:
                clock["later"]=True
            return result
        self.preflight=Feature3GPUJobPlanPreflight(
            admin_store=self.db,source_proof=slow_last_proof)
        with patch("feature3_gpu_job_plan.datetime",VirtualClock):
            with self.assertRaisesRegex(Feature3PlanDenied,
                                        "expired during final rights"):
                self.preflight.check_claimed(
                    self.db.shop,self.db.job,self.token,(self.db.media,),lease)
        self.assertEqual(self.db.proofs,2)
        self.assertEqual(len(self.lease_reads),1)
        self.assertTrue(all(method=="GET" for _,__,method in self.db.calls))

    def test_claimed_real_private_png_storage_and_twice_current_legal_review(self):
        lease=self.make_claimed()
        raw=BytesIO()
        Image.new("RGB",(320,400),"#506f80").save(raw,format="PNG")
        original=raw.getvalue()
        digest=sha256(original).hexdigest()
        self.db.sha=digest
        self.db.asset_row["object_path"]=(
            f"{self.db.shop}/model-library/{self.db.model}/{digest}.png")
        self.db.model_row["image_sha256"]=digest
        self.review_reads=[]
        class Response(BytesIO):
            def __init__(self,url):
                super().__init__(original)
                self.url=url
                self.headers={"Content-Type":"image/png",
                              "Content-Length":str(len(original))}
            def geturl(self):return self.url
            def getcode(self):return 200
        def private_transport(request,*,timeout):
            self.assertEqual(request.get_method(),"GET")
            self.assertEqual(timeout,15)
            self.assertEqual(request.get_header("Apikey"),"sb_secret_"+"r"*40)
            return Response(request.full_url)
        def review(shop,asset,image_sha,row):
            self.review_reads.append(image_sha)
            self.assertEqual(row,self.db.asset_row)
            return {"shop_id":shop,"asset_id":asset,"image_sha256":digest,
                    "rights_revision":2,"independent_license_verified":True,
                    "current_customer_approval":True,"rights_revoked":False}
        proof=Feature3TrustedPrivateSourceProof(
            origin="https://fixture.supabase.co",
            backend_secret="sb_secret_"+"r"*40,
            review_authority=review,transport=private_transport)
        planner=Feature3GPUJobPlanPreflight(admin_store=self.db,source_proof=proof)
        receipt=planner.check_claimed(
            self.db.shop,self.db.job,self.token,(self.db.media,),lease)
        self.assertEqual(receipt["source_sha256s"],(digest,))
        self.assertEqual(len(self.review_reads),4)
        self.assertEqual(len(self.lease_reads),2)
        self.assertFalse(receipt["provider_call_permitted"])

if __name__=="__main__":
    unittest.main()
