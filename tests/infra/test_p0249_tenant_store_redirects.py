"""#249: original user-JWT PostgREST transport must never follow HTTP redirects.

No real credentials, network, Azure deployment, database or customer records.
"""
import io
from email.message import Message
from pathlib import Path
import sys
import unittest
from unittest.mock import patch
from urllib.request import HTTPSHandler, ProxyHandler, build_opener
from urllib.response import addinfourl

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "azure-functions/campaign-api"))
import tenant_store  # noqa: E402

ORIGIN = "https://synthetic-p0249.supabase.co"
TOKEN = "synthetic.bearer.not-real"
PUBLIC = "sb_publishable_synthetic_only"


class RedirectingHTTPS(HTTPSHandler):
    """A synthetic upstream 30x; no actual DNS/TLS request."""
    def __init__(self, redirect_status):
        super().__init__()
        self.status = redirect_status
        self.attempted = []

    def https_open(self, request):
        self.attempted.append((
            request.full_url, request.get_header("Authorization"),
            request.get_header("Apikey"),
        ))
        headers = Message()
        headers["Location"] = "https://untrusted-p0249.invalid/collect"
        response = addinfourl(io.BytesIO(b""), headers, request.full_url,
                              self.status)
        response.msg = "Redirect"
        return response


class JSONResponse:
    def __enter__(self):
        return self

    def __exit__(self, *_args):
        return False

    def read(self):
        return b"[]"


class TenantStoreRedirectSafety(unittest.TestCase):
    def test_real_default_transport_rejects_all_redirects_without_replaying_user_jwt(self):
        for status in (301, 302, 303, 307, 308):
            with self.subTest(status=status):
                redirect = RedirectingHTTPS(status)
                opener = build_opener(ProxyHandler({}),
                                      tenant_store._RejectRedirects(), redirect)
                with patch.object(tenant_store, "_NO_REDIRECT_OPENER", opener):
                    store = tenant_store.TenantStore(ORIGIN, PUBLIC)
                    self.assertIs(store.transport.__self__, opener)
                    with self.assertRaises(tenant_store.StorageUnavailable) as error:
                        store._request("campaigns", TOKEN, query={"select": "id"})
                self.assertEqual(len(redirect.attempted), 1)
                path, auth, public = redirect.attempted[0]
                self.assertEqual(path, ORIGIN + "/rest/v1/campaigns?select=id")
                self.assertEqual(auth, "Bearer " + TOKEN)
                self.assertEqual(public, PUBLIC)
                self.assertNotIn(TOKEN, str(error.exception))

    def test_initial_origin_is_pinned_to_https_authority_before_jwt_transport(self):
        bad = (
            "", "http://synthetic-p0249.supabase.co",
            "https://", "https://name:password@synthetic-p0249.supabase.co",
            "https://synthetic-p0249.supabase.co/rest/v1",
            "https://synthetic-p0249.supabase.co/?token=leak",
            "https://synthetic-p0249.supabase.co/#fragment",
            "https://synthetic-p0249.supabase.co?",
            "https://synthetic-p0249.supabase.co#",
            "https://synthetic-p0249.supabase.co:bad",
            "https://[not-an-ipv6",
            "https://synthetic-p0249.supabase.co\\\\@untrusted.invalid",
            "https://synthetic-p0249.supabase.co\nExtra: yes",
            None, 42,
        )
        for origin in bad:
            with self.subTest(origin=repr(origin)), self.assertRaises(ValueError):
                tenant_store.TenantStore(origin, PUBLIC)
        for origin in (ORIGIN, ORIGIN + "/", ORIGIN + ":443"):
            with self.subTest(origin=origin):
                store = tenant_store.TenantStore(origin, PUBLIC)
                self.assertEqual(store.origin, origin.rstrip("/"))
        for key in (None, "", 5):
            with self.subTest(key=key), self.assertRaises(ValueError):
                tenant_store.TenantStore(ORIGIN, key)

    def test_explicit_test_transport_remains_injectable(self):
        seen = []

        def fixture(request, timeout):
            seen.append((request.full_url, request.get_header("Authorization"),
                         request.get_method(), timeout))
            return JSONResponse()

        store = tenant_store.TenantStore(ORIGIN, PUBLIC, transport=fixture)
        self.assertEqual(store._request("campaigns", TOKEN), [])
        self.assertEqual(seen, [
            (ORIGIN + "/rest/v1/campaigns", "Bearer " + TOKEN, "GET", 8)
        ])


if __name__ == "__main__":
    unittest.main()
