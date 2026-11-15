"""Offline source tests for real signed DEV Y1 Auth-only test and cleanup."""
import importlib.util
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
        })
        env.start()
        self.addCleanup(env.stop)

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
             patch.object(trial.helper, "owner_only_cleanup") as cleaned:
            trial.main()
        self.assertEqual(created.call_count, 2)
        self.assertEqual(cleaned.call_count, 2)
        self.assertEqual(request.call_count, 9)

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
        marker = trial.helper.CANARY_PREFIX + "fixture123"
        uid = "11111111-1111-4111-8111-111111111111"
        values = [
            (200, {"users": [{"email": "unrelated@example.invalid"}], "next_page": 2}, None, 0.1),
            (200, {"users": [{"email": marker + "@example.invalid", "id": uid}], "next_page": 0}, None, 0.1),
            (204, {}, None, 0.1),
        ]
        with patch.object(trial.helper, "request", side_effect=values) as req:
            trial.helper.owner_only_cleanup("sb_secret_" + "x" * 42, marker, None)
        self.assertEqual(req.call_count, 3)
        self.assertIn("page=1", req.call_args_list[0].args[0])
        self.assertIn("page=2", req.call_args_list[1].args[0])
        self.assertTrue(req.call_args_list[2].args[0].endswith("/auth/v1/admin/users/" + uid))
        self.assertEqual(req.call_args_list[2].kwargs["method"], "DELETE")
        self.assertEqual(req.call_args_list[2].kwargs["headers"], {"apikey": "sb_secret_" + "x" * 42})

    def test_unknown_auth_inventory_fails_closed_without_deletion(self):
        marker = trial.helper.CANARY_PREFIX + "fixture456"
        with patch.object(trial.helper, "request", return_value=(
            200, {"users": [], "next_page": 7}, None, 0.1
        )) as req, self.assertRaises(RuntimeError):
            trial.helper.owner_only_cleanup("sb_secret_" + "x" * 42, marker, None)
        self.assertEqual(req.call_count, 1)
        self.assertNotIn("method", req.call_args.kwargs)

    def test_workflow_never_passes_admin_key_as_azure_appsetting(self):
        workflow = (ROOT / ".github/workflows/p0249-dev-y1-public-shadow-bounded-once.yml").read_text()
        self.assertIn("RGAI_DEV_SERVICE_KEY: ${{ secrets.RETAIL_SUPABASE_SERVICE_ROLE_KEY }}", workflow)
        self.assertIn("tests/e2e/p0249_y1_signed_auth_shadow_once.py", workflow)
        self.assertIn("independent-restore:", workflow)
        self.assertNotIn("RETAIL_SUPABASE_SERVICE_ROLE_KEY=", workflow)
        self.assertNotIn("RGAI_DEV_SERVICE_KEY=", workflow)


if __name__ == "__main__":
    unittest.main()
