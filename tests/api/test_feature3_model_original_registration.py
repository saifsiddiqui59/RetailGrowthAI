"""Signed model-library private original registration, source-only no GPU."""
import sys
from pathlib import Path
import unittest
from uuid import uuid4

sys.path.insert(0,str(Path(__file__).resolve().parents[2]/"azure-functions"/"campaign-api"))
from http_api import HTTPAPI
from feature3_v2_api import Feature3V2API
from feature3_v2_store import Feature3V2Store
from security import AuthenticationError


class ModelOriginalTests(unittest.TestCase):
    def setUp(self):
        self.shop,self.model,self.asset,self.user=[str(uuid4()) for _ in range(4)]
        self.role="OWNER";self.active=True
        self.request={"model_id":self.model,"image_sha256":"a"*64,
                      "license_name":"owned","license_url":None,
                      "attribution":"Fictional studio image only"}
        self.receipt={"shop_id":self.shop,"model_id":self.model,
                      "media_asset_id":self.asset,"image_sha256":"a"*64,
                      "registered":True,"byte_sha_verified":False,
                      "license_verified":False,
                      "status":"SOURCE_REGISTERED_PENDING_EVIDENCE",
                      "gpu_authorized":False}
        class Tenant:
            def __init__(self,outer): self.outer=outer
            def member(self,token,user,shop,write=False):
                o=self.outer
                return (token=="fictional-jwt" and user==o.user and
                    shop==o.shop and o.active and o.role in
                    (("OWNER","EDITOR") if write else ("OWNER","EDITOR","VIEWER")))
        self.tenant=Tenant(self)
        self.store=Feature3V2Store("https://example.supabase.co","sb_publishable_test")
        self.calls=[]
        def request(token,resource,*,query=None,body=None):
            self.calls.append((token,resource,body)); return self.receipt
        self.store._request=request
        self.on=Feature3V2API(self.tenant,self.store,model_review_enabled=True)
        self.off=Feature3V2API(self.tenant,self.store)
        def verifier(token):
            if token!="fictional-jwt":raise AuthenticationError("expired fixture session")
            return self.user
        self.verifier=verifier
        self.path=f"/shops/{self.shop}/feature3-model-originals/register"

    def call(self,body=None,path=None,method="POST",auth="Bearer fictional-jwt",api=None):
        return HTTPAPI(self.verifier,self.tenant,feature3_api=api or self.on).handle(
            method,path or self.path,auth,self.request if body is None else body)

    def test_only_signed_owner_editor_can_register_unverified_original(self):
        status,r=self.call()
        self.assertEqual(status,201)
        self.assertEqual(r["status"],"SOURCE_REGISTERED_PENDING_EVIDENCE")
        self.assertFalse(r["byte_sha_verified"])
        self.assertFalse(r["license_verified"])
        self.assertFalse(r["gpu_authorized"])
        self.assertEqual(self.calls[0][0],"fictional-jwt")
        self.assertEqual(self.calls[0][1],"rpc/feature3_register_model_original")
        self.assertNotIn("p_status",self.calls[0][2])
        self.assertNotIn("p_actor",self.calls[0][2])
        self.role="EDITOR";self.assertEqual(self.call()[0],201)

    def test_viewer_foreign_revoked_or_expired_denied(self):
        self.role="VIEWER";self.assertEqual(self.call()[0],404)
        self.role="OWNER";self.active=False;self.assertEqual(self.call()[0],404)
        self.active=True;self.assertEqual(self.call(path=self.path.replace(self.shop,str(uuid4())))[0],404)
        self.assertEqual(self.call(auth="Bearer expired")[0],401)
        self.assertEqual(self.call(api=self.off)[0],503)
        self.assertEqual(self.calls,[])

    def test_wrong_route_method_and_forged_fields_denied(self):
        for method in ("GET","DELETE","PUT"):
            self.assertEqual(self.call(method=method)[0],404)
        self.assertEqual(self.call(path=self.path+"/extra")[0],404)
        for change in ({"status":"APPROVED"},{"rights_verified":True},
                       {"object_path":"https://foreign.test/secret.png"},
                       {"gpu_authorized":True}):
            self.assertEqual(self.call(body={**self.request,**change})[0],400)
        self.assertEqual(self.calls,[])

    def test_bad_sha_license_and_identity_denied(self):
        for change in ({"image_sha256":"a"*63},
                       {"license_name":"unverified"},
                       {"license_name":"CC-BY-4.0","license_url":None},
                       {"model_id":self.model.upper()},
                       {"attribution":"x"},
                       {"attribution":"unsafe\nnotes"}):
            with self.subTest(change=change):
                self.assertEqual(self.call(body={**self.request,**change})[0],400)
        self.assertEqual(self.calls,[])

    def test_uncertain_output_does_not_retry_or_infer_rights(self):
        self.receipt=None
        self.assertEqual(self.call()[0],409)
        self.assertEqual(len(self.calls),1)
        self.calls.clear()
        self.receipt={**self.receipt} if self.receipt else {
           "shop_id":self.shop,"model_id":self.model,
           "media_asset_id":self.asset,"image_sha256":"a"*64,
           "registered":True,"byte_sha_verified":False,"license_verified":True,
           "status":"SOURCE_REGISTERED_PENDING_EVIDENCE","gpu_authorized":False}
        self.assertEqual(self.call(),(503,{"error":"SERVICE_UNAVAILABLE"}))
        self.assertEqual(len(self.calls),1)

    def test_user_cannot_pass_service_key_to_store(self):
        with self.assertRaises(ValueError):
            self.store.register_model_original("sb_secret_bad",self.shop,self.request)
        self.assertEqual(self.calls,[])


if __name__=="__main__":
    unittest.main()
