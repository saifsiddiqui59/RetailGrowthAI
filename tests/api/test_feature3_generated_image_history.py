"""Offline JWT route and RLS data-boundary regressions for Feature3 image history."""
import sys
from pathlib import Path
import unittest
from unittest.mock import Mock
from uuid import uuid4

sys.path.insert(0,str(Path(__file__).resolve().parents[2]/"azure-functions/campaign-api"))
from http_api import HTTPAPI
from security import AuthenticationError
from feature3_v2_api import Feature3V2API
from tenant_store import TenantStore,StorageUnavailable

SID,OTHER,JID,USER=[str(uuid4()) for _ in range(4)]

class GeneratedImageHistoryTests(unittest.TestCase):
    def setUp(self):
        self.tenant=Mock()
        self.tenant.member.return_value=True
        self.tenant.feature3_gpu_jobs.return_value=[
            {"id":JID,"shop_id":SID,"status":"SUCCEEDED"}]
        self.api=HTTPAPI(lambda token: USER if token=="valid-user" else self._denied(),
                         store=Mock(),feature3_api=Feature3V2API(self.tenant,Mock()))

    @staticmethod
    def _denied():
        raise AuthenticationError("JWT invalid or expired")

    def test_actual_functions_route_registered_and_paid_post_absent(self):
        from pathlib import Path
        entry=(Path(__file__).resolve().parents[2]/
               "azure-functions/campaign-api/function_app.py").read_text()
        self.assertIn('route="shops/{shop_id}/feature3-gpu-jobs", methods=["GET"]',entry)
        self.assertIn("def feature3_private_job_history(",entry)
        self.assertNotIn('route="shops/{shop_id}/feature3-gpu-jobs", methods=["POST"]',entry)

    def test_signed_member_get_only_and_no_paid_submit(self):
        self.assertEqual(self.api.handle("GET",f"/shops/{SID}/feature3-gpu-jobs",
                                         "Bearer valid-user"),
                         (200,{"shop_id":SID,
                               "jobs":[{"id":JID,"shop_id":SID,"status":"SUCCEEDED"}],
                               "gpu_submission_enabled":False}))
        self.tenant.feature3_gpu_jobs.assert_called_once_with("valid-user",SID)
        for method in ("POST","DELETE","PATCH"):
            self.assertEqual(self.api.handle(method,f"/shops/{SID}/feature3-gpu-jobs",
                                            "Bearer valid-user")[0],404)
        self.assertEqual(self.tenant.feature3_gpu_jobs.call_count,1)

    def test_denies_absent_expired_and_foreign_account(self):
        path=f"/shops/{SID}/feature3-gpu-jobs"
        for token in ("","Bearer expired","Basic bad","Bearer "):
            self.assertEqual(self.api.handle("GET",path,token)[0],401)
        self.tenant.feature3_gpu_jobs.assert_not_called()
        self.tenant.member.return_value=False
        self.assertEqual(self.api.handle("GET",path,"Bearer valid-user")[0],404)
        self.tenant.feature3_gpu_jobs.assert_not_called()

    def test_gpu_feature_disabled_and_no_public_start(self):
        off=HTTPAPI(lambda token:USER,store=Mock())
        self.assertEqual(off.handle("GET",f"/shops/{SID}/feature3-gpu-jobs",
                                    "Bearer valid-user")[0],503)
        # No POST launch endpoint exists, regardless of the feature flag.
        self.assertEqual(off.handle("POST",f"/shops/{SID}/feature3-gpu-jobs",
                                    "Bearer valid-user")[0],404)
        for extra in ("/foreign","/download"):
            self.assertEqual(self.api.handle("GET",f"/shops/{SID}/feature3-gpu-jobs"+extra,
                                             "Bearer valid-user")[0],404)

    def test_store_rejects_foreign_and_oversized_rows_even_if_backend_faults(self):
        store=object.__new__(TenantStore)
        store._request=Mock(return_value=[{"id":JID,"shop_id":OTHER,"status":"SUCCEEDED"}])
        with self.assertRaises(StorageUnavailable):
            store.feature3_gpu_jobs("valid-user",SID)
        store._request.return_value=[{"id":str(uuid4()),"shop_id":SID,
                                      "status":"SUCCEEDED"}]*21
        with self.assertRaises(StorageUnavailable):
            store.feature3_gpu_jobs("valid-user",SID)
        store._request.return_value=[{"id":JID,"shop_id":SID,
                                      "status":"APPROVED"}]
        with self.assertRaises(StorageUnavailable):
            store.feature3_gpu_jobs("valid-user",SID)

if __name__=="__main__":
    unittest.main()
