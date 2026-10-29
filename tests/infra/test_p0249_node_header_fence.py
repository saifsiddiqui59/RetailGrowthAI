"""Issue #249: untrusted Node canary headers never carry browser/service identity.

Only extract the pure helper AST. Never import the live DEV canary or access
GitHub Secrets, Supabase, an Azure endpoint, or an operator ROOT session.
"""
import ast
import io
import json
import re
import time
import urllib.error
import urllib.request
import unittest
from pathlib import Path

TARGET = Path(__file__).resolve().parents[2] / "tests/e2e/p0249_dev_node_full_canary_once.py"


def _headers():
    tree = ast.parse(TARGET.read_text())
    helper = next(n for n in tree.body if isinstance(n, ast.FunctionDef)
                  and n.name == "node_preview_headers")
    namespace = {"re": re}
    exec(compile(ast.Module(body=[helper], type_ignores=[]), str(TARGET), "exec"),
         namespace)
    return namespace["node_preview_headers"]


class NodePreviewHeaderFence(unittest.TestCase):
    def test_only_one_signed_user_token_forwards_with_safe_headers(self):
        headers = _headers()({
            "Authorization": "Bearer eyJhbGciOi.test_-part.signature_123",
            "apikey": "sb_publishable_example_never_forward",
            "Accept": "application/json",
            "Content-Type": "application/json",
            "Prefer": "return=representation",
        })
        self.assertEqual(headers, {
            "accept": "application/json",
            "content-type": "application/json",
            "prefer": "return=representation",
            "x-rgai-supabase-jwt": "eyJhbGciOi.test_-part.signature_123",
        })
        self.assertNotIn("authorization", headers)
        self.assertNotIn("apikey", headers)

    def test_disallow_all_conflicting_node_or_browser_identity_headers(self):
        cases = (
            {"x-rgai-supabase-jwt": "attacker.value.here"},
            {"X-RGAI-SUPABASE-JWT": "attacker.value.here"},
            {"Cookie": "session=stolen"},
            {"Proxy-Authorization": "Bearer proxy"},
            {"x-functions-key": "internal"},
            {"X-MS-CLIENT-PRINCIPAL": "fake"},
            {"Origin": "https://attacker.example"},
            {"Referer": "https://attacker.example"},
            {"Host": "attacker.example"},
            {"X-Forwarded-Host": "attacker.example"},
            {"Set-Cookie": "a=b"},
        )
        for bad in cases:
            with self.subTest(bad=tuple(bad)):
                with self.assertRaisesRegex(RuntimeError, "UNREVIEWED_NODE_HEADER"):
                    _headers()({"Authorization": "Bearer a.b.c", **bad})

    def test_require_one_actual_jwt_shaped_user_bearer(self):
        cases = (
            {}, {"Authorization": ""}, {"Authorization": "Basic a.b.c"},
            {"Authorization": "Bearer "}, {"Authorization": "Bearer sb_secret_example"},
            {"Authorization": "Bearer a..c"},
            {"Authorization": "Bearer a.b.c."},
            {"Authorization": "Bearer a.b.c$"},
            {"Authorization": "Bearer " + "a" * 8193 + ".b.c"},
            {"Authorization": "Bearer a.b.c", "authorization": "Bearer d.e.f"},
        )
        for bad in cases:
            with self.subTest(bad_keys=tuple(bad)):
                with self.assertRaises(RuntimeError):
                    _headers()(bad)

    def test_header_smuggling_and_case_collisions_fail_closed(self):
        cases = (
            {"Authorization": "Bearer a.b.c\r\nCookie: forged"},
            {"Authorization": "Bearer a.b.c", "Accept": "text/plain\nUnsafe"},
            {"Authorization": "Bearer a.b.c", "Accept": "application/json",
             "accept": "text/plain"},
            {"Authorization": "Bearer a.b.c", "a\r\nb": "x"},
            {"Authorization": "Bearer a.b.c", "apikey": None},
            {"Authorization": "Bearer a.b.c", "x-request-id": "unsafe-caller"},
        )
        for bad in cases:
            with self.subTest(bad_keys=tuple(bad)):
                with self.assertRaises(RuntimeError):
                    _headers()(bad)


    def test_standard_library_redirect_handler_denies_all_redirects(self):
        source = ast.parse(TARGET.read_text())
        cls = next(n for n in source.body if isinstance(n, ast.ClassDef)
                   and n.name == "_NodeNeverRedirect")
        namespace = {"urllib": urllib}
        exec(compile(ast.Module(body=[cls], type_ignores=[]), str(TARGET), "exec"),
             namespace)
        handler = namespace["_NodeNeverRedirect"]()
        self.assertIsNone(handler.redirect_request(
            None, None, 302, "Found",
            {"Location": "https://attacker.example"}, "https://attacker.example"))
        self.assertIsNone(handler.redirect_request(
            None, None, 307, "Temporary Redirect",
            {"Location": "https://attacker.example"}, "https://attacker.example"))

    def test_node_transport_never_replays_mutations_or_follows_redirect(self):
        source = ast.parse(TARGET.read_text())
        fn = next(n for n in source.body if isinstance(n, ast.FunctionDef)
                  and n.name == "_call_node_preview")
        url = ("https://purple-dune-06b5da200-p0249writes."
               "eastasia.2.azurestaticapps.net/api/campaigns")
        header = {"x-rgai-supabase-jwt": "a.b.c"}
        actions = []

        class FakeResponse:
            status = 202
            def __init__(self, payload=b'{"status":"PLANNING"}'):
                self.payload = payload
            def read(self, count):
                return self.payload[:count]
            def __enter__(self):
                return self
            def __exit__(self, *args):
                return False

        class Opener:
            def __init__(self, results):
                self.results = iter(results)
            def open(self, req, timeout):
                actions.append((req.full_url, req.get_method(),
                                req.headers.get("X-rgai-supabase-jwt")))
                item = next(self.results)
                if isinstance(item, BaseException):
                    raise item
                return item

        def invoke(items, method="POST", expected=(202,)):
            namespace = {
                "json": json, "urllib": urllib, "time": time,
                "NODE_PREVIEW": url[:-len("/api/campaigns")],
                "_NODE_OPENER": Opener(items),
            }
            exec(compile(ast.Module(body=[fn], type_ignores=[]),
                         str(TARGET), "exec"), namespace)
            return namespace["_call_node_preview"](
                url, method=method, payload={} if method=="POST" else None,
                headers=header, timeout=30, expect=expected)

        self.assertEqual(invoke([FakeResponse()]),
                         (202, {"status": "PLANNING"}))
        self.assertEqual(len(actions), 1)
        self.assertEqual(actions[0][2], "a.b.c")
        actions.clear()
        redirect = urllib.error.HTTPError(
            url, 307, "Temporary Redirect",
            {"Location": "https://attacker.example"}, io.BytesIO(b""))
        with self.assertRaisesRegex(RuntimeError, "REDIRECT_DENIED"):
            invoke([redirect])
        self.assertEqual(len(actions), 1)
        actions.clear()
        transient = urllib.error.HTTPError(
            url, 503, "Unavailable", {}, io.BytesIO(b""))
        with self.assertRaisesRegex(RuntimeError, "TRANSACTION_UNCONFIRMED"):
            invoke([transient])
        self.assertEqual(len(actions), 1)
        actions.clear()
        with self.assertRaisesRegex(RuntimeError, "TRANSACTION_UNCONFIRMED"):
            invoke([TimeoutError("failed")])
        self.assertEqual(len(actions), 1)

    def test_pure_source_integration_keeps_dev_and_mutation_safety(self):
        source = TARGET.read_text()
        self.assertIn("original=node_preview_headers(headers or {})", source)
        self.assertIn("is_node=url.startswith(NODE_PREVIEW+\"/api/\")", source)
        self.assertIn("P0249_REAL_NODE_HTTP_TRANSACTION_UNCONFIRMED", source)
        self.assertIn("RGAI_DEV_CANARY_APPROVAL", source)
        self.assertNotIn("sb_secret_", source)
        self.assertNotIn("WineShopPOS", source.split("def node_preview_headers", 1)[1])


if __name__ == "__main__":
    unittest.main()
