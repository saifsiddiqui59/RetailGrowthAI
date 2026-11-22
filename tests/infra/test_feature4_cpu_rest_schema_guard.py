"""Offline negative checks for the protected DEV Supabase REST schema proof."""
import importlib.util
from pathlib import Path
from unittest.mock import patch
import unittest

SCRIPT = Path(__file__).resolve().parents[2] / "scripts/deploy/feature4_cpu_rest_schema_guard.py"
spec = importlib.util.spec_from_file_location("f4_rest_schema_guard", SCRIPT)
guard = importlib.util.module_from_spec(spec)
spec.loader.exec_module(guard)


class FakeResponse:
    def __init__(self, body, status=200):
        self.body = body
        self.status = status
    def read(self, limit):
        return self.body[:limit]
    def __enter__(self):
        return self
    def __exit__(self, *args):
        return False


class Feature4RestProofTests(unittest.TestCase):
    def test_exact_host_public_tables_and_nonmutating_service_role_claim(self):
        calls = []
        def opener(request, timeout):
            calls.append((request.full_url, request.get_method(), request.data,
                          request.get_header("Apikey")))
            assert timeout == 25
            if request.full_url.endswith("/rpc/feature4_claim_cpu_render"):
                return FakeResponse(b"null")
            return FakeResponse(b"[]")
        self.assertTrue(guard.verify("sb_secret_" + "x" * 32, opener=opener))
        self.assertEqual(len(calls), 3)
        self.assertTrue(all(u.startswith("https://jeearzffnjbvghwjjjrf.supabase.co/rest/v1/")
                            for u, *_ in calls))
        self.assertEqual([m for _, m, *_ in calls], ["GET", "GET", "POST"])
        self.assertEqual(calls[-1][2], b'{"p_id":null}')
        self.assertTrue(all(x[3].startswith("sb_secret_") for x in calls))

    def test_no_role_bypass_or_unsupported_secret(self):
        for key in ("", "bad", "eyJx.notjwt", "sb_secret_"):
            with self.subTest(key=key):
                with self.assertRaises(guard.GuardDenied):
                    guard.verify(key, opener=lambda *_args, **_kwargs: FakeResponse(b"[]"))

    def test_zero_length_and_foreign_response_denied(self):
        for payload in (b'{"id":"customer"}', b'[{"id":123}]', b"", b"null"):
            with self.subTest(payload=payload):
                with self.assertRaises(guard.GuardDenied):
                    guard.verify("sb_secret_" + "z" * 20,
                                 opener=lambda *a, **k: FakeResponse(payload))
        with self.assertRaises(guard.GuardDenied):
            guard.verify("sb_secret_" + "z"*20,
                         opener=lambda *a, **k: FakeResponse(b"[]", status=403))

    def test_service_rpc_requires_null_denial_and_live_success(self):
        def opener(request, timeout):
            if request.get_method() == "POST":
                return FakeResponse(b'{"job_id":"fake"}')
            return FakeResponse(b"[]")
        with self.assertRaises(guard.GuardDenied):
            guard.verify("sb_secret_" + "z"*20, opener=opener)

    def test_workflow_only_falls_back_after_failed_live_db_and_keeps_azure_gate(self):
        wf = (SCRIPT.parents[2]/".github/workflows/retail-dev-feature4-cpu-queues-once.yml").read_text()
        self.assertIn("if result=\"$(timeout 35s psql", wf)
        self.assertIn("test \"$result\" = t", wf)
        self.assertIn("scripts/deploy/feature4_cpu_rest_schema_guard.py", wf)
        self.assertIn("secrets.RETAIL_SUPABASE_SERVICE_ROLE_KEY", wf)
        self.assertIn("environment: dev", wf)
        self.assertIn("feature4_cpu_dev_queues.py --apply", wf)
        self.assertNotIn("AZURE_STORAGE_KEY:", wf)


if __name__ == "__main__":
    unittest.main()
