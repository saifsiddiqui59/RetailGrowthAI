"""Offline source tests for real signed DEV Y1 Auth-only test and cleanup."""
import importlib.util
import io
from email.message import Message
import urllib.error
import urllib.request
import urllib.response
import os
from pathlib import Path
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "tests/e2e/p0249_y1_signed_auth_shadow_once.py"
spec = importlib.util.spec_from_file_location("p0249_y1_real_auth_testee", SCRIPT)
trial = importlib.util.module_from_spec(spec)
spec.loader.exec_module(trial)


class RealSignedY1SafetyTests(unittest.TestCase):
    def setUp(self):
        env = patch.dict(os.environ, {
            "RGAI_DEV_P0249_JWT_CANARY_APPROVAL": "OWNER_APPROVED_READ_ONLY_JWT_TEST",
            "RGAI_DEV_SERVICE_KEY": "sb_secret_" + "x" * 54,
            "RGAI_DEV_P0249_PUBLISHABLE_KEY": trial.helper.PUBLIC,
            "GITHUB_RUN_ID": "123456789",
            "GITHUB_RUN_ATTEMPT": "1",
        })
        env.start()
        self.addCleanup(env.stop)

    def test_http_redirect_refused_for_signed_dev_requests(self):
        """The initial trusted-origin request never follows a Location header."""
        sent_to = []

        class RedirectingHTTPS(urllib.request.HTTPSHandler):
            def https_open(self, request):
                sent_to.append(request.full_url)
                headers = Message()
                headers["Location"] = "https://example.invalid/redirect"
                response = urllib.response.addinfourl(
                    io.BytesIO(b""), headers, request.full_url, 302)
                response.msg = "Found"
                return response

        opener = urllib.request.build_opener(
            trial.helper._BlockRedirects(), RedirectingHTTPS())
        with patch.object(trial.helper, "NO_REDIRECT_OPENER", opener), \
             self.assertRaisesRegex(RuntimeError, "DEV_TEST_UNEXPECTED_HTTP_302"):
            trial.helper.request(
                trial.helper.SUPABASE + "/auth/v1/admin/users",
                headers={"apikey": "synthetic-only"})
        self.assertEqual(sent_to, [trial.helper.SUPABASE + "/auth/v1/admin/users"])
        sent_to.clear()
        with patch.object(trial.helper, "NO_REDIRECT_OPENER", opener):
            status, marker, payload, elapsed = trial.y1_read("synthetic.jwt.test")
        self.assertEqual(status, 302)
        self.assertFalse(marker)
        self.assertEqual(sent_to, [trial.Y1 + "/api/campaigns/" + trial.CAMPAIGN])
        self.assertIn("helper.NO_REDIRECT_OPENER.open", SCRIPT.read_text())

    def test_signed_y1_and_admin_denials_release_http_handles(self):
        headers = Message()
        headers["X-Request-ID"] = "test-only"
        packet = io.BytesIO(b'{"error":"UNAUTHORIZED"}')
        denied = urllib.error.HTTPError(
            trial.Y1 + "/api/campaigns/" + trial.CAMPAIGN,
            401, "Unauthorized", headers, packet)
        with patch.object(trial.helper.NO_REDIRECT_OPENER, "open",
                          side_effect=denied):
            status, marked, body, _ = trial.y1_read("synthetic")
        self.assertEqual((status, marked, body),
                         (401, True, {"error": "UNAUTHORIZED"}))
        self.assertTrue(packet.closed)

        admin_packet = io.BytesIO(b'{"error":"UNAUTHORIZED"}')
        admin_denied = urllib.error.HTTPError(
            trial.helper.SUPABASE + "/auth/v1/admin/users",
            401, "Unauthorized", Message(), admin_packet)
        with patch.object(trial.helper.NO_REDIRECT_OPENER, "open",
                          side_effect=admin_denied):
            status, body, _, _ = trial.helper.request(
                trial.helper.SUPABASE + "/auth/v1/admin/users",
                expected=(401,))
        self.assertEqual(status, 401)
        self.assertEqual(body, {"error": "UNAUTHORIZED"})
        self.assertTrue(admin_packet.closed)

    def test_fixed_y1_origin_and_no_data_mutators(self):
        self.assertEqual(trial.Y1, "https://rgai-dev-y1-p0249-d4e5ddbd.azurewebsites.net")
        code = SCRIPT.read_text()
        for denied in ("az deployment group create", "az functionapp config",
                       "INSERT INTO", "UPDATE public.", "subprocess.run"):
            self.assertNotIn(denied, code)

    def test_two_signed_users_get_only_404_and_both_cleaned(self):
        accounts = [
            ("rgai-p0249-jwt-test1", "11111111-1111-4111-8111-111111111111", "a.b.c"),
            ("rgai-p0249-jwt-test2", "22222222-2222-4222-8222-222222222222", "a.b.d"),
        ]
        def shadow_get(token):
            if token == "fake-but-wellformed-jwt" or token.endswith(".A"):
                return 401, True, {"error": "UNAUTHORIZED"}, 0.2
            return 404, True, {"error": "NOT_FOUND"}, 0.3
        with patch.object(trial, "create_test_user", side_effect=accounts) as created, \
             patch.object(trial, "y1_read", side_effect=shadow_get) as request, \
             patch.object(trial.helper, "request",
                          return_value=(200, {"keys": [{"alg": "RS256"}]}, None, 0.2)), \
             patch.object(trial.helper, "owner_only_cleanup") as cleaned, \
             patch.object(trial.time, "sleep") as idle:
            trial.main()
        self.assertEqual(created.call_count, 2)
        self.assertEqual(cleaned.call_count, 2)
        self.assertEqual(request.call_count, 11)
        idle.assert_called_once_with(240)

    def test_failed_signed_get_after_idle_still_cleans_both_users(self):
        accounts = [
            ("rgai-p0249-jwt-" + "a" * 16, "11111111-1111-4111-8111-111111111111", "a.b.c"),
            ("rgai-p0249-jwt-" + "b" * 16, "22222222-2222-4222-8222-222222222222", "a.b.d"),
        ]
        calls = [("fake-but-wellformed-jwt", 401)]
        # The ordinary pre-idle successful sequence is three 404s then a 401
        # for each of the two genuine (mocked) user tokens.
        def read(token):
            if token == "fake-but-wellformed-jwt" or token.endswith(".A"):
                return 401, True, {"error": "UNAUTHORIZED"}, 0.2
            read.user_calls += 1
            if read.user_calls == 8:
                return 503, False, None, 18.0
            return 404, True, {"error": "NOT_FOUND"}, 0.3
        read.user_calls = 0
        with patch.object(trial, "create_test_user", side_effect=accounts), \
             patch.object(trial, "y1_read", side_effect=read), \
             patch.object(trial.helper, "request",
                          return_value=(200, {"keys": [{"alg": "ES256"}]}, None, 0.2)), \
             patch.object(trial.helper, "owner_only_cleanup") as cleaned, \
             patch.object(trial.time, "sleep") as idle, \
             self.assertRaisesRegex(RuntimeError, "after 240s idle"):
            trial.main()
        self.assertEqual(cleaned.call_count, 2)
        idle.assert_called_once_with(240)

    def test_expiring_test_jwt_is_rejected_before_idle_soak_and_cleaned(self):
        uid = "11111111-1111-4111-8111-111111111111"
        email_request = None
        def request(url, **kwargs):
            nonlocal email_request
            if url.endswith("/auth/v1/admin/users"):
                email_request = kwargs["data"]["email"]
                return 201, {"id": uid, "email": email_request}, None, 0.2
            return 200, {"access_token": "a.b.c"}, None, 0.2
        with patch.object(trial.helper, "request", side_effect=request), \
             patch.object(trial.helper, "jwt_claims_for_local_shape_only",
                          return_value={"sub": uid, "exp": int(trial.time.time()) + 40}), \
             patch.object(trial.helper, "owner_only_cleanup") as cleaned, \
             self.assertRaisesRegex(RuntimeError, "expires before bounded idle soak"):
            trial.create_test_user("sb_secret_" + "x" * 42, trial.helper.PUBLIC, 0)
        cleaned.assert_called_once()
        self.assertTrue(email_request.endswith("@example.invalid"))

    def test_failed_signed_read_cleans_disposable_account(self):
        with patch.object(trial, "create_test_user", return_value=(
                "rgai-p0249-jwt-test1", "11111111-1111-4111-8111-111111111111", "a.b.c")), \
             patch.object(trial, "y1_read", side_effect=[
                 (401, True, {"error": "UNAUTHORIZED"}, 0.3),
                 (503, True, {"error": "SERVICE_NOT_CONFIGURED"}, 0.3),
             ]), \
             patch.object(trial.helper, "request",
                          return_value=(200, {"keys": [{"alg": "ES256"}]}, None, 0.2)), \
             patch.object(trial.helper, "owner_only_cleanup") as cleaned, \
             self.assertRaises(RuntimeError):
            trial.main()
        cleaned.assert_called_once()

    def test_401_without_handler_marker_denies_before_auth_creation(self):
        with patch.object(trial, "y1_read", return_value=(401, False, None, 0.3)), \
             patch.object(trial, "create_test_user",
                          side_effect=AssertionError("must not create user")), \
             self.assertRaises(RuntimeError):
            trial.main()

    def test_missing_elevated_runner_secret_denies_before_network(self):
        with patch.dict(os.environ, {"RGAI_DEV_SERVICE_KEY": ""}), \
             patch.object(trial, "y1_read",
                          side_effect=AssertionError("must not network")), \
             self.assertRaises(RuntimeError):
            trial.main()

    def test_modern_supabase_secret_admin_header_is_apikey_only(self):
        key = "sb_secret_" + "x" * 42
        self.assertEqual(trial.helper.admin_headers(key), {"apikey": key})
        self.assertNotIn("Authorization", trial.helper.admin_headers(key))
        jwt = "eyJabc.def.ghi"
        self.assertEqual(trial.helper.admin_headers(jwt),
                         {"apikey": jwt, "Authorization": "Bearer " + jwt})
        for bad in ("", "sb_publishable_not_privileged", "random-value", "eyJnot_a_jwt"):
            with self.subTest(bad=bad), self.assertRaises(RuntimeError):
                trial.helper.admin_headers(bad)

    def test_uncertain_auth_create_cleanup_reads_second_page_before_deleting(self):
        marker = trial.helper.CANARY_PREFIX + "a" * 16
        uid = "11111111-1111-4111-8111-111111111111"
        values = [
            (200, {"users": [{"email": "unrelated@example.invalid"}], "next_page": 2}, None, 0.1),
            (200, {"users": [{"email": marker + "@example.invalid", "id": uid}], "next_page": 0}, None, 0.1),
            (200, {"id": uid, "email": marker + "@example.invalid"}, None, 0.1),
            (204, {}, None, 0.1),
        ]
        with patch.object(trial.helper, "request", side_effect=values) as req:
            trial.helper.owner_only_cleanup("sb_secret_" + "x" * 42, marker, None)
        self.assertEqual(req.call_count, 4)
        self.assertIn("page=1", req.call_args_list[0].args[0])
        self.assertIn("page=2", req.call_args_list[1].args[0])
        self.assertTrue(req.call_args_list[2].args[0].endswith("/auth/v1/admin/users/" + uid))
        self.assertNotIn("method", req.call_args_list[2].kwargs)
        self.assertEqual(req.call_args_list[3].kwargs["method"], "DELETE")
        self.assertEqual(req.call_args_list[3].kwargs["headers"], {"apikey": "sb_secret_" + "x" * 42})

    def test_unknown_auth_inventory_fails_closed_without_deletion(self):
        marker = trial.helper.CANARY_PREFIX + "b" * 16
        with patch.object(trial.helper, "request", return_value=(
            200, {"users": [], "next_page": 7}, None, 0.1
        )) as req, self.assertRaises(RuntimeError):
            trial.helper.owner_only_cleanup("sb_secret_" + "x" * 42, marker, None)
        self.assertEqual(req.call_count, 1)
        self.assertNotIn("method", req.call_args.kwargs)

    def test_known_uid_delete_requires_fresh_email_and_id_match(self):
        marker = trial.helper.CANARY_PREFIX + "c" * 16
        uid = "11111111-1111-4111-8111-111111111111"
        key = "sb_secret_" + "x" * 42
        for response in (
            {"id": uid, "email": "real-user@example.com"},
            {"id": "22222222-2222-4222-8222-222222222222",
             "email": marker + "@example.invalid"},
            {"id": uid},
            {},
        ):
            with self.subTest(response=response), \
                 patch.object(trial.helper, "request", return_value=(
                     200, response, None, 0.1)) as req, \
                 self.assertRaisesRegex(RuntimeError, "UNSAFE_SYNTHETIC_AUTH_DELETE_TARGET"):
                trial.helper.owner_only_cleanup(key, marker, uid)
            self.assertEqual(req.call_count, 1)
            self.assertNotIn("method", req.call_args.kwargs)

    def test_known_uid_cleanup_must_verify_get_then_delete(self):
        marker = trial.helper.CANARY_PREFIX + "d" * 16
        uid = "11111111-1111-4111-8111-111111111111"
        fake = [(200, {"id": uid, "email": marker + "@example.invalid"}, None, 0.1),
                (204, {}, None, 0.1)]
        with patch.object(trial.helper, "request", side_effect=fake) as req:
            trial.helper.owner_only_cleanup("sb_secret_" + "x" * 42, marker, uid)
        self.assertEqual(req.call_count, 2)
        self.assertEqual(req.call_args_list[0].args[0], req.call_args_list[1].args[0])
        self.assertNotIn("method", req.call_args_list[0].kwargs)
        self.assertEqual(req.call_args_list[1].kwargs["method"], "DELETE")

    def test_non_canary_marker_never_deletes_user_even_with_known_uid(self):
        uid = "11111111-1111-4111-8111-111111111111"
        key = "sb_secret_" + "x" * 42
        for marker in ("rgai-p0249-jwt-owner", trial.helper.CANARY_PREFIX + "f" * 15,
                       trial.helper.CANARY_PREFIX + "z" * 16,
                       "different-prefix-" + "a" * 16):
            with self.subTest(marker=marker), \
                 patch.object(trial.helper, "request",
                              side_effect=AssertionError("no privileged API call")), \
                 self.assertRaisesRegex(RuntimeError, "UNSAFE_AUTH_CLEANUP_SCOPE"):
                trial.helper.owner_only_cleanup(key, marker, uid)

    def test_wrong_created_account_email_does_not_sign_in(self):
        expected = "11111111-1111-4111-8111-111111111111"
        responses = [(200, {"id": expected, "email": "someone-real@example.com"}, None, 0.1)]
        with patch.object(trial.helper, "request", side_effect=responses) as req, \
             patch.object(trial.helper, "owner_only_cleanup") as cleanup, \
             self.assertRaisesRegex(RuntimeError, "Synthetic Auth create response identity mismatch"):
            trial.create_test_user("sb_secret_" + "x" * 42, trial.helper.PUBLIC, 0)
        self.assertEqual(req.call_count, 1)
        cleanup.assert_called_once()

    def test_run_bound_fixture_identifiers_are_exact_two_and_nonreused(self):
        a, b = trial.canary_marker(0), trial.canary_marker(1)
        self.assertNotEqual(a, b)
        for label in (a, b):
            self.assertRegex(label, r"^rgai-p0249-jwt-[0-9a-f]{16}$")
        with patch.dict(os.environ, {"GITHUB_RUN_ATTEMPT": "2"}):
            self.assertNotIn(trial.canary_marker(0), (a, b))
        with patch.dict(os.environ, {"GITHUB_RUN_ID": ""}):
            with self.assertRaisesRegex(RuntimeError, "UNSAFE_RUN_BOUND_AUTH_MARKER"):
                trial.canary_marker(0)
        for slot in (-1, 2, False, "0"):
            with self.subTest(slot=slot), self.assertRaises(RuntimeError):
                trial.canary_marker(slot)

    def test_independent_reconciliation_uses_only_two_exact_run_markers(self):
        with patch.object(trial.helper, "owner_only_cleanup") as cleanup:
            trial.cleanup_only()
        self.assertEqual(cleanup.call_count, 2)
        actual = [item.args for item in cleanup.call_args_list]
        self.assertEqual(actual, [
            ("sb_secret_" + "x" * 54, trial.canary_marker(1), None),
            ("sb_secret_" + "x" * 54, trial.canary_marker(0), None),
        ])

    def test_independent_cleanup_attempts_both_if_one_fails(self):
        with patch.object(trial.helper, "owner_only_cleanup",
                          side_effect=(RuntimeError("cannot verify"), None)) as cleanup, \
             self.assertRaisesRegex(RuntimeError, "manual review"):
            trial.cleanup_only()
        self.assertEqual(cleanup.call_count, 2)

    def test_protected_restore_tries_auth_cleanup_even_if_azure_restore_fails(self):
        workflow = (ROOT / ".github/workflows/p0249-dev-y1-public-shadow-bounded-once.yml").read_text()
        restore = workflow.split("\n  independent-restore:\n", 1)[1]
        self.assertIn("Independently reconcile run-bound disposable Auth users", restore)
        self.assertIn("if: always()", restore)
        self.assertIn("RGAI_DEV_SERVICE_KEY: ${{ secrets.RETAIL_SUPABASE_SERVICE_ROLE_KEY }}", restore)
        self.assertIn("p0249_y1_signed_auth_shadow_once.py cleanup-only", restore)
        self.assertLess(restore.index("p0249_y1_public_shadow_trial_guard.py rollback"),
                        restore.index("p0249_y1_signed_auth_shadow_once.py cleanup-only"))

    def test_workflow_never_passes_admin_key_as_azure_appsetting(self):
        workflow = (ROOT / ".github/workflows/p0249-dev-y1-public-shadow-bounded-once.yml").read_text()
        self.assertIn("RGAI_DEV_SERVICE_KEY: ${{ secrets.RETAIL_SUPABASE_SERVICE_ROLE_KEY }}", workflow)
        self.assertIn("tests/e2e/p0249_y1_signed_auth_shadow_once.py", workflow)
        self.assertIn("independent-restore:", workflow)
        self.assertNotIn("RETAIL_SUPABASE_SERVICE_ROLE_KEY=", workflow)
        self.assertNotIn("RGAI_DEV_SERVICE_KEY=", workflow)


if __name__ == "__main__":
    unittest.main()
