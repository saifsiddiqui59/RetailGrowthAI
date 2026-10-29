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

    def test_parallel_fresh_canaries_fail_closed_before_any_approval(self):
        a = "rgai-canary-47c4fd8f5eb5-a@example.invalid"
        b = "rgai-canary-47c4fd8f5eb5-b@example.invalid"
        other_a = "rgai-canary-deadbeefdead-a@example.invalid"
        self.assertIsNone(MOD.choose_pending_candidate(set(), set(), set(), None))
        self.assertEqual(MOD.choose_pending_candidate({a, b}, set(), set(), None), a)
        with self.assertRaisesRegex(RuntimeError, "Multiple fresh canary runs"):
            MOD.choose_pending_candidate({a, other_a}, set(), set(), None)
        self.assertEqual(
            MOD.choose_pending_candidate({b, other_a}, set(), {a}, "47c4fd8f5eb5"),
            b,
        )
        self.assertIsNone(
            MOD.choose_pending_candidate({a, other_a}, {a}, set(), "47c4fd8f5eb5"))

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

    def test_both_queue_buttons_bind_to_their_own_new_request_and_render(self):
        """Regression: opening the queue can leave an older GET in flight."""
        target = "rgai-canary-012345abcdef-a@example.invalid"
        target_id = "123e4567-e89b-42d3-a456-426614174000"
        url = "https://jeearzffnjbvghwjjjrf.supabase.co/rest/v1/rpc/retail_platform_onboarding_requests"
        for button, operation in [("Review requests", MOD.open_pending_queue),
                                  ("Refresh queue", MOD.refresh_pending)]:
            with self.subTest(button=button):
                calls = []

                class Page:
                    def expect_request(self, predicate, *, timeout):
                        calls.append(("expect-request", timeout))
                        request = SimpleNamespace(url=url, method="POST")
                        assert predicate(request)
                        reply = SimpleNamespace(url=url, request=request, ok=True,
                                                json=lambda: [{"email": target, "user_id": target_id}])
                        def own_response():
                            calls.append(("own-response", None))
                            return reply
                        request.response = own_response
                        class Waiter:
                            value = request
                            def __enter__(self): return self
                            def __exit__(self, *_): return False
                        return Waiter()
                    def get_by_role(self, role, *, name):
                        assert (role, name) == ("button", button)
                        return SimpleNamespace(click=lambda: calls.append(("click", name)))
                    def get_by_text(self, text, *, exact):
                        assert text == "Loading pending retailer requests…" and exact
                        return SimpleNamespace(wait_for=lambda **k: calls.append(("hidden", k["state"])))
                    def wait_for_function(self, js, *, arg, timeout):
                        assert "shown.every((email, index) => email === expected[index])" in js
                        assert "platform-review-item strong" in js
                        assert 'role="alert"' in js
                        assert arg == [target] and timeout == 15_000
                        calls.append(("fence", tuple(arg)))
                    def locator(self, selector):
                        assert selector == ".platform-review-item strong"
                        assert ("own-response", None) in calls
                        assert ("fence", (target,)) in calls
                        calls.append(("rows", None))
                        return SimpleNamespace(all_inner_texts=lambda: [target])

                self.assertEqual(operation(Page()), {target: target_id})
                self.assertEqual([x[0] for x in calls],
                                 ["expect-request", "click", "own-response",
                                  "hidden", "fence", "rows"])

    def test_request_predicate_and_failed_own_reply_fail_closed(self):
        url = "https://jeearzffnjbvghwjjjrf.supabase.co/rest/v1/rpc/retail_platform_onboarding_requests"
        request = SimpleNamespace(url=url, method="POST")
        reply = SimpleNamespace(url=url, request=request, ok=False)
        self.assertTrue(MOD.is_onboarding_queue_request(request))
        self.assertTrue(MOD.is_onboarding_queue_reply(reply))
        for path, method in [
            ("https://evil.example.invalid/rest/v1/rpc/retail_platform_onboarding_requests", "POST"),
            ("http://jeearzffnjbvghwjjjrf.supabase.co/rest/v1/rpc/retail_platform_onboarding_requests", "POST"),
            ("https://jeearzffnjbvghwjjjrf.supabase.co/rest/v1/rpc/retail_platform_review_onboarding", "POST"),
            (url, "GET"),
        ]:
            with self.subTest(path=path, method=method):
                other = SimpleNamespace(url=path, method=method)
                self.assertFalse(MOD.is_onboarding_queue_request(other))
                self.assertFalse(MOD.is_onboarding_queue_reply(
                    SimpleNamespace(url=path, request=other)))
        for failed_response in (None, reply, SimpleNamespace(
            url="https://evil.example.invalid", request=request, ok=True)):
            with self.subTest(response=repr(failed_response)):
                request.response = lambda: failed_response
                class Page:
                    def expect_request(self, predicate, *, timeout):
                        assert predicate(request)
                        class Waiter:
                            value = request
                            def __enter__(self): return self
                            def __exit__(self, *_): return False
                        return Waiter()
                    def get_by_role(self, *_args, **_kwargs):
                        return SimpleNamespace(click=lambda: None)
                    def get_by_text(self, *_args, **_kwargs):
                        raise AssertionError("No DOM read after failed own response")
                with self.assertRaisesRegex(RuntimeError, "HTTP request failed"):
                    MOD.refresh_pending(Page())

    def test_refresh_denies_malformed_queue_response_before_dom_read(self):
        url = "https://jeearzffnjbvghwjjjrf.supabase.co/rest/v1/rpc/retail_platform_onboarding_requests"
        class Page:
            def __init__(self, payload): self.payload = payload
            def expect_request(self, predicate, *, timeout):
                request = SimpleNamespace(url=url, method="POST")
                reply = SimpleNamespace(url=url, request=request, ok=True,
                                        json=lambda: self.payload)
                request.response = lambda: reply
                assert predicate(request)
                class Waiter:
                    value = request
                    def __enter__(self): return self
                    def __exit__(self, *_): return False
                return Waiter()
            def get_by_role(self, *_args, **_kwargs):
                return SimpleNamespace(click=lambda: None)
            def get_by_text(self, *_args, **_kwargs):
                raise AssertionError("No DOM read after invalid RPC body")
            def wait_for_function(self, *_args, **_kwargs):
                raise AssertionError("No DOM wait after invalid RPC body")
        for payload in [{}, "text", [{"email": ""}], [{"email": 19}],
                        [{"email": "same"}, {"email": "same"}], [{}],
                        [{"email": "valid"}] * 41,
                        [{"email": "x", "user_id": "not-uuid"}],
                        [{"email": "x", "user_id": 4}],
                        [{"email": "x", "user_id": "123e4567-e89b-12d3-a456-426614174000"}],
                        [{"email": "a", "user_id": "123e4567-e89b-42d3-a456-426614174000"},
                         {"email": "b", "user_id": "123e4567-e89b-42d3-a456-426614174000"}]]:
            with self.subTest(payload=payload):
                with self.assertRaisesRegex(RuntimeError, "queue"):
                    MOD.refresh_pending(Page(payload))

    def test_audited_root_approval_requires_exact_request_body_and_own_ack(self):
        path = "https://jeearzffnjbvghwjjjrf.supabase.co/rest/v1/rpc/retail_platform_review_onboarding"
        user_id = "123e4567-e89b-42d3-a456-426614174000"
        body = {"p_user_id": user_id, "p_approve": True,
                "p_reason": MOD.DECISION_REASON}
        req = SimpleNamespace(url=path, method="POST", post_data_json=body)
        reply = SimpleNamespace(request=req, ok=True)
        req.response = lambda: reply
        self.assertTrue(MOD.is_onboarding_approval_request(req))
        self.assertIs(MOD.verified_approval_reply(req, user_id), reply)
        with self.assertRaisesRegex(RuntimeError, "mismatch"):
            MOD.verified_approval_reply(req, "223e4567-e89b-42d3-a456-426614174000")
        for bad in [
            dict(body, p_approve=False),
            dict(body, p_reason="wrong audit reason"),
            dict(body, p_user_id="not-a-uuid"),
            dict(body, p_user_id="123e4567-e89b-12d3-a456-426614174000"),
            dict(body, extra="unapproved"),
            {"p_approve": True},
            None,
        ]:
            req.post_data_json = bad
            with self.subTest(body=repr(bad)):
                with self.assertRaisesRegex(RuntimeError, "mismatch"):
                    MOD.verified_approval_reply(req, user_id)
        req.post_data_json = body
        for bad in [None, SimpleNamespace(request=req, ok=False),
                    SimpleNamespace(request=SimpleNamespace(), ok=True)]:
            req.response = lambda: bad
            with self.subTest(response=repr(bad)):
                with self.assertRaisesRegex(RuntimeError, "uncertain"):
                    MOD.verified_approval_reply(req, user_id)
        for url, method in [(path.replace("supabase.co", "evil.invalid"), "POST"),
                            (path, "GET"),
                            (path.replace("review_onboarding", "onboarding_requests"), "POST")]:
            req.url, req.method = url, method
            self.assertFalse(MOD.is_onboarding_approval_request(req))
            with self.assertRaisesRegex(RuntimeError, "Wrong ROOT decision"):
                MOD.verified_approval_reply(req, user_id)

    def test_ui_approval_waits_for_bound_http_ack_before_considering_row_done(self):
        path = "https://jeearzffnjbvghwjjjrf.supabase.co/rest/v1/rpc/retail_platform_review_onboarding"
        user_id = "123e4567-e89b-42d3-a456-426614174000"
        email = "rgai-canary-012345abcdef-a@example.invalid"
        calls = []
        request = SimpleNamespace(
            url=path, method="POST",
            post_data_json={"p_user_id": user_id, "p_approve": True,
                            "p_reason": MOD.DECISION_REASON})
        response = SimpleNamespace(request=request, ok=True)
        def own_reply():
            calls.append("ack")
            return response
        request.response = own_reply

        class FakeRow:
            def __init__(self, texts): self.texts = texts
            def filter(self, *, has):
                calls.append("filter")
                return self
            def count(self): return 1
            def locator(self, name):
                assert name == "strong"
                return SimpleNamespace(inner_text=lambda: email)
            def get_by_role(self, role, *, name, **kwargs):
                if role == "checkbox":
                    assert name == "I verified this account request and authorize the decision."
                    return SimpleNamespace(check=lambda: calls.append("check"))
                assert role == "button"
                return SimpleNamespace(click=lambda: calls.append("click-"+name))
            def get_by_label(self, name):
                return SimpleNamespace(fill=lambda value: calls.append("fill"),
                                       check=lambda: calls.append("check"))
            def wait_for(self, *, state, timeout):
                assert state == "detached" and timeout == 15_000
                assert "ack" in calls
                calls.append("detach")

        class Page:
            def locator(self, name, **kwargs):
                if name == "strong":
                    return SimpleNamespace()
                assert name == ".platform-review-item"
                return FakeRow([])
            def expect_request(self, predicate, *, timeout):
                assert timeout == 15_000 and predicate(request)
                calls.append("expect")
                class Waiter:
                    value = request
                    def __enter__(self): return self
                    def __exit__(self, *_): return False
                return Waiter()
            def get_by_text(self, value, *, exact):
                assert (value, exact) == ("Retailer onboarding approved.", True)
                return SimpleNamespace(count=lambda: 1)

        MOD.approve_exact_row(Page(), email, user_id)
        self.assertLess(calls.index("ack"), calls.index("detach"))
        self.assertEqual(calls.count("click-Approve"), 1)

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
