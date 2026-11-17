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
