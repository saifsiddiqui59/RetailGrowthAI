"""Mocked no-cloud safety gates for the #249 guarded costed trial."""
import json
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "ops"))
import p0_249_always_ready_trial_guarded as subject

ENV = {"GITHUB_RUN_ID": "1234", "GITHUB_RUN_ATTEMPT": "1"}


class GuardedAlwaysReadyTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.path = str(Path(self.tmp.name) / "prior.json")
        p = patch.dict(os.environ, ENV)
        p.start()
        self.addCleanup(p.stop)

    def marker(self):
        with open(self.path, "w", encoding="utf-8") as fp:
            json.dump({"schema": "retailgrowthai/p0249-trial/v1",
                       "run_id": "1234", "run_attempt": "1",
                       "http_count_before": None}, fp)

    def test_safe_http_count_rejects_duplicate_groups(self):
        self.assertIsNone(subject.http_count([]))
        self.assertIsNone(subject.http_count([{"name": "function:x", "instanceCount": 1}]))
        self.assertEqual(subject.http_count([{"name": "http", "instanceCount": 1}]), 1)
        with self.assertRaises(RuntimeError):
            subject.http_count([{"name": "http"}, {"name": "http"}])

    def test_preflight_creates_exact_marker_after_readonly_check(self):
        with patch.object(subject, "read_scope", return_value=[]), \
             patch.object(subject, "az", side_effect=AssertionError("no Azure write")):
            subject.preflight(self.path)
        subject.check_snapshot(self.path)
        self.assertEqual(json.loads(Path(self.path).read_text())["http_count_before"], None)

    def test_preflight_does_not_overwrite_existing_http_setting(self):
        with patch.object(subject, "read_scope",
                          return_value=[{"name": "http", "instanceCount": 1}]), \
             self.assertRaises(RuntimeError):
            subject.preflight(self.path)
        self.assertFalse(Path(self.path).exists())

    def test_mismatched_or_missing_marker_prevents_trial_and_cleanup(self):
        Path(self.path).write_text('{"schema":"something-else"}')
        with self.assertRaises(RuntimeError):
            subject.check_snapshot(self.path)
        with patch.object(subject, "az", side_effect=AssertionError("no Azure mutation")), \
             self.assertRaises(RuntimeError):
            subject.trial(self.path)

    def test_rollback_deletes_only_http_and_verifies_absence(self):
        self.marker()
        sequence = [[{"name": "function:keep", "instanceCount": 2},
                     {"name": "http", "instanceCount": 1}],
                    [{"name": "function:keep", "instanceCount": 2}]]
        with patch.object(subject, "read_scope", side_effect=sequence), \
             patch.object(subject, "az", return_value={}) as azure, \
             patch.object(subject.time, "sleep"):
            self.assertTrue(subject.rollback(self.path))
        self.assertEqual(azure.call_count, 1)
        cmd = azure.call_args.args
        self.assertEqual(cmd[:6], ("functionapp", "scale", "config", "always-ready", "delete", "-g"))
        self.assertEqual(cmd[-2:], ("--setting-names", "http"))
        self.assertNotIn("function:keep", cmd)

    def test_rollback_aborts_if_count_was_changed_by_another_actor(self):
        self.marker()
        with patch.object(subject, "read_scope",
                          return_value=[{"name": "http", "instanceCount": 2}]), \
             patch.object(subject, "az", side_effect=AssertionError("must not delete")):
            self.assertFalse(subject.rollback(self.path))

    def test_uncertain_write_ack_still_triggers_rollback(self):
        self.marker()
        with patch.object(subject, "read_scope", return_value=[]), \
             patch.object(subject, "az", side_effect=RuntimeError("lost ACK")), \
             patch.object(subject, "rollback", return_value=True) as rb, \
             self.assertRaises(RuntimeError):
            subject.trial(self.path)
        rb.assert_called_once_with(self.path)

    def test_successful_trial_runs_two_12_get_windows_and_rolls_back(self):
        self.marker()
        reads = [[], [{"name": "http", "instanceCount": 1}]]
        with patch.object(subject, "read_scope", side_effect=reads), \
             patch.object(subject, "az", return_value={}) as azure, \
             patch.object(subject, "probe", return_value=True) as check, \
             patch.object(subject, "rollback", return_value=True) as rollback, \
             patch.object(subject.time, "sleep"), \
             patch.object(subject.time, "monotonic", return_value=100.0):
            self.assertEqual(subject.trial(self.path), 0)
        self.assertEqual(check.call_count, 24)
        self.assertEqual(azure.call_count, 1)
        self.assertEqual(azure.call_args.args[-2:], ("--settings", "http=1"))
        rollback.assert_called_once_with(self.path)

    def test_live_scope_denies_wrong_subscription_before_any_change(self):
        with patch.dict(os.environ,
                        {"RGAI_DEV_EXPECTED_SUBSCRIPTION":
                         "11111111-1111-4111-8111-111111111111"}), \
             patch.object(subject, "az", return_value={"id":
                         "22222222-2222-4222-8222-222222222222"}) as azure, \
             self.assertRaises(RuntimeError):
            subject.read_scope()
        self.assertEqual(azure.call_args.args, ("account", "show"))


if __name__ == "__main__":
    unittest.main()
