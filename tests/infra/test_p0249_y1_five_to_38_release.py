"""Offline negative tests for guarded Y1 FIVE -> 38 index/rollback (no Azure)."""
import importlib.util
import os
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "ops/p0249-y1-cutover/five_to_38_release.py"
spec = importlib.util.spec_from_file_location("p0249_y1_five_to_38_release", SOURCE)
release = importlib.util.module_from_spec(spec)
spec.loader.exec_module(release)

FIVE_URL = (
    "https://rgaid4e5ddbdf0d21d96.blob.core.windows.net/"
    "y1-verified-package/five-source.zip?sv=2026&sig=private-not-logged"
)
NEW_URL = (
    "https://rgaid4e5ddbdf0d21d96.blob.core.windows.net/"
    "y1-verified-package/new-38-source.zip?sv=2026&sig=private-not-logged"
)


class FiveTo38ReleaseTests(unittest.TestCase):
    def setUp(self):
        self.settings = {"WEBSITE_RUN_FROM_PACKAGE": FIVE_URL,
                         "SCM_DO_BUILD_DURING_DEPLOYMENT": "true"}
        self.index = set(release.FIVE)
        self.azure_mutations = []
        self.probe_calls = 0

        def az(*args):
            if args[:3] == ("functionapp", "function", "list"):
                return [release.guard.SITE + "/" + name
                        for name in sorted(self.index)]
            if args[:2] == ("resource", "invoke-action"):
                self.index = set(release.FIVE)
                self.azure_mutations.append("trigger-sync")
                return {}
            raise AssertionError("Unexpected Azure command: " + repr(args[:2]))

        def set_settings(**pairs):
            self.azure_mutations.append("appsettings-set")
            self.settings.update(pairs)

        def delete_settings(*names):
            self.azure_mutations.append("appsettings-delete")
            for name in names:
                self.settings.pop(name, None)

        self.patches = [
            patch.object(release.guard, "verify", return_value=None),
            patch.object(release.guard, "probe",
                         side_effect=lambda: setattr(
                             self, "probe_calls", self.probe_calls + 1)),
            patch.object(release.legacy, "_settings",
                         side_effect=lambda: dict(self.settings)),
            patch.object(release.legacy, "_set", side_effect=set_settings),
            patch.object(release.legacy, "_delete", side_effect=delete_settings),
            patch.object(release.legacy, "_az", side_effect=az),
            patch.object(release.legacy, "_run_id", return_value="45099900001"),
            patch.object(release.time, "sleep", return_value=None),
        ]
        for item in self.patches:
            item.start()
            self.addCleanup(item.stop)

    def test_five_preflight_is_read_only(self):
        release.preflight()
        self.assertEqual(self.azure_mutations, [])

    def test_two_baseline_and_partial_five_are_denied(self):
        for functions in (set(), set(release.FIVE) - {"poster_job_read"},
                          {"p0249_health", "campaign_read"}):
            self.index = functions
            with self.assertRaises(RuntimeError):
                release.prepare()
        self.assertEqual(self.azure_mutations, [])

    def test_wrong_or_malformed_package_is_denied_before_write(self):
        candidates = [
            "1", "", None, "https://another.blob.core.windows.net/object",
            FIVE_URL.replace("https:", "http:"),
            FIVE_URL.replace("rgaid4e5ddbdf0d21d96", "foreignstorage"),
            "https://rgaid4e5ddbdf0d21d96.blob.core.windows.net:garbage/x",
            FIVE_URL + "#token",
        ]
        for value in candidates:
            self.settings["WEBSITE_RUN_FROM_PACKAGE"] = value
            with self.assertRaises((ValueError, RuntimeError)):
                release.prepare()
            self.assertEqual(self.azure_mutations, [])

    def test_backup_is_persisted_without_replacing_live_five(self):
        release.prepare()
        self.assertEqual(self.settings[release.BACKUP], FIVE_URL)
        self.assertEqual(self.settings[release.OWNER], "45099900001")
        self.assertEqual(self.settings[release.ORYX_BASELINE], "absent")
        self.assertNotIn("WEBSITE_RUN_FROM_PACKAGE", self.settings)
        self.assertEqual(self.settings["ENABLE_ORYX_BUILD"], "true")
        self.assertEqual(self.index, set(release.FIVE))
        with self.assertRaises(RuntimeError):
            release.prepare()  # no accidental overwrite / double release

    def test_verify_requires_new_pinned_url_and_exact_38_http(self):
        release.prepare()
        self.settings["WEBSITE_RUN_FROM_PACKAGE"] = NEW_URL
        self.index = set(release.THIRTY_EIGHT)
        release.verify()
        for current in (set(release.THIRTY_EIGHT) - {"read_campaign"},
                        set(release.FIVE), set(release.THIRTY_EIGHT) | {"render_campaign_reel"}):
            self.index = current
            with self.assertRaises(RuntimeError):
                release.verify()
        self.index = set(release.THIRTY_EIGHT)
        self.settings["WEBSITE_RUN_FROM_PACKAGE"] = FIVE_URL
        with self.assertRaises(RuntimeError):
            release.verify()

    def test_foreign_and_duplicate_index_deny_before_rollout(self):
        self.index = set(release.FIVE) | {"evil_unknown"}
        with self.assertRaises(RuntimeError):
            release.prepare()
        self.assertEqual(self.azure_mutations, [])

    def test_missing_owner_or_other_run_must_not_revert(self):
        self.index = set(release.THIRTY_EIGHT)
        self.settings.update({release.BACKUP: FIVE_URL,
                              release.OWNER: "foreign-run",
                              "WEBSITE_RUN_FROM_PACKAGE": NEW_URL})
        with self.assertRaises(RuntimeError):
            release.rollback()
        self.assertEqual(self.azure_mutations, [])

    def test_partial_backup_denied_and_never_changes_cloud(self):
        self.settings[release.BACKUP] = FIVE_URL
        with self.assertRaises(RuntimeError):
            release.rollback()
        self.assertEqual(self.azure_mutations, [])

    def test_unmodified_five_no_owner_has_no_rollback_write(self):
        release.rollback()
        self.assertEqual(self.probe_calls, 1)
        self.assertEqual(self.azure_mutations, [])

    def test_restore_five_after_38_and_verify_twice(self):
        release.prepare()
        self.settings["WEBSITE_RUN_FROM_PACKAGE"] = NEW_URL
        self.index = set(release.THIRTY_EIGHT)
        release.rollback()
        self.assertEqual(self.settings["WEBSITE_RUN_FROM_PACKAGE"], FIVE_URL)
        self.assertNotIn(release.BACKUP, self.settings)
        self.assertNotIn(release.OWNER, self.settings)
        self.assertNotIn(release.ORYX_BASELINE, self.settings)
        self.assertNotIn("ENABLE_ORYX_BUILD", self.settings)
        self.assertEqual(self.index, set(release.FIVE))
        self.assertEqual(self.probe_calls, 2)
        self.assertIn("trigger-sync", self.azure_mutations)

    def test_legacy_true_oryx_baseline_is_restored_exactly(self):
        self.settings["ENABLE_ORYX_BUILD"] = "true"
        release.prepare()
        self.assertEqual(self.settings[release.ORYX_BASELINE], "true")
        self.settings["WEBSITE_RUN_FROM_PACKAGE"] = NEW_URL
        self.index = set(release.THIRTY_EIGHT)
        release.rollback()
        self.assertEqual(self.settings["WEBSITE_RUN_FROM_PACKAGE"], FIVE_URL)
        self.assertEqual(self.settings["ENABLE_ORYX_BUILD"], "true")
        self.assertNotIn(release.ORYX_BASELINE, self.settings)

    def test_legacy_false_oryx_baseline_is_restored_exactly(self):
        self.settings["ENABLE_ORYX_BUILD"] = "false"
        release.prepare()
        self.assertEqual(self.settings["ENABLE_ORYX_BUILD"], "true")
        release.rollback()
        self.assertEqual(self.settings["WEBSITE_RUN_FROM_PACKAGE"], FIVE_URL)
        self.assertEqual(self.settings["ENABLE_ORYX_BUILD"], "false")

    def test_partial_oryx_backup_fails_closed(self):
        self.settings[release.ORYX_BASELINE] = "absent"
        with self.assertRaises(RuntimeError):
            release.rollback()
        self.assertEqual(self.azure_mutations, [])

    def test_remote_build_mode_must_have_absent_old_zip_and_enabled_oryx(self):
        release.prepare()
        self.assertNotIn("WEBSITE_RUN_FROM_PACKAGE", self.settings)
        self.assertEqual(self.settings["ENABLE_ORYX_BUILD"], "true")
        self.assertEqual(self.settings["SCM_DO_BUILD_DURING_DEPLOYMENT"], "true")
        self.assertIn("appsettings-delete", self.azure_mutations)
        self.settings["WEBSITE_RUN_FROM_PACKAGE"] = NEW_URL
        self.index = set(release.THIRTY_EIGHT)
        self.settings["ENABLE_ORYX_BUILD"] = "false"
        with self.assertRaises(RuntimeError):
            release.verify()

    def test_unknown_worker_denies_rollback_before_appsettings_write(self):
        release.prepare()
        self.azure_mutations.clear()
        self.settings["WEBSITE_RUN_FROM_PACKAGE"] = NEW_URL
        self.index = {"render_campaign_reel"}
        with self.assertRaises(RuntimeError):
            release.rollback()
        self.assertEqual(self.azure_mutations, [])


if __name__ == "__main__":
    unittest.main()
