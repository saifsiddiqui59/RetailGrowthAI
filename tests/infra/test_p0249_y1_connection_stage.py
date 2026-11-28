"""Offline synthetic guards for Y1 DEV missing-only core connection staging.

No Azure network, real credentials, user data, app configuration or cloud writes.
"""
import importlib.util
import contextlib
import io
import json
import sys
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
DIR = ROOT / "ops/p0249-y1-cutover"
sys.path.insert(0, str(DIR))
spec = importlib.util.spec_from_file_location("p0249_stage_connections",
                                              DIR / "stage_core_connections.py")
stage = importlib.util.module_from_spec(spec)
spec.loader.exec_module(stage)

ENV = {
    "GITHUB_ACTIONS": "true", "GITHUB_REPOSITORY": stage.REPO,
    "GITHUB_REF": "refs/heads/main",
    "AZURE_SUBSCRIPTION_ID": "synthetic-subscription",
    "GITHUB_ENVIRONMENT": "dev",
}
ORIGINAL = {
    "RETAIL_SUPABASE_URL": stage.SUPABASE,
    "RETAIL_SUPABASE_PUBLISHABLE_KEY": "pub_" + "p" * 64,
    "RETAIL_SUPABASE_SERVICE_ROLE_KEY": "service_" + "s" * 68,
    "RETAIL_STORAGE": "DefaultEndpointsProtocol=https;" + "synthetic" * 8,
    "AzureWebJobsStorage": "host-only-original-strong-secret",
}
TARGET = {
    "AzureWebJobsStorage": "separate-y1-host-strong-secret",
    "FUNCTIONS_WORKER_RUNTIME": "python",
}


class FakeAzure:
    def __init__(self):
        self.original = dict(ORIGINAL)
        self.target = dict(TARGET)
        self.routes = set(stage.FIVE)
        self.origin = stage.FRONTEND
        self.subscription = ENV["AZURE_SUBSCRIPTION_ID"]
        self.location = "centralindia"
        self.writes = []
        self.reads = 0
        self.payload_paths = []
        self.fail_settings = False
        self.fail_cors = False

    def _resource(self, name):
        return {
            "name": name,
            "id": ("/subscriptions/" + self.subscription + "/resourceGroups/"
                   + stage.RG + "/providers/Microsoft.Web/sites/" + name),
            "properties": {"state": "Running", "functionAppConfig": {"runtime": {"name": "python"}}},
        }

    def read(self, args, **kwargs):
        self.reads += 1
        self_args = tuple(args[1:-2])
        assert args[0] == "az" and tuple(args[-2:]) == ("--output", "json")
        if self_args[:2] == ("account", "show"):
            data = {"id": self.subscription}
        elif self_args[:2] == ("group", "show"):
            data = {"name": stage.RG, "location": self.location,
                    "tags": {"app": "RetailGrowthAI", "environment": "dev"}}
        else:
            app = self_args[self_args.index("-n")+1]
            if self_args[:2] == ("resource", "show"):
                assert self_args == stage.site_read_args(app)
                data = self._resource(app)
            elif self_args[:3] == ("functionapp", "function", "list"):
                data = [{"name": stage.Y1 + "/" + n} for n in sorted(self.routes)]
            elif self_args[:3] == ("functionapp", "cors", "show"):
                data = {"supportCredentials": False,
                        "allowedOrigins": [self.origin] if self.origin else []}
            elif self_args[:3] == ("functionapp", "config", "appsettings"):
                obj = self.original if app == stage.FLEX else self.target
                data = [{"name": n, "value": v} for n, v in obj.items()]
            else:
                raise AssertionError("Unexpected Azure read")
        return SimpleNamespace(returncode=0, stdout=json.dumps(data),
                               stderr="sensitive-must-not-show")

    def write(self, args, **kwargs):
        if args[:4] == ["az", "functionapp", "cors", "add"]:
            assert args[4:9] == ["-g", stage.RG, "-n", stage.Y1, "--allowed-origins"]
            assert args[9] == stage.FRONTEND
            assert args[-3:] == ["-o", "none", "--only-show-errors"]
            self.writes.append(("CORS",))
            if self.fail_cors:
                return SimpleNamespace(returncode=1, stdout="sensitive-must-not-show",
                                       stderr="sensitive-must-not-show")
            self.origin = stage.FRONTEND
            return SimpleNamespace(returncode=0, stdout="", stderr="")
        assert args[:7] == ["az", "functionapp", "config", "appsettings",
                            "set", "-g", stage.RG]
        assert args[7:10] == ["-n", stage.Y1, "--settings"]
        assert args[-3:] == ["-o", "none", "--only-show-errors"]
        assert len(args[10:-3]) == 1 and args[10].startswith("@")
        for secret in self.original.values():
            assert secret not in " ".join(args), "Secret included in subprocess argv"
        payload_path = Path(args[10][1:])
        self.payload_paths.append(payload_path)
        assert payload_path.is_file()
        assert payload_path.stat().st_mode & 0o777 == 0o600
        assert payload_path.parent.stat().st_mode & 0o777 == 0o700
        document = json.loads(payload_path.read_text(encoding="utf-8"))
        assert isinstance(document, list) and document
        assert all(set(item) == {"name", "value", "slotSetting"} and
                   item["slotSetting"] is False for item in document)
        self.writes.append(tuple(item["name"] for item in document))
        if self.fail_settings:
            return SimpleNamespace(returncode=1, stdout="sensitive-must-not-show",
                                   stderr="sensitive-must-not-show")
        for item in document:
            name, value = item["name"], item["value"]
            assert name in stage.CORE
            assert value == self.original[name]
            self.target[name] = value
        return SimpleNamespace(returncode=0, stdout="sensitive-must-not-show",
                               stderr="sensitive-must-not-show")


class ConnectionStageTests(unittest.TestCase):
    def setUp(self):
        self.az = FakeAzure()

    def test_stopped_exact_arm_app_never_writes_or_restarts(self):
        for name, category in ((stage.FLEX, "ORIGINAL_FLEX_STOPPED"),
                               (stage.Y1, "TARGET_Y1_STOPPED")):
            az = FakeAzure()
            resource = az._resource
            def stopped(app):
                row = resource(app)
                if app == name:
                    row["properties"]["state"] = "Stopped"
                return row
            with patch.object(az, "_resource", side_effect=stopped), \
                    self.assertRaisesRegex(RuntimeError, category):
                stage.run(apply=True, env={**ENV, "RGAI_Y1_CORE_CONNECTION_STAGE": stage.STAGE_CONFIRM},
                          reader=az.read, writer=az.write)
            self.assertEqual(az.writes, [])

    def test_flex_runtime_accepts_exact_nested_or_flattened_python_only(self):
        flat = {"functionAppConfig": {"runtime": {"name": "python"}}}
        nested = {"properties": flat}
        self.assertTrue(stage._original_python(flat, {}))
        self.assertTrue(stage._original_python(nested, {}))
        self.assertFalse(stage._original_python(flat, {"FUNCTIONS_WORKER_RUNTIME": "node"}))
        self.assertFalse(stage._original_python({}, {}))
        self.assertFalse(stage._original_python({**flat, "properties": {"functionAppConfig":
            {"runtime": {"name": "node"}}}}, {}))
        with self.assertRaisesRegex(RuntimeError, "MALFORMED"):
            stage._original_python({"functionAppConfig": "SENSITIVE"}, {})

    def test_cli_failure_category_never_reflects_arbitrary_errors(self):
        for error, label in (
            (RuntimeError("FOREIGN_DEV_RESOURCE_GROUP"), "FOREIGN_DEV_RESOURCE_GROUP"),
            (RuntimeError("AZURE_APPSETTINGS_SHAPE_INVALID"), "AZURE_APPSETTINGS_SHAPE_INVALID"),
            (RuntimeError("SECRET?sig=PRIVATE"), "UNKNOWN_REDACTED"),
            (ValueError("SECRET"), "UNKNOWN_REDACTED"),
        ):
            with self.subTest(label=label), patch.object(stage, "run", side_effect=error), \
                    patch.object(sys, "argv", ["stage_core_connections.py"]), \
                    contextlib.redirect_stderr(io.StringIO()) as output:
                with self.assertRaises(SystemExit) as failure:
                    stage.main()
                self.assertEqual(failure.exception.code, 2)
                self.assertIn("P0249_Y1_STAGE_FAILURE_CATEGORY=" + label, output.getvalue())
                self.assertNotIn("SECRET", output.getvalue())
                self.assertNotIn("PRIVATE", output.getvalue())

    def test_plan_is_read_only_and_only_allowlisted_missing_names(self):
        missing, values, missing_cors = stage.plan(env=ENV, runner=self.az.read)
        self.assertEqual(set(missing), set(stage.CORE))
        self.assertEqual(set(values), set(stage.CORE))
        self.assertFalse(missing_cors)
        self.assertEqual(self.az.writes, [])
        self.assertNotEqual(self.az.original["AzureWebJobsStorage"],
                            self.az.target["AzureWebJobsStorage"])

    def test_existing_matching_value_is_not_rewritten(self):
        self.az.target["RETAIL_SUPABASE_URL"] = stage.SUPABASE
        missing, _, missing_cors = stage.plan(env=ENV, runner=self.az.read)
        self.assertFalse(missing_cors)
        self.assertEqual(set(missing), set(stage.CORE) - {"RETAIL_SUPABASE_URL"})

    def test_existing_drift_never_overwritten(self):
        self.az.target["RETAIL_SUPABASE_SERVICE_ROLE_KEY"] = "foreign" * 10
        with self.assertRaisesRegex(RuntimeError, "DRIFT"):
            stage.plan(env=ENV, runner=self.az.read)
        self.assertEqual(self.az.writes, [])

    def test_foreign_or_unverified_scope_denied(self):
        for change in ("subscription", "location", "origin"):
            azure = FakeAzure()
            setattr(azure, change, "foreign-resource")
            with self.subTest(change=change), self.assertRaises(RuntimeError):
                stage.plan(env=ENV, runner=azure.read)
            self.assertEqual(azure.writes, [])
        for key, value in (("GITHUB_REF", "refs/heads/feature"),
                           ("GITHUB_REPOSITORY", "somebody/WineShopPOS")):
            azure = FakeAzure()
            with self.assertRaisesRegex(RuntimeError, "TRUSTED"):
                stage.plan(env={**ENV, key: value}, runner=azure.read)
            self.assertEqual(azure.reads, 0)

    def test_non_five_index_denied_including_duplicate_worker(self):
        for routes in (set(), {"p0249_health", "campaign_read"},
                       set(stage.FIVE) | {"render_campaign_reel"}):
            az = FakeAzure()
            az.routes = routes
            with self.subTest(routes=routes), self.assertRaisesRegex(RuntimeError, "FIVE"):
                stage.plan(env=ENV, runner=az.read)
            self.assertEqual(az.writes, [])

    def test_wildcard_or_foreign_cors_refused(self):
        for origin in ("*", "https://foreign.example"):
            az = FakeAzure()
            az.origin = origin
            with self.subTest(origin=origin), self.assertRaisesRegex(RuntimeError, "CORS"):
                stage.plan(env=ENV, runner=az.read)
            self.assertEqual(az.writes, [])

    def test_missing_exact_frontend_cors_is_staged_without_wildcard(self):
        self.az.origin = None
        names, _, add_cors = stage.plan(env=ENV, runner=self.az.read)
        self.assertEqual(len(names), 4)
        self.assertTrue(add_cors)
        approved = {**ENV, "RGAI_Y1_CORE_CONNECTION_STAGE": stage.STAGE_CONFIRM}
        self.assertEqual(stage.run(apply=True, env=approved, reader=self.az.read,
                                   writer=self.az.write), ())
        self.assertEqual(set(self.az.writes[0]), set(stage.CORE))
        self.assertEqual(self.az.writes[1], ("CORS",))
        self.assertEqual(self.az.origin, stage.FRONTEND)
        self.assertEqual(len(self.az.writes), 2)

    def test_missing_original_value_denied(self):
        self.az.original.pop("RETAIL_STORAGE")
        with self.assertRaisesRegex(RuntimeError, "MALFORMED"):
            stage.plan(env=ENV, runner=self.az.read)
        self.assertEqual(self.az.writes, [])

    def test_unresolved_key_vault_reference_denied(self):
        self.az.original["RETAIL_STORAGE"] = "@Microsoft.KeyVault(SecretUri=https://example)"
        with self.assertRaisesRegex(RuntimeError, "CROSS_IDENTITY"):
            stage.plan(env=ENV, runner=self.az.read)

    def test_apply_requires_distinct_protected_confirmation(self):
        with self.assertRaisesRegex(RuntimeError, "CONFIRMATION"):
            stage.run(apply=True, env=ENV, reader=self.az.read,
                      writer=self.az.write)
        self.assertEqual(self.az.writes, [])

    def test_apply_writes_exact_missing_set_and_readback_then_idempotent(self):
        approved = {**ENV, "RGAI_Y1_CORE_CONNECTION_STAGE": stage.STAGE_CONFIRM}
        self.assertEqual(stage.run(apply=True, env=approved, reader=self.az.read,
                                   writer=self.az.write), ())
        self.assertEqual(len(self.az.writes), 1)
        self.assertEqual(set(self.az.writes[0]), set(stage.CORE))
        self.assertEqual(stage.run(apply=True, env=approved, reader=self.az.read,
                                   writer=self.az.write), ())
        self.assertEqual(len(self.az.writes), 1)

    def test_private_payload_deleted_after_success_and_idempotent_apply(self):
        approved = {**ENV, "RGAI_Y1_CORE_CONNECTION_STAGE": stage.STAGE_CONFIRM}
        self.assertEqual(stage.run(apply=True, env=approved, reader=self.az.read,
                                   writer=self.az.write), ())
        self.assertEqual(len(self.az.payload_paths), 1)
        for path in self.az.payload_paths:
            self.assertFalse(path.exists())
            self.assertFalse(path.parent.exists())
        self.assertEqual(stage.run(apply=True, env=approved, reader=self.az.read,
                                   writer=self.az.write), ())
        self.assertEqual(len(self.az.payload_paths), 1)

    def test_private_payload_deleted_after_azure_failure(self):
        self.az.fail_settings = True
        approved = {**ENV, "RGAI_Y1_CORE_CONNECTION_STAGE": stage.STAGE_CONFIRM}
        with self.assertRaisesRegex(RuntimeError, "PROTECTED_DEV_STAGE_WRITE_FAILED"):
            stage.run(apply=True, env=approved, reader=self.az.read,
                      writer=self.az.write)
        self.assertEqual(len(self.az.payload_paths), 1)
        self.assertFalse(self.az.payload_paths[0].exists())
        self.assertFalse(self.az.payload_paths[0].parent.exists())
        self.assertFalse(any(name in self.az.target for name in stage.CORE))

    def test_failed_settings_stage_never_changes_cors(self):
        self.az.origin = None
        self.az.fail_settings = True
        approved = {**ENV, "RGAI_Y1_CORE_CONNECTION_STAGE": stage.STAGE_CONFIRM}
        with self.assertRaisesRegex(RuntimeError, "PROTECTED_DEV_STAGE_WRITE_FAILED"):
            stage.run(apply=True, env=approved, reader=self.az.read,
                      writer=self.az.write)
        self.assertEqual(len(self.az.writes), 1)
        self.assertNotIn(("CORS",), self.az.writes)
        self.assertIsNone(self.az.origin)

    def test_cors_failure_preserves_staged_settings_and_retries_idempotently(self):
        self.az.origin = None
        self.az.fail_cors = True
        approved = {**ENV, "RGAI_Y1_CORE_CONNECTION_STAGE": stage.STAGE_CONFIRM}
        with self.assertRaisesRegex(RuntimeError, "PROTECTED_DEV_CORS_WRITE_FAILED"):
            stage.run(apply=True, env=approved, reader=self.az.read,
                      writer=self.az.write)
        self.assertEqual(set(self.az.target).intersection(stage.CORE), set(stage.CORE))
        self.assertIsNone(self.az.origin)
        self.assertEqual(self.az.writes[-1], ("CORS",))
        self.az.fail_cors = False
        self.assertEqual(stage.run(apply=True, env=approved, reader=self.az.read,
                                   writer=self.az.write), ())
        self.assertEqual(len(self.az.writes), 3)
        self.assertEqual(self.az.writes[-1], ("CORS",))
        self.assertEqual(self.az.origin, stage.FRONTEND)

    def test_writer_never_accepts_unapproved_settings(self):
        with self.assertRaisesRegex(RuntimeError, "UNAPPROVED"):
            stage._write_missing({"RETAIL_PRODUCTION_SECRET": "unsafe"},
                                 runner=self.az.write)
        self.assertEqual(self.az.writes, [])


if __name__ == "__main__":
    unittest.main()
