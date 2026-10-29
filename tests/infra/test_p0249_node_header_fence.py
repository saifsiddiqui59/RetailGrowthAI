"""Issue #249: untrusted Node canary headers never carry browser/service identity.

Only extract the pure helper AST. Never import the live DEV canary or access
GitHub Secrets, Supabase, an Azure endpoint, or an operator ROOT session.
"""
import ast
import re
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
