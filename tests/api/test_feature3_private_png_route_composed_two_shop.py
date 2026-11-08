"""F3-08 CPU-only two-shop private PNG route composition and revocation.

These are synthetic JWTs, generated images, RLS responses and Storage HTTP
responses. They prove source isolation and response contracts only, NOT an
activated Azure route or genuine hosted Supabase authorization.
"""
from __future__ import annotations

from hashlib import sha256
from io import BytesIO
from pathlib import Path
import sys
import unittest
from uuid import uuid4

from PIL import Image

sys.path.insert(
    0, str(Path(__file__).resolve().parents[2] /
           "azure-functions" / "campaign-api")
)
from feature3_private_png_binding import build_private_png_reader_factory
from feature3_private_png_route import handle_private_png_request


class Request:
    method = "GET"
    params = {}

    def __init__(self, shop, job, token):
        self.route_params = {"shop_id": shop, "job_id": job}
        self.headers = {"Authorization": "Bearer " + token}

    def get_body(self):
        return b""


class Response:
    def __init__(self, *, body, status_code, headers, mimetype):
        self.body = body
        self.status_code = status_code
        self.headers = headers
        self.mimetype = mimetype


class PrivateStorageResponse:
    def __init__(self, url, raw, on_read):
        self.url = url
        self.raw = raw
        self.headers = {"Content-Type": "image/png",
                        "Content-Length": str(len(raw))}
        self.on_read = on_read

    def __enter__(self):
        return self

    def __exit__(self, *_):
        return False

    def geturl(self):
        return self.url

    def getcode(self):
        return 200

    def read(self, max_bytes):
        self.on_read()
        return self.raw[:max_bytes]


class TwoShopRLS:
    origin = "https://fixture-project.supabase.co"
    key = "sb_publishable_" + "x" * 24

    def __init__(self, fixtures, calls):
        self.fixtures = fixtures
        self.calls = calls

    def member(self, token, actor, shop):
        self.calls.append(("rls_member", shop))
        current = self.fixtures.get(shop)
        return (current is not None and token == current["token"] and
                actor == current["actor"] and current["member_active"])

    def feature3_gpu_job(self, token, shop, job):
        self.calls.append(("rls_job", shop))
        current = self.fixtures.get(shop)
        if current is None or job != current["job"]:
            return None
        return {"id": job, "shop_id": shop, "status": "SUCCEEDED",
                "output_asset_id": current["asset"]}

    def feature3_generated_asset(self, token, shop, job, asset):
        self.calls.append(("rls_asset", shop))
        current = self.fixtures.get(shop)
        if (current is None or job != current["job"] or
                asset != current["asset"]):
            return None
        # Real TenantStore verifies the row's private bucket and generated
        # source before reducing it to this minimal RLS receipt.
        return {"object_path": current["path"], "mime_type": "image/png"}


class ComposedRouteTests(unittest.TestCase):
    def setUp(self):
        self.fixtures = {}
        self.calls = []
        for label, color in (("A", "#245a7a"), ("B", "#a35c47")):
            shop, job, actor, asset = (str(uuid4()) for _ in range(4))
            stream = BytesIO()
            Image.new("RGB", (320, 400), color).save(stream, format="PNG")
            raw = stream.getvalue()
            digest = sha256(raw).hexdigest()
            token = "synthetic-jwt-shop-" + label + "-long-not-real"
            self.fixtures[shop] = {
                "label": label, "shop": shop, "job": job,
                "actor": actor, "asset": asset, "token": token,
                "raw": raw, "digest": digest, "member_active": True,
                "rights_active": True,
                "path": f"{shop}/feature3/gpu/{job}/{digest}.png",
            }
        self.a, self.b = list(self.fixtures.values())
        self.revoke_on_storage_read = None
        self.expire_token_on_storage_read = None
        self.jwt_revoked = set()
        tenant = TwoShopRLS(self.fixtures, self.calls)

        def verify(token):
            self.calls.append(("jwt", token))
            if token in self.jwt_revoked:
                raise ValueError("synthetic expired JWT")
            for fixture in self.fixtures.values():
                if fixture["token"] == token:
                    return fixture["actor"]
            raise ValueError("unrecognized synthetic token")

        def fresh_rights(shop, job, asset):
            self.calls.append(("rights", shop))
            current = self.fixtures.get(shop)
            return (current is not None and
                    current["job"] == job and current["asset"] == asset and
                    current["rights_active"])

        def private_transport(request, timeout):
            self.assertEqual(timeout, 10)
            self.assertEqual(request.get_method(), "GET")
            self.assertEqual(request.get_header("Apikey"), tenant.key)
            token = request.get_header("Authorization")
            self.assertIsInstance(token, str)
            self.assertTrue(token.startswith("Bearer synthetic-jwt-shop-"))
            self.calls.append(("storage", request.full_url))
            for fixture in self.fixtures.values():
                if request.full_url.endswith(fixture["path"]):
                    self.assertEqual(token, "Bearer " + fixture["token"])
                    def on_read():
                        if self.revoke_on_storage_read == fixture["shop"]:
                            fixture["rights_active"] = False
                        if self.expire_token_on_storage_read == fixture["shop"]:
                            self.jwt_revoked.add(fixture["token"])
                    return PrivateStorageResponse(
                        request.full_url, fixture["raw"], on_read)
            raise AssertionError("foreign or nonprivate Storage path")

        self.factory = build_private_png_reader_factory(
            origin=tenant.origin, publishable_key=tenant.key,
            tenant=tenant, verifier=verify,
            current_output_rights=fresh_rights,
            transport=private_transport)

    def request(self, fixture, *, token=None):
        return handle_private_png_request(
            Request(fixture["shop"], fixture["job"],
                    fixture["token"] if token is None else token),
            reader_factory=self.factory, response_type=Response)

    def assert_no_private_bytes(self, reply, status):
        self.assertEqual(reply.status_code, status)
        self.assertEqual(reply.body, b"")
        self.assertEqual(reply.headers["Content-Length"], "0")
        self.assertIn("no-store", reply.headers["Cache-Control"])

    def test_two_distinct_shops_get_only_their_own_png_and_safe_headers(self):
        for fixture in (self.a, self.b):
            with self.subTest(shop=fixture["label"]):
                start = len(self.calls)
                reply = self.request(fixture)
                self.assertEqual(reply.status_code, 200)
                self.assertEqual(reply.body, fixture["raw"])
                self.assertNotEqual(reply.body,
                                    (self.b if fixture is self.a else self.a)["raw"])
                self.assertEqual(reply.mimetype, "image/png")
                self.assertEqual(reply.headers["Content-Length"],
                                 str(len(fixture["raw"])))
                self.assertEqual(reply.headers["Cache-Control"],
                                 "no-store, private")
                self.assertEqual(reply.headers["Vary"], "Authorization")
                self.assertNotIn("Location", reply.headers)
                self.assertNotIn("Set-Cookie", reply.headers)
                self.assertNotIn("X-Feature3-Image-Sha256", reply.headers)
                performed = self.calls[start:]
                self.assertEqual(sum(name == "rights"
                                     for name, _ in performed), 2)
                self.assertEqual(sum(name == "storage"
                                     for name, _ in performed), 1)
                self.assertEqual(sum(name == "rls_member"
                                     for name, _ in performed), 2)

    def test_foreign_shop_token_denies_before_storage_or_rights(self):
        for fixture, foreign in ((self.a, self.b), (self.b, self.a)):
            with self.subTest(shop=fixture["label"]):
                self.calls.clear()
                reply = self.request(fixture, token=foreign["token"])
                self.assert_no_private_bytes(reply, 404)
                self.assertFalse(any(name in ("storage", "rights")
                                     for name, _ in self.calls))
        # Cross-shop denial is not a global outage; a correct JWT still works.
        self.assertEqual(self.request(self.a).status_code, 200)

    def test_revocation_during_private_storage_read_denies_returned_png(self):
        self.revoke_on_storage_read = self.a["shop"]
        reply = self.request(self.a)
        self.assert_no_private_bytes(reply, 404)
        self.assertEqual(sum(name == "storage"
                             for name, _ in self.calls), 1)
        self.assertEqual(sum(name == "rights"
                             for name, _ in self.calls), 2)
        self.revoke_on_storage_read = None
        self.a["rights_active"] = True
        self.assertEqual(self.request(self.a).status_code, 200)

    def test_expired_jwt_after_bytes_denies_even_if_rights_stay_approved(self):
        self.expire_token_on_storage_read = self.b["shop"]
        reply = self.request(self.b)
        self.assert_no_private_bytes(reply, 404)
        self.assertTrue(self.b["rights_active"])
        self.assertEqual(sum(name == "storage"
                             for name, _ in self.calls), 1)
        self.jwt_revoked.clear()
        self.expire_token_on_storage_read = None
        self.assertEqual(self.request(self.b).status_code, 200)


if __name__ == "__main__":
    unittest.main()
