"""#249: privileged original PostgREST worker transport denies off-origin redirects.

Offline synthetic HTTPS and error bodies only. No Azure, Supabase, paid model,
queue or customer data. Preserves the original AdminStore business RPCs.
"""
import io
from email.message import Message
from pathlib import Path
import sys
import unittest
from unittest.mock import patch
from urllib.error import HTTPError
from urllib.request import HTTPSHandler, ProxyHandler, build_opener
from urllib.response import addinfourl

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "azure-functions/campaign-api"))
import admin_store  # noqa: E402
from tenant_store import StorageUnavailable, SubscriptionDenied  # noqa: E402

ORIGIN = "https://synthetic-p0249.supabase.co"
OPAQUE_KEY = "sb_secret_testfixture_not_real"
LEGACY_KEY = "eyJfake.header.not_a_signature"


class SyntheticRedirectHTTPS(HTTPSHandler):
    def __init__(self, status):
        super().__init__()
        self.status = status
        self.sent = []
        self.responses = []

    def https_open(self, req):
        self.sent.append((req.full_url, req.get_method(),
                          req.get_header("Apikey"),
                          req.get_header("Authorization")))
        headers = Message()
        headers["Location"] = "https://untrusted-p0249.invalid/collect"
        response = addinfourl(io.BytesIO(b""), headers, req.full_url,
                              self.status)
        response.msg = "Redirect"
        self.responses.append(response)
        return response


class JSONResponse:
    def __enter__(self):
        return self

    def __exit__(self, *_args):
        return False

    def read(self):
        return b"[]"


class PrivilegedWorkerRedirectSafety(unittest.TestCase):
    def test_default_transport_uses_the_no_redirect_opener(self):
        store = admin_store.AdminStore(ORIGIN, OPAQUE_KEY)
        self.assertIs(store.transport, admin_store.urlopen)
        self.assertTrue(any(isinstance(handler, admin_store._DenyRedirects)
                            for handler in admin_store.urlopen.__self__.handlers))

    def test_admin_key_never_replays_get_or_mutating_rpc_on_redirect(self):
        for secret, expected_bearer in (
            (OPAQUE_KEY, None), (LEGACY_KEY, "Bearer " + LEGACY_KEY)
        ):
            for method, path, data in (
                ("GET", "campaigns", None),
                ("POST", "rpc/claim_campaign_job", {"p_id": "synthetic"}),
            ):
                for status in (301, 302, 303, 307, 308):
                    with self.subTest(method=method, status=status,
                                      key_class="opaque" if secret == OPAQUE_KEY else "legacy"):
                        redirect = SyntheticRedirectHTTPS(status)
                        opener = build_opener(ProxyHandler({}),
                                              admin_store._DenyRedirects(), redirect)
                        with patch.object(admin_store, "urlopen", opener.open):
                            store = admin_store.AdminStore(ORIGIN, secret)
                            with self.assertRaises(StorageUnavailable) as error:
                                store.request(path, method=method, data=data)
                        self.assertEqual(redirect.sent, [(
                            ORIGIN + "/rest/v1/" + path, method, secret,
                            expected_bearer
                        )])
                        self.assertEqual(len(redirect.responses), 1)
                        self.assertTrue(redirect.responses[0].closed)
                        self.assertNotIn(secret, str(error.exception))

    def test_worker_rejects_untrusted_initial_origin_before_secret_use(self):
        bad = (
            "", "http://synthetic-p0249.supabase.co", "https://",
            "https://admin:pass@synthetic-p0249.supabase.co",
            "https://synthetic-p0249.supabase.co/rest/v1",
            "https://synthetic-p0249.supabase.co/?key=leak",
            "https://synthetic-p0249.supabase.co/#fragment",
            "https://synthetic-p0249.supabase.co?",
            "https://synthetic-p0249.supabase.co:bad",
            "https://[not-an-ipv6", "https://synthetic-p0249.supabase.co\\\\@evil.invalid",
            "https://synthetic-p0249.supabase.co\nX-Key: secret",
            None, 42,
        )
        for origin in bad:
            with self.subTest(origin=repr(origin)), self.assertRaises(ValueError):
                admin_store.AdminStore(origin, OPAQUE_KEY)
        for valid in (ORIGIN, ORIGIN + "/", ORIGIN + ":443"):
            self.assertEqual(admin_store.AdminStore(valid, OPAQUE_KEY).origin,
                             valid.rstrip("/"))
        for secret in ("", None, 3):
            with self.subTest(secret=repr(secret)), self.assertRaises(ValueError):
                admin_store.AdminStore(ORIGIN, secret)

    def test_injected_worker_transport_preserves_bounded_original_rpc(self):
        calls = []

        def fixture(req, timeout):
            calls.append((req.full_url, req.get_method(), timeout,
                          req.get_header("Apikey")))
            return JSONResponse()

        store = admin_store.AdminStore(ORIGIN, OPAQUE_KEY, transport=fixture)
        self.assertEqual(store.request("campaigns"), [])
        self.assertEqual(calls, [
            (ORIGIN + "/rest/v1/campaigns", "GET", 10, OPAQUE_KEY)
        ])

    def test_quota_and_auth_http_errors_are_closed_without_exposing_keys(self):
        for code, body, exception in (
            (401, b'{"code":"PGRST301"}', StorageUnavailable),
            (403, b'{"code":"PGRST301"}', StorageUnavailable),
            (402, b'{"code":"RG001"}', SubscriptionDenied),
        ):
            with self.subTest(code=code):
                handles = []

                def denied(req, timeout):
                    response = HTTPError(
                        req.full_url, code, "synthetic failure",
                        Message(), io.BytesIO(body)
                    )
                    handles.append(response)
                    raise response

                store = admin_store.AdminStore(ORIGIN, OPAQUE_KEY,
                                               transport=denied)
                with self.assertRaises(exception) as error:
                    store.request("campaigns")
                self.assertTrue(handles[0].closed)
                self.assertNotIn(OPAQUE_KEY, str(error.exception))


if __name__ == "__main__":
    unittest.main()
