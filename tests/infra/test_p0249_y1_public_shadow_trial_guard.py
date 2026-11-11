"""Offline, no-Azure tests of bounded Y1 read shadow activation/rollback."""
import importlib.util
import json
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "ops"))
import p0249_y1_public_shadow_trial_guard as trial


class PublicShadowTrialSafetyTests(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.path = str(Path(tmp.name) / "rollback.json")
        self.k = "sb_publishable_" + "x" * 24
        env = patch.dict(os.environ, {
            "GITHUB_RUN_ID": "1000", "GITHUB_RUN_ATTEMPT": "1",
            "RGAI_DEV_P0249_PUBLISHABLE_KEY": self.k,
        })
        env.start()
        self.addCleanup(env.stop)

    def marker(self):
        Path(self.path).write_text(json.dumps(trial.marker()))

    def test_exact_public_only_setting_allowlist(self):
        self.assertEqual(set(trial.NAMES), {
            "RETAIL_SUPABASE_URL", "RETAIL_SUPABASE_PUBLISHABLE_KEY",
            "RGAI_P0249_READONLY_SHADOW"})
        self.assertEqual(trial.key(), self.k)
        self.assertEqual(trial.EXPECTED_FUNCTIONS, {"p0249_health", "campaign_read"})

    def test_reject_service_or_legacy_or_missing_keys(self):
        for key in ("", "eyJabc123", "sb_secret_abcdef0123456789",
                    "sb_publishable_short", "something=wrong"):
            with self.subTest(key=key[:9]), \
                 patch.dict(os.environ, {"RGAI_DEV_P0249_PUBLISHABLE_KEY": key}), \
                 self.assertRaises(RuntimeError):
                trial.key()

    def test_preflight_is_readonly_and_creates_run_bound_marker(self):
        with patch.object(trial, "verify_y1"), \
             patch.object(trial, "indexed"), \
             patch.object(trial, "current", return_value={}), \
             patch.object(trial, "mutate",
                          side_effect=AssertionError("preflight must never write")):
            trial.preflight(self.path)
        trial.read_marker(self.path)
        self.assertEqual(json.loads(Path(self.path).read_text())["before"],
                         "all-three-absent")

    def test_preflight_refuses_to_override_any_existing_setting(self):
        for name in trial.NAMES:
            with self.subTest(name=name), \
                 patch.object(trial, "verify_y1"), \
                 patch.object(trial, "indexed"), \
                 patch.object(trial, "current", return_value={name: "prior"}), \
                 patch.object(trial, "mutate", side_effect=AssertionError("unsafe")), \
                 self.assertRaises(RuntimeError):
                trial.preflight(self.path)
        self.assertFalse(Path(self.path).exists())

    def test_stale_or_crossrun_marker_never_allows_mutation(self):
        self.marker()
        with patch.dict(os.environ, {"GITHUB_RUN_ID": "1001"}), \
             patch.object(trial, "mutate", side_effect=AssertionError("unsafe")), \
             self.assertRaises(RuntimeError):
            trial.set_public_only(self.path)

    def test_activate_sets_only_three_public_settings(self):
        self.marker()
        cfg = {"RETAIL_SUPABASE_URL": trial.PROJECT_URL,
               "RETAIL_SUPABASE_PUBLISHABLE_KEY": self.k,
               "RGAI_P0249_READONLY_SHADOW": "true"}
        with patch.object(trial, "verify_y1"), \
             patch.object(trial, "indexed"), \
             patch.object(trial, "current", side_effect=[{}, cfg]), \
             patch.object(trial, "mutate") as act:
            trial.set_public_only(self.path)
        args = act.call_args.args
        self.assertEqual(args[:5], ("functionapp", "config", "appsettings", "set", "-g"))
        self.assertEqual(args[args.index("-n")+1], trial.SITE)
        self.assertEqual(len(args[args.index("--settings")+1:]), 3)
        self.assertNotIn("service_role", " ".join(args))
        self.assertIn("RGAI_P0249_READONLY_SHADOW=true", args)

    def test_activate_refuses_changed_config_without_writes(self):
        self.marker()
        with patch.object(trial, "verify_y1"), \
             patch.object(trial, "indexed"), \
             patch.object(trial, "current", return_value={"RGAI_P0249_READONLY_SHADOW": "true"}), \
             patch.object(trial, "mutate", side_effect=AssertionError("unsafe")), \
             self.assertRaises(RuntimeError):
            trial.set_public_only(self.path)

    def test_rollback_removes_only_trial_keys_and_verifies_absence(self):
        self.marker()
        cfg = {"RETAIL_SUPABASE_URL": trial.PROJECT_URL,
               "RETAIL_SUPABASE_PUBLISHABLE_KEY": self.k,
               "RGAI_P0249_READONLY_SHADOW": "true"}
        with patch.object(trial, "verify_y1"), \
             patch.object(trial, "current", side_effect=[cfg, {}]), \
             patch.object(trial, "mutate") as action, \
             patch.object(trial.time, "sleep"):
            self.assertTrue(trial.rollback(self.path))
        args = action.call_args.args
        self.assertEqual(args[:4], ("functionapp", "config", "appsettings", "delete"))
        self.assertEqual(set(args[args.index("--setting-names")+1:]), set(trial.NAMES))

    def test_rollback_aborts_if_concurrent_value_is_different(self):
        self.marker()
        with patch.object(trial, "verify_y1"), \
             patch.object(trial, "current",
                          return_value={"RGAI_P0249_READONLY_SHADOW": "false"}), \
             patch.object(trial, "mutate", side_effect=AssertionError("unsafe")):
            self.assertFalse(trial.rollback(self.path))

    def test_rollback_accepts_preexisting_absence_after_failed_activation(self):
        self.marker()
        with patch.object(trial, "verify_y1"), \
             patch.object(trial, "current", return_value={}), \
             patch.object(trial, "mutate", side_effect=AssertionError("unsafe")):
            self.assertTrue(trial.rollback(self.path))

    def test_index_rejects_missing_or_additional_functions(self):
        for names in ([], [{"name":"p0249_health"}],
                      [{"name":"p0249_health"},{"name":"campaign_read"},{"name":"queue"}]):
            with self.subTest(names=names), \
                 patch.object(trial, "cli", return_value=names), \
                 self.assertRaises(RuntimeError):
                trial.indexed()

    def test_protected_workflow_has_separate_rollback_and_no_other_azure_mutation(self):
        work = (ROOT / ".github/workflows/p0249-dev-y1-public-shadow-bounded-once.yml").read_text()
        self.assertIn("environment: dev", work)
        self.assertEqual(work.count("environment: dev"), 3)
        self.assertIn("cancel-in-progress: false", work)
        self.assertIn("independent-restore:", work)
        self.assertIn("needs: [preflight, temporary-negative-test]", work)
        self.assertIn("github.ref == 'refs/heads/main'", work)
        self.assertIn("YES-Y1-DEV-PUBLIC-SHADOW-BOUNDED", work)
        self.assertIn("p0249_y1_public_shadow_trial_guard.py preflight", work)
        self.assertIn("p0249_y1_public_shadow_trial_guard.py activate", work)
        self.assertIn("p0249_y1_public_shadow_trial_guard.py rollback", work)
        for forbidden in ("az deployment group create", "az functionapp create",
                          "az functionapp delete", "az group delete",
                          "az storage account", "AZURE_CLIENT_SECRET",
                          "RETAIL_SUPABASE_SERVICE_ROLE_KEY", "sb_secret_"):
            with self.subTest(forbidden=forbidden):
                self.assertNotIn(forbidden, work)

    def test_live_negative_probe_requires_marker_and_exact_status(self):
        self.marker()
        with patch.object(trial, "indexed"), \
             patch.object(trial, "get", side_effect=lambda p, t="": (
                (401, True, 0.5) if p==trial.CAMPAIGN_PATH
                else (200, True, 0.4)
             )) as req:
            trial.test_negative()
        self.assertEqual(req.call_count, 16)

    def test_live_negative_probe_fails_on_unmarked_401(self):
        with patch.object(trial, "indexed"), \
             patch.object(trial, "get", return_value=(401, False, 0.4)), \
             self.assertRaises(RuntimeError):
            trial.test_negative()


if __name__ == "__main__":
    unittest.main()
