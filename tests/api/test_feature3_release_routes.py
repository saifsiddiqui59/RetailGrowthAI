"""Feature3 Task3.6: end-to-end *offline* HTTP route release gate.

Uses the actual HTTPAPI dispatch class and no user tokens/remote services.
Does not prove a live hosted signed-in user or any CUDA execution.
"""
from pathlib import Path
import sys
import unittest
from uuid import uuid4
from unittest.mock import Mock

sys.path.insert(0,str(Path(__file__).resolve().parents[2]/"azure-functions/campaign-api"))
from http_api import HTTPAPI
from security import AuthenticationError

S,A,J,U=[str(uuid4()) for _ in range(4)]
SRC=f"/shops/{S}/feature3-source-assets/{A}"
GPU=f"/shops/{S}/feature3-gpu-jobs/{J}/download"
MOD=f"/shops/{S}/feature3-models"

class RouterTests(unittest.TestCase):
    def jwt(self, token):
        if token!="owner-jwt":
            raise AuthenticationError("unauthorized")
        return U
    def api(self, feature=None):
        return HTTPAPI(self.jwt,store=Mock(),feature3_api=feature)
    def test_feature3_routes_off_and_no_gpu_entrypoint(self):
        api=self.api()
        for path in (SRC,GPU,MOD):
            with self.subTest(path=path):
                self.assertEqual(api.handle("GET",path,"Bearer owner-jwt"),
                                 (503,{"error":"FEATURE3_V2_DISABLED"}))
        self.assertEqual(api.handle("POST",GPU,"Bearer owner-jwt")[0],503)
        self.assertEqual(api.handle("POST",SRC,"Bearer owner-jwt")[0],503)
        # There is no public endpoint that directly starts a GPU job.
        self.assertEqual(api.handle("POST",f"/shops/{S}/feature3-gpu-jobs",
                                    "Bearer owner-jwt")[0],404)
    def test_missing_fake_expired_and_malformed_bearer_denied_first(self):
        feature=Mock()
        api=self.api(feature)
        for auth in ("","Bearer invalid","Basic username:password",
                     "Bearer expired","Bearer "):
            for path in (SRC,GPU,MOD):
                self.assertEqual(api.handle("GET",path,auth)[0],401)
        feature.source_asset.assert_not_called()
        feature.gpu_download.assert_not_called()
        feature.models.assert_not_called()
    def test_exact_route_method_and_uri_dispatch(self):
        f=Mock()
        f.source_asset.return_value=(200,{"registered":True})
        f.gpu_download.return_value=(200,{"expires_in_seconds":60})
        f.models.return_value=(200,{"models":[]})
        api=self.api(f)
        self.assertEqual(api.handle("GET",SRC,"Bearer owner-jwt")[0],200)
        self.assertEqual(api.handle("GET",GPU,"Bearer owner-jwt")[0],200)
        self.assertEqual(api.handle("GET",MOD,"Bearer owner-jwt")[0],200)
        f.source_asset.assert_called_once_with("owner-jwt",U,S,A)
        f.gpu_download.assert_called_once_with("owner-jwt",U,S,J)
        f.models.assert_called_once_with("owner-jwt",U,S)
        for bad_method,path in (("POST",SRC),("POST",GPU),("PATCH",MOD),
                                ("DELETE",SRC),("DELETE",GPU)):
            self.assertEqual(api.handle(bad_method,path,"Bearer owner-jwt")[0],404)
        self.assertEqual(f.source_asset.call_count,1)
        self.assertEqual(f.gpu_download.call_count,1)
        self.assertEqual(f.models.call_count,1)
    def test_forged_extra_route_parts_never_reach_privileged_api(self):
        f=Mock()
        api=self.api(f)
        for path in (SRC+"/extra",GPU+"/extra",MOD+"/foreign",
                     f"/shops/{S}/feature3-source-assets/{A}/download"):
            self.assertIn(api.handle("GET",path,"Bearer owner-jwt")[0],(404,503))
        f.source_asset.assert_not_called()
        f.gpu_download.assert_not_called()
        f.models.assert_not_called()

if __name__=="__main__":unittest.main()
