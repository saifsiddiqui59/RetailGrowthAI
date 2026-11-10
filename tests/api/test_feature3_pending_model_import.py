"""Feature3 pending model import: signed JWT route and strict SQL receipt.

Fictional shops/PNG SHA and empty provider. Does not upload, approve or
generate a media asset. No live customer image, GPU or hosted SQL.
"""
from pathlib import Path
from uuid import uuid4
import sys
import unittest

sys.path.insert(0,str(Path(__file__).resolve().parents[2]/"azure-functions"/"campaign-api"))
from http_api import HTTPAPI
from feature3_v2_api import Feature3V2API
from feature3_v2_store import Feature3V2Store
from security import AuthenticationError
from tenant_store import StorageUnavailable


class FakeTenant:
    def __init__(self, shop):
        self.shop=shop
        self.role="OWNER"
        self.active=True
    def member(self,token,uid,shop,write=False):
        return (token=="fictional-jwt" and shop==self.shop and self.active
                and self.role in (("OWNER","EDITOR") if write else
                                  ("OWNER","EDITOR","VIEWER")))


class ImportTests(unittest.TestCase):
    def setUp(self):
        self.shop,self.model,self.media,self.user=[str(uuid4()) for _ in range(4)]
        self.body={"model_id":self.model,"media_asset_id":self.media,
                   "source_kind":"retailer_licensed","label":"Original adult photo",
                   "image_sha256":"a"*64,"license_id":"REVIEWED-COMMERCIAL",
                   "license_evidence_sha256":"b"*64,
                   "attribution":"Original fictional studio asset",
                   "approved_uses":["poster","try_on","video_reference"]}
        self.tenant=FakeTenant(self.shop)
        self.store=Feature3V2Store("https://fake.supabase.co","sb_publishable_OFFLINE_TEST")
        self.calls=[]
        self.receipt={"shop_id":self.shop,"model_id":self.model,"media_asset_id":self.media,
                      "status":"PENDING_REVIEW","rights_revision":1,"rights_verified":False,
                      "evidence_verified":False,"gpu_authorized":False,"registered":True}
        def request(token,resource,*,query=None,body=None):
            self.calls.append((token,resource,body))
            return self.receipt
        self.store._request=request
        self.off=Feature3V2API(self.tenant,self.store)
        self.on=Feature3V2API(self.tenant,self.store,model_review_enabled=True)
        def verify(token):
            if token!="fictional-jwt":
                raise AuthenticationError("Invalid synthetic token")
            return self.user
        self.verify=verify
        self.path=f"/shops/{self.shop}/feature3-models/import"
    def call(self,body=None,method="POST",api=None,auth="Bearer fictional-jwt",path=None):
        return HTTPAPI(self.verify,self.tenant,feature3_api=api or self.on).handle(
            method,path or self.path,auth,self.body if body is None else body)

    def test_signed_owner_pending_only_and_no_gpu_or_approval(self):
        status,response=self.call()
        self.assertEqual(status,201)
        self.assertEqual(response["status"],"PENDING_REVIEW")
        self.assertFalse(response["rights_verified"])
        self.assertFalse(response["evidence_verified"])
        self.assertFalse(response["gpu_authorized"])
        self.assertFalse(response["generation_executed"])
        self.assertEqual(self.calls[0][0],"fictional-jwt")
        self.assertEqual(self.calls[0][1],"rpc/feature3_import_pending_model")
        payload=self.calls[0][2]
        self.assertEqual(payload["p_shop_id"],self.shop)
        self.assertEqual(payload["p_model_id"],self.model)
        self.assertEqual(payload["p_media_asset_id"],self.media)
        self.assertEqual(payload["p_approved_uses"],self.body["approved_uses"])
        self.assertNotIn("p_actor",payload)
        self.assertNotIn("p_status",payload)
        self.assertNotIn("rights_verified",payload)

    def test_independent_flag_disabled_and_JWT_rejected(self):
        self.assertEqual(self.call(api=self.off)[0],503)
        for token in ("","Bearer expired","Basic fictional-jwt"):
            self.assertEqual(self.call(auth=token)[0],401)
        self.assertEqual(self.calls,[])

    def test_current_active_editor_allowed_but_viewer_foreign_disabled(self):
        self.tenant.role="EDITOR"
        self.assertEqual(self.call()[0],201)
        self.calls.clear()
        for role in ("VIEWER","DISABLED"):
            self.tenant.role=role
            with self.subTest(role=role):
                self.assertEqual(self.call()[0],404)
        self.tenant.role="OWNER"
        self.tenant.active=False
        self.assertEqual(self.call()[0],404)
        self.tenant.active=True
        self.assertEqual(self.call(path=self.path.replace(self.shop,str(uuid4())))[0],404)
        self.assertEqual(self.calls,[])

    def test_only_POST_exact_path_and_exact_user_proposal(self):
        for method in ("GET","PATCH","DELETE"):
            self.assertEqual(self.call(method=method)[0],404)
        self.assertEqual(self.call(path=self.path+"/extra")[0],404)
        self.assertEqual(self.call(body={**self.body,"status":"APPROVED"})[0],400)
        self.assertEqual(self.call(body={**self.body,"rights_verified":True})[0],400)
        self.assertEqual(self.call(body={**self.body,"gpu":True})[0],400)
        self.assertEqual(self.call(body={**self.body,"scope":"platform"})[0],400)
        self.assertEqual(self.calls,[])

    def test_invalid_source_and_forged_parameters_never_hit_DB(self):
        changes=[
          {"image_sha256":"invalid"},{"license_evidence_sha256":"b"*63},
          {"approved_uses":["poster","poster"]},{"approved_uses":["publish"]},
          {"label":"\nmalformed"},{"label":""},
          {"model_id":str(uuid4()).upper()},{"attribution":"control\nline"},
          {"license_id":"unlicensed"},
          {"license_id":"CC-BY-4.0","attribution":""},
          {"approved_uses":[True]},
        ]
        for change in changes:
            with self.subTest(change=change):
                self.assertEqual(self.call(body={**self.body,**change})[0],400)
        self.assertEqual(self.calls,[])

    def test_refused_or_forged_or_stale_receipt_never_returns_success(self):
        self.receipt=None
        self.assertEqual(self.call()[0],409)
        self.assertEqual(len(self.calls),1)
        base={"shop_id":self.shop,"model_id":self.model,"media_asset_id":self.media,
              "status":"PENDING_REVIEW","rights_revision":1,"rights_verified":False,
              "evidence_verified":False,"gpu_authorized":False,"registered":True}
        for k,v in (("shop_id",str(uuid4())),("status","APPROVED"),
                    ("rights_revision",2),("gpu_authorized",True),
                    ("evidence_verified",True),("registered",False)):
            self.receipt={**base,k:v}
            with self.subTest(k=k):
                self.assertEqual(self.call(), (503, {"error": "SERVICE_UNAVAILABLE"}))
        self.assertEqual(len(self.calls),7)

    def test_service_role_rejected_as_user_bearer(self):
        with self.assertRaises(ValueError):
            self.store.import_pending_model("sb_secret_not_a_user",self.shop,self.body)
        self.assertEqual(self.calls,[])


if __name__=="__main__":
    unittest.main()
