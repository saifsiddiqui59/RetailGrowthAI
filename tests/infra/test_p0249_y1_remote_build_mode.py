"""Offline safety and rollback tests for the #249 Linux Y1 mode transition."""
from __future__ import annotations

import contextlib
import io
import os
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "ops"))
import p0249_y1_remote_build_mode as y1


class FakeAzure:
    def __init__(self):
        self.secret = "https://rgaid4e5ddbdf0d21d96.blob.core.windows.net/private/old.zip?sig=SENSITIVE"
        self.settings = {"WEBSITE_RUN_FROM_PACKAGE": self.secret,
                         "SCM_DO_BUILD_DURING_DEPLOYMENT": "true",
                         "FUNCTIONS_WORKER_RUNTIME": "python"}
        self.names = ["p0249_health", "campaign_read"]
        self.mutations = []
        self.sync = 0

    def execute(self, *cmd):
        args = list(cmd)
        if args[:4] == ["functionapp", "config", "appsettings", "list"]:
            return [{"name": k, "value": v} for k, v in self.settings.items()]
        if args[:3] == ["functionapp", "function", "list"]:
            return [y1.SITE + "/" + name for name in self.names]
        if args[:4] == ["functionapp", "config", "appsettings", "set"]:
            vals = args[args.index("--settings") + 1:]
            self.mutations.append(("set", tuple(z.split("=", 1)[0] for z in vals)))
            for val in vals:
                key, value = val.split("=", 1)
                self.settings[key] = value
            if "WEBSITE_RUN_FROM_PACKAGE" in [v.split("=", 1)[0] for v in vals]:
                self.names = ["p0249_health", "campaign_read"]
            return []
        if args[:4] == ["functionapp", "config", "appsettings", "delete"]:
            names = args[args.index("--setting-names") + 1:]
            self.mutations.append(("delete", tuple(names)))
            for name in names:
                self.settings.pop(name, None)
            return []
        if args[:2] == ["functionapp", "sync-function-triggers"]:
            self.sync += 1
            return None
        raise AssertionError("Unapproved Azure CLI path: " + repr(args[:4]))


class Y1RemoteBuildModeTests(unittest.TestCase):
    def setUp(self):
        self.cloud = FakeAzure()
        self.patches = [
            patch.object(y1, "_az", side_effect=lambda *a: self.cloud.execute(*a)),
            patch.object(y1.guard, "verify", return_value=None),
            patch.object(y1.guard, "probe", return_value=None),
            patch.dict(os.environ, {"GITHUB_RUN_ID": "44630000000"}),
        ]
        for p in self.patches:
            p.start()
            self.addCleanup(p.stop)

    def test_prepare_switches_to_remote_build_only_after_backup_is_saved(self):
        with contextlib.redirect_stdout(io.StringIO()) as buf:
            y1.prepare()
        self.assertEqual(self.cloud.settings[y1.BACKUP], self.cloud.secret)
        self.assertEqual(self.cloud.settings[y1.OWNER], "44630000000")
        self.assertNotIn("WEBSITE_RUN_FROM_PACKAGE", self.cloud.settings)
        self.assertEqual(self.cloud.settings["ENABLE_ORYX_BUILD"], "true")
        self.assertEqual([m[0] for m in self.cloud.mutations], ["set", "delete", "set"])
        self.assertNotIn("SENSITIVE", buf.getvalue())

    def test_complete_rollback_restores_original_url_without_printing_it(self):
        y1.prepare()
        self.cloud.names = sorted(y1.FIVE)
        with contextlib.redirect_stdout(io.StringIO()) as buf:
            y1.rollback()
        self.assertEqual(self.cloud.settings["WEBSITE_RUN_FROM_PACKAGE"], self.cloud.secret)
        self.assertNotIn(y1.BACKUP, self.cloud.settings)
        self.assertNotIn(y1.OWNER, self.cloud.settings)
        self.assertNotIn("ENABLE_ORYX_BUILD", self.cloud.settings)
        self.assertEqual(self.cloud.sync, 1)
        self.assertEqual(frozenset(self.cloud.names), y1.TWO)
        self.assertIn("P0249_Y1_ORIGINAL_EXTERNAL_PACKAGE_ROLLBACK=PASS", buf.getvalue())
        self.assertNotIn("SENSITIVE", buf.getvalue())

    def test_no_cloud_write_on_shadows_foreign_functions_or_invalid_package(self):
        for modifier in (
            lambda s, c: s.update({"RETAIL_SUPABASE_URL": "SECRET"}),
            lambda s, c: c.names.append("queue_trigger"),
            lambda s, c: s.update({"WEBSITE_RUN_FROM_PACKAGE": "http://bad/?secret=PASS"}),
            lambda s, c: s.update({"ENABLE_ORYX_BUILD": "true"}),
            lambda s, c: s.update({y1.BACKUP: "https://other.example/old.zip"}),
        ):
            with self.subTest(modifier=modifier):
                self.cloud = FakeAzure()
                modifier(self.cloud.settings, self.cloud)
                with self.assertRaises(RuntimeError):
                    y1.prepare()
                self.assertEqual(self.cloud.mutations, [])

    def test_rollback_refuses_foreign_owner_and_unexpected_new_index(self):
        y1.prepare()
        self.cloud.settings[y1.OWNER] = "98765432100"
        self.cloud.mutations.clear()
        with self.assertRaisesRegex(RuntimeError, "Unowned"):
            y1.rollback()
        self.assertEqual(self.cloud.mutations, [])
        self.cloud.settings[y1.OWNER] = "44630000000"
        self.cloud.names = ["p0249_health", "unexpected_write_route"]
        with self.assertRaisesRegex(RuntimeError, "Unknown"):
            y1.rollback()
        self.assertEqual(self.cloud.mutations, [])

    def test_prepare_refuses_second_run_and_no_backup_state(self):
        y1.prepare()
        self.cloud.mutations.clear()
        with self.assertRaisesRegex(RuntimeError, "already exists"):
            y1.prepare()
        self.assertEqual(self.cloud.mutations, [])
        self.cloud.settings.pop(y1.BACKUP)
        self.cloud.settings.pop(y1.OWNER)
        with self.assertRaisesRegex(RuntimeError, "No Y1 backup"):
            y1.rollback()

    def test_postpublish_build_settings_fail_closed_on_removed_oryx(self):
        y1.prepare()
        with contextlib.redirect_stdout(io.StringIO()) as b:
            y1.verify_build_mode()
        self.assertIn("POSTPUBLISH_SETTINGS=PASS", b.getvalue())
        self.cloud.settings.pop("ENABLE_ORYX_BUILD")
        self.cloud.mutations.clear()
        with self.assertRaisesRegex(RuntimeError, "settings or owner drifted"):
            y1.verify_build_mode()
        self.assertEqual(self.cloud.mutations, [])
        self.cloud.settings["ENABLE_ORYX_BUILD"] = "true"
        self.cloud.settings["WEBSITE_RUN_FROM_PACKAGE"] = self.cloud.secret
        with self.assertRaisesRegex(RuntimeError, "settings or owner drifted"):
            y1.verify_build_mode()
        self.assertEqual(self.cloud.mutations, [])

    def test_verify_five_requires_actual_routes_remote_mode_and_owner(self):
        y1.prepare()
        with self.assertRaisesRegex(RuntimeError, "not actually indexed"):
            y1.verify_five()
        self.cloud.names = sorted(y1.FIVE)
        with contextlib.redirect_stdout(io.StringIO()) as b:
            y1.verify_five()
        self.assertIn("P0249_Y1_REMOTE_BUILD_FIVE_INDEXES=PASS", b.getvalue())
        self.cloud.settings[y1.OWNER] = "other"
        with self.assertRaisesRegex(RuntimeError, "owner/mode drifted"):
            y1.verify_five()

    def test_original_reference_is_never_in_exception_or_public_log(self):
        self.cloud.settings["WEBSITE_RUN_FROM_PACKAGE"] = (
            "https://user:password@bad.blob.core.windows.net/package.zip?sig=TOKEN")
        with contextlib.redirect_stdout(io.StringIO()) as b:
            with self.assertRaises(RuntimeError) as err:
                y1.prepare()
        for secret in ("password", "TOKEN", "sig=", "rgaid4e5"):
            self.assertNotIn(secret, str(err.exception) + b.getvalue())

    def test_readonly_classification_matches_expected_azure_deployment_mode(self):
        from p0249_y1_deploy_diagnostic_readonly import setting_flags
        flags = setting_flags([
            {"name": "SCM_DO_BUILD_DURING_DEPLOYMENT", "value": "true"},
            {"name": "WEBSITE_RUN_FROM_PACKAGE", "value": self.cloud.secret},
        ])
        self.assertEqual(flags["WEBSITE_RUN_FROM_PACKAGE"]["nonsecret_mode"],
                         "EXTERNAL_HTTPS_URL")
        self.assertEqual(flags["WEBSITE_RUN_FROM_PACKAGE"]["build_config_class"],
                         "REMOTE_BUILD_FLAGS_MIXED")


if __name__ == "__main__":
    unittest.main()
