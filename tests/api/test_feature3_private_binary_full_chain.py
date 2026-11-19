"""F3-08: route -> actual revocable reader, isolated synthetic two-shop tests.

No real JWT, hosted tenant, customer approval, GPU or commercial assets are used.
These exercise the complete in-process HTTP/reader/storage authorization chain.
"""
import sys
import unittest
from pathlib import Path
from uuid import uuid4

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "azure-functions" / "campaign-api"))
sys.path.insert(0, str(Path(__file__).resolve().parent))
from feature3_private_binary_route import private_png_response
from feature3_private_png_reader import Feature3RevocablePNGReader
from test_feature3_private_png_reader import FakeTenant, Response, original_png
from hashlib import sha256


class Request:
    method = "GET"
    headers = {"Authorization": "Bearer fake-signed-retailer-token"}


class IntegratedPrivateRouteTests(unittest.TestCase):
    def setUp(self):
        self.shop_a, self.shop_b = str(uuid4()), str(uuid4())
        self.job, self.user, self.asset = (str(uuid4()) for _ in range(3))
        self.png = original_png()
        self.digest = sha256(self.png).hexdigest()
        self.tenant = FakeTenant(self.shop_a, self.job, self.user, self.asset, self.digest)
        self.events = []
        self.rights_active = True
        self.switch_actor = False
        self.revoke_on_storage_read = False
        self.revoke_rights_on_storage_read = False

    def verifier(self, token):
        self.events.append("verify")
        if token != "fake-signed-retailer-token":
            raise ValueError("synthetic invalid JWT")
        return str(uuid4()) if self.switch_actor else self.user

    def rights(self, shop, job, asset):
        self.events.append("rights")
        return self.rights_active and (shop, job, asset) == (
            self.shop_a, self.job, self.asset)

    def storage(self, request, timeout):
        self.events.append("storage")
        self.assertEqual(timeout, 10)
        self.assertEqual(request.get_header("Authorization"),
                         "Bearer fake-signed-retailer-token")
        self.assertNotIn("/object/public/", request.full_url)
        self.assertNotIn("/object/sign/", request.full_url)
        if self.revoke_on_storage_read:
            self.tenant.active = False
        if self.revoke_rights_on_storage_read:
            self.rights_active = False
        return Response(request.full_url, self.png)

    def factory(self):
        self.events.append("factory")
        return Feature3RevocablePNGReader(
            tenant_store=self.tenant,
            verify_user_jwt=self.verifier,
            current_output_rights=self.rights,
            transport=self.storage)

    def invoke(self, shop=None, request=None):
        return private_png_response(
            request or Request(), shop_id=shop or self.shop_a,
            job_id=self.job, reader_factory=self.factory, enabled=True)

    def test_valid_synthetic_same_shop_uses_two_current_rights_checks(self):
        status, body, headers = self.invoke()
        self.assertEqual((status, body), (200, self.png))
        self.assertEqual(self.events,
                         ["factory", "verify", "rights", "storage", "rights", "verify"])
        self.assertEqual(self.tenant.calls,
                         ["member", "job", "asset", "member", "job", "asset"])
        self.assertEqual(headers["X-Feature3-Image-Sha256"], self.digest)
        self.assertEqual(headers["Cache-Control"], "no-store, private, max-age=0")
        self.assertNotIn("Location", headers)
        self.assertNotIn("Access-Control-Allow-Origin", headers)

    def test_foreign_shop_denied_before_storage_or_rights(self):
        status, body, headers = self.invoke(self.shop_b)
        self.assertEqual((status, body), (404, b""))
        self.assertEqual(self.events, ["factory", "verify"])
        self.assertNotIn("Location", headers)
        self.assertNotIn("X-Feature3-Media-Asset-Id", headers)

    def test_revoked_membership_after_storage_denies_bytes(self):
        self.revoke_on_storage_read = True
        status, body, headers = self.invoke()
        self.assertEqual((status, body), (404, b""))
        self.assertEqual(self.events, ["factory", "verify", "rights", "storage"])
        self.assertNotIn("X-Feature3-Image-Sha256", headers)

    def test_revoked_output_rights_after_storage_denies_bytes(self):
        self.revoke_rights_on_storage_read = True
        status, body, headers = self.invoke()
        self.assertEqual((status, body), (404, b""))
        self.assertEqual(self.events,
                         ["factory", "verify", "rights", "storage", "rights"])
        self.assertNotIn("Content-Disposition", headers)

    def test_bad_bearer_never_constructs_privileged_reader(self):
        req = Request()
        req.headers = {"Authorization": "Bearer sb_secret_fixture_only"}
        status, body, _ = self.invoke(request=req)
        self.assertEqual((status, body), (401, b""))
        self.assertEqual(self.events, [])
        self.assertEqual(self.tenant.calls, [])

    def test_backend_rights_outage_does_not_fall_back_to_png(self):
        def unavailable(*_args):
            raise RuntimeError("private rights service offline")
        self.rights = unavailable
        status, body, headers = self.invoke()
        self.assertEqual((status, body), (404, b""))
        self.assertEqual(self.events, ["factory", "verify"])
        self.assertNotIn("private rights", str(headers).lower())
        self.assertNotIn("Location", headers)

    def test_reader_construction_failure_is_opaque(self):
        self.tenant.key = "sb_secret_NOT_A_PUBLIC_KEY"
        status, body, headers = self.invoke()
        self.assertEqual((status, body), (503, b""))
        self.assertEqual(self.events, ["factory"])
        self.assertNotIn("secret", str(headers).lower())


if __name__ == "__main__":
    unittest.main()
