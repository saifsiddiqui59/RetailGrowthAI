"""Actual Feature3 HTTP transport allowlist wiring, no cloud or paid GPU.

The existing Feature3 unit tests mocked store.db.request; this module runs
TenantStore and AdminStore with real urllib.Request objects and a fake
in-memory HTTP transport to catch allowlist failures BEFORE any hosted use.
"""
from __future__ import annotations

import json
from pathlib import Path
import sys
import unittest
from uuid import uuid4

sys.path.insert(0, str(Path(__file__).resolve().parents[2] /
                       "azure-functions" / "campaign-api"))
from admin_store import AdminStore
from feature3_gpu_outbox_service import Feature3GPUOutboxService
from feature3_gpu_service import Feature3GPUServiceStore
from feature3_v2_api import Feature3V2API
from tenant_store import TenantStore

ORIGIN = "https://fictionalproject.supabase.co"
PUBLIC_KEY = "sb_publishable_OFFLINE_TEST_ONLY"
BACKEND_KEY = "sb_secret_OFFLINE_TEST_ONLY"


class Response:
    def __init__(self, data):
        self.data=json.dumps(data).encode("utf-8")
    def __enter__(self): return self
    def __exit__(self, *_): return False
    def read(self, *_): return self.data


class Feature3HTTPWireTests(unittest.TestCase):
    def setUp(self):
        self.shop,self.job,self.user,self.asset,self.token,self.source = [
            str(uuid4()) for _ in range(6)
        ]
        self.sha="a"*64
        self.key=f"{self.shop}/feature3/gpu/{self.job}/{self.sha}.png"
        self.requests=[]
        self.denied=False
        self.wrong_media=False

    def transport(self, request, *, timeout):
        self.requests.append(request)
        url=request.full_url
        auth=request.get_header("Authorization")
        apikey=request.get_header("Apikey")
        if "/rest/v1/shop_memberships?" in url:
            self.assertEqual(request.get_method(),"GET")
            self.assertEqual(auth,"Bearer signed-retailer-JWT")
            self.assertEqual(apikey,PUBLIC_KEY)
            self.assertIn("shop_id=eq."+self.shop,url)
            self.assertIn("user_id=eq."+self.user,url)
            data=[] if self.denied else [{"role":"OWNER"}]
        elif "/rest/v1/feature3_gpu_jobs?" in url:
            self.assertEqual(request.get_method(),"GET")
            self.assertEqual(auth,"Bearer signed-retailer-JWT")
            self.assertEqual(apikey,PUBLIC_KEY)
            self.assertIn("shop_id=eq."+self.shop,url)
            if "id=eq." in url:
                data=[{"id":self.job,"shop_id":self.shop,"status":"SUCCEEDED",
                       "output_asset_id":self.asset}]
            else:
                data=[{"id":self.job,"shop_id":self.shop,"status":"SUCCEEDED",
                       "created_at":"2026-10-29T00:00:00Z"}]
        elif "/rest/v1/media_assets?" in url:
            self.assertEqual(auth,"Bearer signed-retailer-JWT")
            self.assertIn("id=eq."+self.asset,url)
            data=[{"id":self.asset,
                   "shop_id":str(uuid4()) if self.wrong_media else self.shop,
                   "storage_bucket":"retailgrowth-media",
                   "object_path":self.key,"mime_type":"image/png",
                   "source":"GENERATED"}]
        elif "/storage/v1/object/sign/retailgrowth-media/" in url:
            self.assertEqual(request.get_method(),"POST")
            self.assertEqual(auth,"Bearer signed-retailer-JWT")
            self.assertEqual(apikey,PUBLIC_KEY)
            self.assertIn(self.key,url)
            self.assertEqual(json.loads(request.data),{"expiresIn":60})
            prefix="/object/sign/retailgrowth-media/"+self.key
            data={"signedURL":prefix+"?token=fixture"}
        elif "/rest/v1/rpc/feature3_commit_gpu_private_output" in url:
            self.assertEqual(request.get_method(),"POST")
            self.assertEqual(apikey,BACKEND_KEY)
            self.assertIsNone(auth)
            payload=json.loads(request.data)
            self.assertEqual(set(payload),{
                "p_shop_id","p_job_id","p_attempt","p_claim_token",
                "p_object_path","p_image_sha256","p_object_bytes",
                "p_source_asset_ids"})
            self.assertEqual(payload["p_source_asset_ids"],[self.source])
            data={"shop_id":self.shop,"job_id":self.job,
                  "claim_token":self.token,"attempt":1,
                  "media_asset_id":self.asset,"image_sha256":self.sha,
                  "object_path":self.key,"review_status":"UNREVIEWED",
                  "source":"GENERATED","private":True}
        elif "/rest/v1/rpc/feature3_claim_gpu_dispatch" in url:
            self.assertEqual(request.get_method(),"POST")
            self.assertEqual(apikey,BACKEND_KEY)
            self.assertIsNone(auth)
            self.assertEqual(json.loads(request.data),{"p_limit":1})
            data=[{"shop_id":self.shop,"job_id":self.job,
                   "dispatch_token":self.token,
                   "expires_in_seconds":120}]
        elif "/rest/v1/rpc/feature3_confirm_gpu_dispatch" in url:
            self.assertEqual(request.get_method(),"POST")
            self.assertEqual(apikey,BACKEND_KEY)
            self.assertIsNone(auth)
            self.assertEqual(json.loads(request.data),{
                "p_job_id":self.job,"p_dispatch_token":self.token,
                "p_sent":True})
            data=True
        elif "/rest/v1/rpc/feature3_audit_gpu_recovery" in url:
            self.assertEqual(request.get_method(),"POST")
            self.assertEqual(apikey,BACKEND_KEY)
            self.assertIsNone(auth)
            self.assertEqual(json.loads(request.data),{"p_limit":1})
            data=0
        else:
            raise AssertionError("Unexpected or unauthorized HTTP destination: "+url)
        return Response(data)

    def test_real_jwt_rls_gpu_history_and_signed_download_path(self):
        tenant=TenantStore(ORIGIN,PUBLIC_KEY,transport=self.transport)
        api=Feature3V2API(tenant,None)
        code,body=api.gpu_jobs("signed-retailer-JWT",self.user,self.shop)
        self.assertEqual(code,200)
        self.assertEqual(body["jobs"],[
            {"id":self.job,"shop_id":self.shop,"status":"SUCCEEDED"}])
        code,download=api.gpu_download(
            "signed-retailer-JWT",self.user,self.shop,self.job)
        self.assertEqual(code,200)
        self.assertEqual(download["media_asset_id"],self.asset)
        self.assertEqual(download["expires_in_seconds"],60)
        self.assertFalse(download["approved_model"])
        self.assertNotIn("object_path",download)
        self.assertEqual(
            [r.get_method() for r in self.requests],
            ["GET","GET","GET","GET","GET","POST"])
        self.assertTrue(all(r.get_header("Apikey")==PUBLIC_KEY for r in self.requests))

    def test_denied_role_or_foreign_generated_media_never_sign(self):
        tenant=TenantStore(ORIGIN,PUBLIC_KEY,transport=self.transport)
        api=Feature3V2API(tenant,None)
        self.denied=True
        self.assertEqual(
            api.gpu_download("signed-retailer-JWT",self.user,self.shop,self.job)[0],404)
        self.assertEqual(len(self.requests),1)
        self.denied=False
        self.wrong_media=True
        self.assertEqual(
            api.gpu_download("signed-retailer-JWT",self.user,self.shop,self.job)[0],404)
        self.assertFalse(any("/object/sign/" in r.full_url for r in self.requests))

    def test_user_jwt_gpu_table_is_get_only_and_no_rpc_routes(self):
        tenant=TenantStore(ORIGIN,PUBLIC_KEY,transport=self.transport)
        for method in ("POST","PATCH","DELETE","PUT"):
            with self.subTest(method=method),self.assertRaises(ValueError):
                tenant._request("feature3_gpu_jobs","signed-retailer-JWT",
                                method=method,data={"status":"SUCCEEDED"})
        for table in ("feature3_gpu_outbox","shop_ai_spend_reservations",
                      "rpc/feature3_finish_gpu_job"):
            with self.subTest(table=table),self.assertRaises(ValueError):
                tenant._request(table,"signed-retailer-JWT")
        self.assertEqual(self.requests,[])

    def test_actual_service_role_output_registration_rpc(self):
        service=Feature3GPUServiceStore(ORIGIN,BACKEND_KEY,transport=self.transport)
        result=service.commit_private_output(
            self.shop,self.job,1,self.token,self.key,self.sha,345,
            [self.source])
        self.assertEqual(result["media_asset_id"],self.asset)
        self.assertFalse("object_path" in result)
        self.assertEqual(result["review_status"],"UNREVIEWED")
        self.assertEqual(len(self.requests),1)

    def test_real_service_only_outbox_claim_confirm_and_recovery(self):
        service=Feature3GPUOutboxService(ORIGIN,BACKEND_KEY,
                                        transport=self.transport)
        rows=service.claim_dispatch(limit=1)
        self.assertEqual(rows,[{"shop_id":self.shop,"job_id":self.job,
                                "dispatch_token":self.token,
                                "expires_in_seconds":120,"gpu_started":False}])
        self.assertIs(service.confirm_dispatch(self.job,self.token,True),True)
        audit=service.audit_recovery(1)
        self.assertEqual(audit["events_recorded"],0)
        self.assertFalse(audit["paid_retry_authorized"])
        self.assertEqual([r.get_method() for r in self.requests],
                         ["POST","POST","POST"])
        self.assertTrue(all(r.get_header("Apikey")==BACKEND_KEY for r in self.requests))

    def test_privileged_rpcs_are_post_only_and_unknown_paths_denied(self):
        store=AdminStore(ORIGIN,BACKEND_KEY,transport=self.transport)
        for path in ("rpc/feature3_commit_gpu_private_output",
                     "rpc/feature3_claim_gpu_dispatch",
                     "rpc/feature3_confirm_gpu_dispatch",
                     "rpc/feature3_audit_gpu_recovery"):
            for method in ("GET","PATCH","DELETE"):
                with self.subTest(path=path,method=method),self.assertRaises(ValueError):
                    store.request(path,method=method)
        with self.assertRaises(ValueError):
            store.request("rpc/feature3_enable_gpu",method="POST",data={})
        self.assertEqual(self.requests,[])


if __name__=="__main__":
    unittest.main()
