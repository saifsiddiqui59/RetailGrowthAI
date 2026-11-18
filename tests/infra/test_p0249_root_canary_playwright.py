"""Offline regression tests for optional local ROOT Playwright canary approval helper.

Pure Python only: no browser, real credentials, Supabase, HTTP or cloud writes.
"""
import ast
import importlib.util
from pathlib import Path
import unittest
from unittest.mock import patch
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[2]
TARGET = ROOT / "scripts/ops/p0249_root_canary_playwright.py"
SPEC = importlib.util.spec_from_file_location("p0249_root_canary_playwright", TARGET)
MOD = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MOD)


class CanaryOperatorSelection(unittest.TestCase):
    def test_only_new_two_shop_example_invalid_marker_allowed(self):
        good_a = "rgai-canary-47c4fd8f5eb5-a@example.invalid"
        good_b = "rgai-canary-47c4fd8f5eb5-b@example.invalid"
        self.assertTrue(MOD.eligible_canary(good_a, set(), None))
        self.assertFalse(MOD.eligible_canary(good_b, set(), None))  # A first
        self.assertFalse(MOD.eligible_canary(good_a, {good_a}, None))
        self.assertTrue(MOD.eligible_canary(good_b, {good_a}, "47c4fd8f5eb5"))
        for rejected in [
            "retailer@gmail.com",
            "rgai-canary-47c4fd8f5eb5-a@gmail.com",
            "rgai-canary-47c4fd8f5eb5-c@example.invalid",
            "rgai-canary-47c4fd8f5eb5-aa@example.invalid",
            "rgai-canary-47c4fd8f5eb5-a@example.invalid.evil",
            "rgai-canary-47c4fd8f5eb5-b@example.invalid",
            "rgai-canary-47c4fd8f5eb5-a@example.INVALID",
            "rgai-canary-deadbeefdead-b@example.invalid",
        ]:
            with self.subTest(email=rejected):
                self.assertFalse(MOD.eligible_canary(rejected, set(), None))
        self.assertFalse(MOD.eligible_canary(good_a, set(), "47c4fd8f5eb5"))
        self.assertFalse(MOD.eligible_canary("rgai-canary-deadbeefdead-b@example.invalid",
                                            set(), "47c4fd8f5eb5"))

    def test_source_denies_db_bypass_and_embedded_credentials(self):
        source = TARGET.read_text(encoding="utf-8")
        ast.parse(source)
        self.assertIn("getpass.getpass(", source)
        self.assertIn('parser.add_argument("--approve-test-only"', source)
        self.assertIn('login.click()', source)
        self.assertIn('name="Approve", exact=True', source)
        self.assertIn("matching.wait_for(state=\"detached\"", source)
        for prohibited in ("sb_secret_", "service_role", "SUPABASE_SERVICE_ROLE_KEY",
                           "execute_sql", "Authorization: Bearer", "sami9049@gmail.com",
                           "Ppp#2020"):
            self.assertNotIn(prohibited, source)

    def test_refresh_waits_for_real_root_rpc_before_reading_new_rows(self):
        """Regression: a React loading-hidden check alone can read old rows."""
        target = "rgai-canary-012345abcdef-a@example.invalid"
        calls = []

        class FakePage:
            def expect_response(self, predicate, *, timeout):
                calls.append(("expect", timeout))
                reply = SimpleNamespace(
                    url="https://jeearzffnjbvghwjjjrf.supabase.co/rest/v1/rpc/retail_platform_onboarding_requests",
                    request=SimpleNamespace(method="POST"), ok=True)
                assert predicate(reply)
                class Waiter:
                    value = reply
                    def __enter__(self):
                        return self
                    def __exit__(self, *_):
                        calls.append(("response", "ok"))
                return Waiter()

            def get_by_role(self, role, *, name):
                assert (role, name) == ("button", "Refresh queue")
                return SimpleNamespace(click=lambda: calls.append(("click", None)))

            def get_by_text(self, text, *, exact):
                assert text == "Loading pending retailer requests…"
                assert exact
                return SimpleNamespace(wait_for=lambda **k: calls.append(("hidden", k["state"])))

            def wait_for_timeout(self, ms):
                calls.append(("render", ms))

            def locator(self, selector):
                if selector == ".platform-approvals [role='alert']":
                    return SimpleNamespace(count=lambda: 0)
                assert selector == ".platform-review-item strong"
                # Reading the newly created row BEFORE response finished is
                # the regression: the old list must never be accepted.
                assert ("response", "ok") in calls
                assert ("render", 100) in calls
                calls.append(("rows", None))
                return SimpleNamespace(all_inner_texts=lambda: [target])

        self.assertEqual(MOD.refresh_pending(FakePage()), {target})
        self.assertEqual([entry[0] for entry in calls],
                         ["expect", "click", "response", "hidden", "render", "rows"])

    def test_refresh_denies_failed_rpc_and_wrong_route_or_method(self):
        reply = SimpleNamespace(
            url="https://jeearzffnjbvghwjjjrf.supabase.co/rest/v1/rpc/retail_platform_onboarding_requests",
            request=SimpleNamespace(method="POST"), ok=False)
        self.assertTrue(MOD.is_onboarding_queue_reply(reply))
        for path, method in [
            ("https://evil.example.invalid/rest/v1/rpc/retail_platform_onboarding_requests", "POST"),
            ("http://jeearzffnjbvghwjjjrf.supabase.co/rest/v1/rpc/retail_platform_onboarding_requests", "POST"),
            ("https://jeearzffnjbvghwjjjrf.supabase.co/rest/v1/rpc/retail_platform_review_onboarding", "POST"),
            (reply.url, "GET"),
        ]:
            with self.subTest(path=path, method=method):
                self.assertFalse(MOD.is_onboarding_queue_reply(
                    SimpleNamespace(url=path, request=SimpleNamespace(method=method))))
        class Page:
            def expect_response(self, predicate, *, timeout):
                assert predicate(reply)
                class Waiter:
                    value = reply
                    def __enter__(self):
                        return self
                    def __exit__(self, *_):
                        return False
                return Waiter()
            def get_by_role(self, role, *, name):
                return SimpleNamespace(click=lambda: None)
            def get_by_text(self, *_args, **_kwargs):
                raise AssertionError("No DOM read after bad HTTP response")
        with self.assertRaisesRegex(RuntimeError, "HTTP request failed"):
            MOD.refresh_pending(Page())

    def test_dispatch_only_uses_existing_gh_auth_and_protected_choice(self):
        with patch.object(MOD.subprocess, "run") as run:
            MOD.dispatch_owner_approved_dev_canary()
        args = run.call_args.args[0]
        self.assertEqual(args[:3], ["gh", "workflow", "run"])
        self.assertIn("retail-dev-test-accounts-canary-once.yml", args)
        self.assertIn("approval_code=AUTHORIZED_RETAILGROWTHAI_DEV_ONLY", args)
        self.assertIn("mode=node-poster-reel", args)
        self.assertEqual(args[args.index("--ref") + 1], "main")
        self.assertIs(run.call_args.kwargs["capture_output"], True)
        self.assertIs(run.call_args.kwargs["check"], True)
        self.assertNotIn("sami9049@gmail.com", repr(args))
        self.assertNotIn("Ppp#2020", repr(args))

    def test_missing_opt_in_fails_before_password_or_import(self):
        with self.assertRaises(SystemExit) as error:
            MOD.main([])
        self.assertEqual(error.exception.code, 2)

    def test_password_or_email_never_required_by_import(self):
        # The script is importable in normal offline CI; Playwright and the
        # ROOT credentials are requested only after the explicit CLI opt-in.
        self.assertEqual(MOD.DEV_ORIGIN,
                         "https://purple-dune-06b5da200.2.azurestaticapps.net")
        self.assertEqual(MOD.DECISION_REASON.startswith("Owner-authorized"), True)


if __name__ == "__main__":
    unittest.main()
