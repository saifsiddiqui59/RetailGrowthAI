"""GPU-OFF model review authority: real PostgREST Request contract, fake rows.

This does not establish commercial licence authenticity or create a deployed
RPC. Source proof is DENIED unless a trusted service returns exact current
review data; product photos without model review remain blocked.
"""
import json
import sys
from pathlib import Path
import unittest
from uuid import uuid4

sys.path.insert(0,str(Path(__file__).resolve().parents[2]/"azure-functions/campaign-api"))
from admin_store import AdminStore
from feature3_model_review_authority import (
    Feature3ApprovedModelReviewAuthority, Feature3ModelReviewDenied,
    build_approved_model_gpu_off_preflight,
)


class JSONResponse:
    def __init__(self,payload):
        self.data=json.dumps(payload).encode("utf-8")
    def __enter__(self):return self
    def __exit__(self,*_):return False
    def read(self):return self.data


class ReviewTests(unittest.TestCase):
    def setUp(self):
        self.shop,self.asset,self.other=(str(uuid4()) for _ in range(3))
        self.sha="f"*64
        self.media={"id":self.asset,"shop_id":self.shop,
                    "storage_bucket":"retailgrowth-media",
                    "mime_type":"image/png"}
        self.receipt={
            "shop_id":self.shop,"asset_id":self.asset,
            "image_sha256":self.sha,"rights_revision":2,
            "independent_license_verified":True,
            "current_customer_approval":True,"rights_revoked":False,
        }
        self.calls=[]
        self.fail=False
        self.admin=AdminStore(
            "https://fixture.supabase.co", "sb_secret_TEST_PRIVATE_ROLE_ABC",
            transport=self.transport)
        self.authority=Feature3ApprovedModelReviewAuthority(admin_store=self.admin)

    def transport(self,request,*,timeout):
        self.calls.append(request)
        self.assertEqual(timeout,10)
        self.assertEqual(request.get_method(),"POST")
        self.assertEqual(request.full_url,
            "https://fixture.supabase.co/rest/v1/rpc/feature3_read_current_model_review")
        self.assertEqual(request.get_header("Apikey"),"sb_secret_TEST_PRIVATE_ROLE_ABC")
        self.assertIsNone(request.get_header("Authorization"))
        self.assertEqual(json.loads(request.data),{
            "p_shop_id":self.shop,"p_media_asset_id":self.asset,
            "p_image_sha256":self.sha,
        })
        return JSONResponse(None if self.fail else self.receipt)

    def verify(self):
        return self.authority(self.shop,self.asset,self.sha,self.media)

    def test_exact_independently_verified_service_only_current_receipt(self):
        self.assertEqual(self.verify(),self.receipt)
        self.assertEqual(len(self.calls),1)
        self.assertFalse(any(k in self.receipt for k in
            ("url","storage_path","reviewer_key","provider_call_permitted")))
        self.assertEqual(self.verify(),self.receipt)
        self.assertEqual(len(self.calls),2)

    def test_non_model_or_missing_rights_does_not_fake_approval(self):
        self.fail=True
        with self.assertRaises(Feature3ModelReviewDenied):self.verify()
        self.assertEqual(len(self.calls),1)

    def test_foreign_mismatched_or_revoked_review_receipt_denied(self):
        bad=[{"shop_id":self.other},{"asset_id":self.other},
             {"image_sha256":"a"*64},{"rights_revision":1},
             {"rights_revision":True},{"rights_revision":3.5},
             {"independent_license_verified":False},
             {"current_customer_approval":False},
             {"rights_revoked":True},{"reviewer":"browser"},
             {"source":"user-post"}]
        for fragment in bad:
            self.receipt={**{
                "shop_id":self.shop,"asset_id":self.asset,
                "image_sha256":self.sha,"rights_revision":2,
                "independent_license_verified":True,
                "current_customer_approval":True,"rights_revoked":False,
            },**fragment}
            with self.subTest(fragment=fragment), self.assertRaises(
                Feature3ModelReviewDenied):
                self.verify()

    def test_invalid_media_or_source_identity_rejected_before_rpc(self):
        invalid=[
            ("",self.asset,self.sha,self.media),
            (self.shop,"forged-id",self.sha,self.media),
            (self.shop,self.asset,"bad-sha",self.media),
            (self.shop,self.asset,self.sha,{**self.media,"shop_id":self.other}),
            (self.shop,self.asset,self.sha,{**self.media,"mime_type":"image/jpeg"}),
            (self.shop,self.asset,self.sha,{**self.media,"storage_bucket":"public"}),
        ]
        for args in invalid:
            with self.subTest(args=args[:3]), self.assertRaises(
                Feature3ModelReviewDenied):
                self.authority(*args)
        self.assertEqual(self.calls,[])

    def test_no_generic_get_and_no_unsupported_service_role_path(self):
        for method in ("GET","PATCH","DELETE"):
            with self.subTest(method=method),self.assertRaises(ValueError):
                self.admin.request("rpc/feature3_read_current_model_review",
                                   method=method)
        with self.assertRaises(ValueError):
            self.admin.request("rpc/feature3_override_current_model_review",
                               method="POST",data={})
        self.assertEqual(self.calls,[])

    def test_preflight_factory_reuses_existing_real_private_byte_reader(self):
        plan=build_approved_model_gpu_off_preflight(
            admin_store=self.admin,origin="https://fixture.supabase.co",
            backend_secret="sb_secret_TEST_PRIVATE_ROLE_ABC",
            transport=self.transport)
        self.assertIsInstance(plan.proof.review,Feature3ApprovedModelReviewAuthority)
        self.assertIs(plan.proof.review.db,self.admin)
        self.assertEqual(self.calls,[])


if __name__=="__main__":
    unittest.main()
