"""#249: genuine offline signed JWT through original 3 GET status APIs/RLS.

No cloud, data mutations or private identities. Local RSA keys and synthetic
PostgREST transport simulate even an unsafe foreign-row response; original
HTTPAPI and TenantStore must still enforce current membership.
"""
from datetime import datetime, timedelta, timezone
import importlib.util
import json
from pathlib import Path
import sys
from types import SimpleNamespace
import unittest
from unittest.mock import patch
from urllib.parse import parse_qs, urlsplit

import jwt
from cryptography.hazmat.primitives.asymmetric import rsa

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "ai-agents/src"))
sys.path.insert(0, str(ROOT / "azure-functions/campaign-api"))
SOURCE = ROOT / "ops/p0249-y1-readonly-extra-get/p0249_readonly_jobs.py"
spec = importlib.util.spec_from_file_location("p0249_real_extra_signed_shadow", SOURCE)
shadow = importlib.util.module_from_spec(spec)
spec.loader.exec_module(shadow)

ORIGIN = "https://p0249-test-only.supabase.co"
ENV = {
    "RGAI_P0249_READONLY_SHADOW": "true",
    "RGAI_P0249_EXTRA_GET_SHADOW": "true",
    "RETAIL_SUPABASE_URL": ORIGIN,
    "RETAIL_SUPABASE_PUBLISHABLE_KEY": "sb_publishable_synthetic_only",
}
A_USER = "11111111-1111-4111-8111-111111111111"
B_USER = "22222222-2222-4222-8222-222222222222"
A_SHOP = "33333333-3333-4333-8333-333333333333"
B_SHOP = "44444444-4444-4444-8444-444444444444"
A_RECORD = "55555555-5555-4555-8555-555555555555"
B_RECORD = "66666666-6666-4666-8666-666666666666"
KEY = rsa.generate_private_key(public_exponent=65537, key_size=2048)
WRONG_KEY = rsa.generate_private_key(public_exponent=65537, key_size=2048)
KINDS = ("render_job", "poster_job", "poster_draft")
TABLES = {"render_job": "render_jobs", "poster_job": "poster_jobs",
          "poster_draft": "poster_drafts"}


def token(user=A_USER, key=KEY, **updates):
    now = datetime.now(timezone.utc)
    claims = {
        "sub": user,
        "iss": ORIGIN + "/auth/v1",
        "aud": "authenticated",
        "role": "authenticated",
        "iat": now,
        "exp": now + timedelta(minutes=10),
    }
    claims.update(updates)
    return jwt.encode(claims, key, algorithm="RS256",
                      headers={"kid": "synthetic-offline-only"})


class Response:
    def __init__(self, rows):
        self.rows = rows

    def __enter__(self):
        return self

    def __exit__(self, *_):
        return False

    def read(self):
        return json.dumps(self.rows).encode("utf-8")


class StrictSyntheticPostgREST:
    def __init__(self):
        self.active = {A_USER: {A_SHOP: "OWNER"}, B_USER: {B_SHOP: "VIEWER"}}
        self.calls = []

    def __call__(self, req, timeout):
        assert timeout <= 8
        assert req.get_method() == "GET", "GET shadow must not mutate any data"
        assert req.data is None
        assert req.get_header("Apikey") == ENV["RETAIL_SUPABASE_PUBLISHABLE_KEY"]
        bearer = req.get_header("Authorization")
        assert bearer and bearer.startswith("Bearer ")
        user = jwt.decode(bearer[7:], KEY.public_key(), algorithms=["RS256"],
                          issuer=ORIGIN + "/auth/v1", audience="authenticated")["sub"]
        uri = urlsplit(req.full_url)
        assert uri.scheme == "https" and uri.netloc == "p0249-test-only.supabase.co"
        assert uri.path.startswith("/rest/v1/")
        table = uri.path.rsplit("/", 1)[-1]
        params = parse_qs(uri.query)
        assert params.get("limit") == ["1"]
        self.calls.append((user, table, dict(params)))
        if table == "shop_memberships":
            assert params["user_id"] == ["eq." + user]
            assert params["active"] == ["eq.true"]
            shop_id = params["shop_id"][0].removeprefix("eq.")
            role = self.active.get(user, {}).get(shop_id)
            return Response([{"role": role}] if role else [])
        assert table in TABLES.values(), "unapproved DB table"
        target = params["id"][0].removeprefix("eq.")
        assert target in (A_RECORD, B_RECORD)
        shop = A_SHOP if target == A_RECORD else B_SHOP
        # Return foreign rows deliberately, so original TenantStore must check
        # current membership even against an unsafe upstream response.
        if table == "render_jobs":
            return Response([{"id": target, "shop_id": shop, "status": "QUEUED",
                              "output_asset_id": None, "error_code": None}])
        if table == "poster_jobs":
            return Response([{"id": target, "shop_id": shop, "poster_id": target,
                              "status": "QUEUED", "output_asset_id": None,
                              "error_code": None}])
        return Response([{"id": target, "shop_id": shop,
                          "campaign_id": target, "day_id": target, "status": "DRAFT",
                          "template": "minimal", "format": "square",
                          "business_name": "Offline Example",
                          "accent_color": "#000000",
                          "background_color": "#ffffff",
                          "offer_text": None, "source_asset_id": target,
                          "output_asset_id": None}])


class SignedThreeReadStatusRLS(unittest.TestCase):
    def setUp(self):
        self.backend = StrictSyntheticPostgREST()
        from security import cached_supabase_verifier
        cached_supabase_verifier.cache_clear()
        self.addCleanup(cached_supabase_verifier.cache_clear)
        p1 = patch("security.PyJWKClient", return_value=SimpleNamespace(
            get_signing_key_from_jwt=lambda _jwt: SimpleNamespace(key=KEY.public_key())))
        p2 = patch("tenant_store.urlopen", side_effect=self.backend)
        for p in (p1, p2):
            p.start()
            self.addCleanup(p.stop)

    def get(self, kind, identity, user=A_USER, *, jwt_token=None, settings=None):
        signed = token(user) if jwt_token is None else jwt_token
        return shadow.handle_get(kind, identity, "Bearer " + signed,
                                 environment=ENV if settings is None else settings)

    def test_each_signed_user_reads_only_current_own_shop_across_three_routes(self):
        for kind in KINDS:
            with self.subTest(kind=kind):
                self.assertEqual(self.get(kind, A_RECORD, A_USER)[0], 200)
                self.assertEqual(self.get(kind, B_RECORD, B_USER)[0], 200)
        self.assertEqual({t for _, t, _ in self.backend.calls},
                         set(TABLES.values()) | {"shop_memberships"})
        self.assertEqual(len(self.backend.calls), 12)

    def test_foreign_rows_hidden_even_if_fake_postgrest_leaks_them(self):
        for kind in KINDS:
            for user, foreign in ((A_USER, B_RECORD), (B_USER, A_RECORD)):
                with self.subTest(kind=kind, user=user):
                    before = len(self.backend.calls)
                    self.assertEqual(self.get(kind, foreign, user),
                                     (404, {"error": "NOT_FOUND"}))
                    recent = self.backend.calls[before:]
                    self.assertEqual([t for _, t, _ in recent],
                                     [TABLES[kind], "shop_memberships"])

    def test_membership_revocation_enforced_next_request_without_jwt_change(self):
        access_token = token(A_USER)
        for kind in KINDS:
            self.assertEqual(self.get(kind, A_RECORD, jwt_token=access_token)[0], 200)
        del self.backend.active[A_USER][A_SHOP]
        for kind in KINDS:
            self.assertEqual(self.get(kind, A_RECORD, jwt_token=access_token),
                             (404, {"error": "NOT_FOUND"}))

    def test_invalid_signature_issuer_audience_anonymous_and_role_never_reach_store(self):
        malformed = [
            token(key=WRONG_KEY),
            token(iss="https://wrong-project.supabase.co/auth/v1"),
            token(aud="wrong"),
            token(role="service_role"),
            token(is_anonymous=True),
            token(exp=datetime.now(timezone.utc)-timedelta(minutes=5)),
            token(sub="not-a-uuid"),
        ]
        for kind in KINDS:
            for value in malformed:
                with self.subTest(kind=kind, index=malformed.index(value)):
                    before = len(self.backend.calls)
                    self.assertEqual(self.get(kind, A_RECORD, jwt_token=value),
                                     (401, {"error": "UNAUTHORIZED"}))
                    self.assertEqual(len(self.backend.calls), before)

    def test_feature_disabled_denies_genuine_signed_user_without_db(self):
        for kind in KINDS:
            with self.subTest(kind=kind):
                self.assertEqual(self.get(kind, A_RECORD, settings={}),
                                 (503, {"error": "SERVICE_NOT_CONFIGURED"}))
        self.assertEqual(self.backend.calls, [])


if __name__ == "__main__":
    unittest.main()
