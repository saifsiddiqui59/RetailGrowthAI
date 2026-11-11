"""#249: real original JWT -> HTTPAPI -> TenantStore, two-shop shadow fixture.

Zero Azure, Supabase, customer credentials or writes. This deliberately does NOT
claim hosted JWT/RLS acceptance or turn on the Y1 shadow feature flag.
"""
from datetime import datetime, timedelta, timezone
import importlib.util
import io
import json
from pathlib import Path
from types import SimpleNamespace, ModuleType
from unittest import TestCase
from unittest.mock import patch
from urllib.parse import parse_qs, urlsplit
from uuid import UUID

import jwt
from cryptography.hazmat.primitives.asymmetric import rsa

ROOT = Path(__file__).resolve().parents[2]
import sys
sys.path.insert(0, str(ROOT / "ai-agents/src"))
sys.path.insert(0, str(ROOT / "azure-functions/campaign-api"))
SHADOW = ROOT / "ops/p0249-y1-readonly-campaign/campaign_read/__init__.py"
spec = importlib.util.spec_from_file_location("p0249_signed_two_shop_shadow", SHADOW)
shadow = importlib.util.module_from_spec(spec)
try:
    import azure.functions  # installed in the real Y1 package and pytest CI
except ModuleNotFoundError:
    # Infra unittest also executes with system Python and no azure-functions.
    # Stub ONLY the framework response shape, never JWT, HTTPAPI or TenantStore.
    framework = ModuleType("azure.functions")
    class LocalHttpResponse:
        def __init__(self, body, *, status_code, mimetype, headers):
            self.status_code = status_code
            self.mimetype = mimetype
            self.headers = headers
            self._body = body.encode("utf-8")
        def get_body(self):
            return self._body
    framework.HttpResponse = LocalHttpResponse
    package = ModuleType("azure")
    package.__path__ = []
    package.functions = framework
    with patch.dict(sys.modules, {"azure": package, "azure.functions": framework}):
        spec.loader.exec_module(shadow)
else:
    spec.loader.exec_module(shadow)

ORIGIN = "https://fixture-p0249.supabase.co"
ENV = {
    "RGAI_P0249_READONLY_SHADOW": "true",
    "RETAIL_SUPABASE_URL": ORIGIN,
    "RETAIL_SUPABASE_PUBLISHABLE_KEY": "sb_publishable_fixture_only",
}
A_USER = "11111111-1111-4111-8111-111111111111"
B_USER = "22222222-2222-4222-8222-222222222222"
A_SHOP = "33333333-3333-4333-8333-333333333333"
B_SHOP = "44444444-4444-4444-8444-444444444444"
A_CAMPAIGN = "55555555-5555-4555-8555-555555555555"
B_CAMPAIGN = "66666666-6666-4666-8666-666666666666"

RSA_KEY = rsa.generate_private_key(public_exponent=65537, key_size=2048)
OTHER_KEY = rsa.generate_private_key(public_exponent=65537, key_size=2048)


class JSONResponse:
    def __init__(self, rows):
        self.rows = rows

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False

    def read(self):
        return json.dumps(self.rows).encode("utf-8")


def make_token(user=A_USER, key=RSA_KEY, **claims):
    now = datetime.now(timezone.utc)
    payload = {
        "sub": user,
        "iss": ORIGIN + "/auth/v1",
        "aud": "authenticated",
        "role": "authenticated",
        "iat": now,
        "exp": now + timedelta(minutes=4),
    }
    payload.update(claims)
    return jwt.encode(payload, key, algorithm="RS256", headers={"kid": "p0249-offline-only"})


class TwoShopRLSFixture:
    """Simulates signed PostgREST SELECT only, not hosted Supabase RLS proof."""

    def __init__(self):
        self.active = {A_USER: {A_SHOP: "OWNER"}, B_USER: {B_SHOP: "VIEWER"}}
        self.leak_foreign_row = True  # even unsafe upstream row cannot skip current member()
        self.requests = []

    def __call__(self, req, timeout):
        assert timeout <= 8
        assert req.get_method() == "GET", "Y1 shadow must never perform SQL mutations"
        assert req.data is None
        assert req.get_header("Apikey") == ENV["RETAIL_SUPABASE_PUBLISHABLE_KEY"]
        bearer = req.get_header("Authorization")
        assert bearer and bearer.startswith("Bearer ")
        token = bearer.removeprefix("Bearer ")
        user = jwt.decode(
            token, RSA_KEY.public_key(), algorithms=["RS256"],
            audience="authenticated", issuer=ORIGIN + "/auth/v1",
        )["sub"]
        uri = urlsplit(req.full_url)
        assert uri.netloc == "fixture-p0249.supabase.co"
        assert uri.scheme == "https"
        assert uri.path.startswith("/rest/v1/")
        params = parse_qs(uri.query, keep_blank_values=True)
        table = uri.path.rsplit("/", 1)[-1]
        self.requests.append((user, table, params))
        if table == "campaigns":
            cid = params.get("id", [""])[0]
            assert cid in ("eq." + A_CAMPAIGN, "eq." + B_CAMPAIGN)
            assert params.get("limit") == ["1"]
            campaign = A_CAMPAIGN if cid == "eq." + A_CAMPAIGN else B_CAMPAIGN
            shop = A_SHOP if campaign == A_CAMPAIGN else B_SHOP
            # Return a row even for a foreign user. The original TenantStore
            # MUST enforce current membership separately before returning it.
            return JSONResponse([{"id": campaign, "shop_id": shop, "status": "PLANNING"}])
        if table == "shop_memberships":
            uid, sid = params.get("user_id", [None])[0], params.get("shop_id", [None])[0]
            assert uid == "eq." + user, "membership must target the VERIFIED JWT sub"
            assert sid in ("eq." + A_SHOP, "eq." + B_SHOP)
            assert params.get("active") == ["eq.true"]
            assert params.get("limit") == ["1"]
            role = self.active.get(user, {}).get(sid.removeprefix("eq."))
            return JSONResponse([{"role": role}] if role else [])
        if table == "campaign_days":
            cid = params.get("campaign_id", [""])[0]
            sid = params.get("shop_id", [""])[0]
            assert (cid, sid) in {
                ("eq." + A_CAMPAIGN, "eq." + A_SHOP),
                ("eq." + B_CAMPAIGN, "eq." + B_SHOP),
            }, "campaign days must use exact selected shop and campaign"
            assert user in self.active and sid.removeprefix("eq.") in self.active[user]
            return JSONResponse([])
        raise AssertionError("Unexpected API/SQL table invoked")


class Y1SignedOriginalTwoShopParity(TestCase):
    def setUp(self):
        self.backend = TwoShopRLSFixture()
        # This is not a mocked verifier or HTTPAPI. We replace only the external
        # JWKS transport and database HTTP transport; real JWT verification,
        # original HTTPAPI and TenantStore membership code all execute.
        self.patches = (
            patch("security.PyJWKClient", return_value=SimpleNamespace(
                get_signing_key_from_jwt=lambda _t: SimpleNamespace(key=RSA_KEY.public_key())
            )),
            patch("tenant_store.urlopen", side_effect=self.backend),
        )
        for p in self.patches:
            p.start()
            self.addCleanup(p.stop)

    def get(self, token, campaign=A_CAMPAIGN):
        return shadow.handle_campaign_get(
            "Bearer " + token, campaign, environment=ENV
        )

    def test_two_real_signed_subjects_get_only_their_own_shop(self):
        first = self.get(make_token(A_USER), A_CAMPAIGN)
        second = self.get(make_token(B_USER), B_CAMPAIGN)
        self.assertEqual(first[0], 200)
        self.assertEqual(second[0], 200)
        self.assertEqual(first[1]["shop_id"], A_SHOP)
        self.assertEqual(second[1]["shop_id"], B_SHOP)
        self.assertEqual(first[1]["days"], [])
        self.assertEqual(second[1]["days"], [])
        self.assertTrue(all(t in ("campaigns", "shop_memberships", "campaign_days")
                            for _, t, _ in self.backend.requests))

    def test_forged_cross_tenant_response_stays_hidden(self):
        for user, foreign in ((A_USER, B_CAMPAIGN), (B_USER, A_CAMPAIGN)):
            before = len(self.backend.requests)
            code, payload = self.get(make_token(user), foreign)
            self.assertEqual((code, payload), (404, {"error": "NOT_FOUND"}))
            new_requests = self.backend.requests[before:]
            self.assertEqual([x[1] for x in new_requests],
                             ["campaigns", "shop_memberships"])
            self.assertNotIn("shop_id", payload)

    def test_current_membership_revocation_takes_effect_next_get(self):
        token = make_token(A_USER)
        self.assertEqual(self.get(token)[0], 200)
        del self.backend.active[A_USER][A_SHOP]
        self.assertEqual(self.get(token), (404, {"error": "NOT_FOUND"}))
        self.assertEqual([t for _, t, _ in self.backend.requests].count("campaign_days"), 1)

    def test_invalid_signed_claims_and_forged_signatures_denied_before_store(self):
        invalid = [
            make_token(key=OTHER_KEY),
            make_token(iss="https://foreign.supabase.co/auth/v1"),
            make_token(aud="unexpected"),
            make_token(role="service_role"),
            make_token(is_anonymous=True),
            make_token(exp=datetime.now(timezone.utc)-timedelta(minutes=5)),
            make_token(sub="not-a-uuid"),
        ]
        for token in invalid:
            before = len(self.backend.requests)
            with self.subTest(token_kind=invalid.index(token)):
                self.assertEqual(self.get(token), (401, {"error": "UNAUTHORIZED"}))
                self.assertEqual(len(self.backend.requests), before,
                                 "rejected JWT must not reach PostgREST")

    def test_disabled_shadow_rejects_even_signed_user_without_jwks_or_sql(self):
        token = make_token(A_USER)
        with patch.object(shadow, "_build_original_api",
                          side_effect=AssertionError("never load API")):
            self.assertEqual(
                shadow.handle_campaign_get("Bearer " + token, A_CAMPAIGN,
                                           environment={}),
                (503, {"error": "SERVICE_NOT_CONFIGURED"}),
            )
        self.assertEqual(self.backend.requests, [])

    def test_malformed_campaign_cannot_read_other_tenants(self):
        token = make_token(A_USER)
        for campaign in ("../" + B_CAMPAIGN, "AAAAAAAA-AAAA-4AAA-8AAA-AAAAAAAAAAAA", "not-a-uuid"):
            # Source HTTPAPI may ask for malformed campaign before DB dispatch,
            # but no other tenant row is returned or leaked.
            before = len(self.backend.requests)
            code, body = self.get(token, campaign)
            self.assertIn(code, (400, 404))
            self.assertNotIn("shop_id", body)
            self.assertEqual(len(self.backend.requests), before)

    def test_shadow_request_response_contains_no_secret_or_customer_token(self):
        token = make_token(A_USER)
        request = SimpleNamespace(
            route_params={"campaign_id": B_CAMPAIGN},
            headers={"Authorization": "Bearer " + token},
        )
        with patch.dict("os.environ", ENV):
            result = shadow.main(request)
        self.assertEqual(result.status_code, 404)
        body = result.get_body().decode("utf-8")
        self.assertEqual(json.loads(body), {"error": "NOT_FOUND"})
        self.assertNotIn(token, body)
        self.assertNotIn(token, json.dumps(dict(result.headers)))
        self.assertTrue(result.headers.get("X-Request-ID"))
        self.assertEqual(result.headers.get("Cache-Control"), "no-store")


if __name__ == "__main__":
    import unittest
    unittest.main()
