"""Feature3 Task3.5: zero-GPU JWT/RLS signed output boundary negative tests."""
from pathlib import Path
import sys
import unittest
from uuid import uuid4

sys.path.insert(0,str(Path(__file__).resolve().parents[2]/"azure-functions/campaign-api"))
from feature3_v2_api import Feature3V2API
from tenant_store import TenantStore

S,J,A,U,OTHER=[str(uuid4()) for _ in range(5)]
SHA="a"*64
PATH=f"{S}/feature3/gpu/{J}/{SHA}.png"

class FakeTenant:
    def __init__(self):
        self.active=True
        self.job={"id":J,"shop_id":S,"status":"SUCCEEDED","output_asset_id":A}
        self.asset={"object_path":PATH,"mime_type":"image/png"}
        self.sign_calls=[]
    def member(self, token,user_id,shop_id,write=False):
        return self.active and shop_id==S
    def feature3_gpu_job(self,token,shop_id,job_id):
        return self.job
    def feature3_generated_asset(self,token,shop_id,job_id,asset_id):
        return self.asset
    def sign_download(self,token,shop_id,path):
        self.sign_calls.append((token,shop_id,path))
        return "https://private.invalid/signed?token=test"

class OutputTests(unittest.TestCase):
    def test_exact_tenant_success_returns_short_lived_private_link_no_approval(self):
        t=FakeTenant()
        code,body=Feature3V2API(t,None).gpu_download("signed-jwt",U,S,J)
        self.assertEqual(code,200)
        self.assertEqual(body["media_asset_id"],A)
        self.assertEqual(body["expires_in_seconds"],60)
        self.assertFalse(body["approved_model"])
        self.assertEqual(t.sign_calls,[("signed-jwt",S,PATH)])
        self.assertNotIn("object_path",body)
    def test_revoked_foreign_missing_job_and_unready_never_sign(self):
        t=FakeTenant()
        t.active=False
        self.assertEqual(Feature3V2API(t,None).gpu_download("jwt",U,S,J)[0],404)
        t.active=True
        t.job=None
        self.assertEqual(Feature3V2API(t,None).gpu_download("jwt",U,S,J)[0],404)
        t.job={"id":J,"shop_id":S,"status":"RUNNING","output_asset_id":None}
        self.assertEqual(Feature3V2API(t,None).gpu_download("jwt",U,S,J)[0],409)
        t.job={"id":J,"shop_id":S,"status":"SUCCEEDED","output_asset_id":A}
        t.asset=None
        self.assertEqual(Feature3V2API(t,None).gpu_download("jwt",U,S,J)[0],404)
        self.assertEqual(t.sign_calls,[])
    def test_registered_asset_must_match_job_shop_and_content_address(self):
        t=object.__new__(TenantStore)
        good={"id":A,"shop_id":S,"source":"GENERATED",
              "storage_bucket":"retailgrowth-media","mime_type":"image/png",
              "object_path":PATH}
        t._request=lambda *args,**kwargs:[good]
        self.assertEqual(t.feature3_generated_asset("jwt",S,J,A)["object_path"],PATH)
        for invalid in [
            {"shop_id":OTHER},{"source":"UPLOAD"},{"mime_type":"text/plain"},
            {"object_path":f"{OTHER}/feature3/gpu/{J}/{SHA}.png"},
            {"object_path":f"{S}/feature3/gpu/{uuid4()}/{SHA}.png"},
            {"object_path":f"{S}/feature3/gpu/{J}/preview.png"},
            {"storage_bucket":"public"}]:
            t._request=lambda *args,invalid=invalid,**kwargs:[{**good,**invalid}]
            self.assertIsNone(t.feature3_generated_asset("jwt",S,J,A))
    def test_duplicate_or_foreign_job_rows_denied(self):
        t=object.__new__(TenantStore)
        row={"id":J,"shop_id":S,"status":"SUCCEEDED","output_asset_id":A}
        t._request=lambda *args,**kwargs:[{**row,"shop_id":OTHER}]
        self.assertIsNone(t.feature3_gpu_job("jwt",S,J))
        t._request=lambda *args,**kwargs:[row,row]
        self.assertIsNone(t.feature3_gpu_job("jwt",S,J))

if __name__=="__main__":unittest.main()
