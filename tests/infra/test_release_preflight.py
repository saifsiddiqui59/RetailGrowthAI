"""Fail-closed, zero-Azure preflight tests; all inventory values are synthetic."""
import importlib.util
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location("azure_release_preflight",
    ROOT / "scripts/deploy/release_preflight.py")
validator = importlib.util.module_from_spec(spec)
spec.loader.exec_module(validator)

SUB = "11111111-1111-4111-8111-111111111111"
PRINCIPAL = "22222222-2222-4222-8222-222222222222"
RG = "rg-retailgrowth-dev"
SCOPE = f"/subscriptions/{SUB}/resourceGroups/{RG}"
ORIGIN = "https://retailgrowth-dev.example.test"
BUDGET_LIMIT = 200


def inventory():
    return {
        "subscription_id": SUB,
        "account": {"userType": "servicePrincipal", "userName": "app-client-id"},
        "resource_group": {
            "id": SCOPE, "name": RG, "location": "centralindia",
            "tags": {"app": "RetailGrowthAI", "environment": "dev"},
        },
        "role_assignments": [
            {"principalId": PRINCIPAL, "scope": SCOPE, "roleDefinitionName": "Contributor"},
        ],
        "storage": {
            "kind": "StorageV2", "sku": {"name": "Standard_LRS"},
            "location": "centralindia",
            "tags": {"app": "RetailGrowthAI", "environment": "dev"},
            "properties": {
                "allowBlobPublicAccess": False, "supportsHttpsTrafficOnly": True,
                "minimumTlsVersion": "TLS1_2",
            },
        },
        "function_app": {
            "location": "centralindia",
            "tags": {"app": "RetailGrowthAI", "environment": "dev"},
            "properties": {
                "httpsOnly": True,
                "siteConfig": {
                    "ftpsState": "Disabled", "minTlsVersion": "1.2",
                    "cors": {"allowedOrigins": [ORIGIN], "supportCredentials": False},
                },
                "functionAppConfig": {
                    "runtime": {"name": "python", "version": "3.12"},
                    "scaleAndConcurrency": {
                        "instanceMemoryMB": 2048, "maximumInstanceCount": 1,
                    },
                },
            },
        },
        "app_setting_names": list(validator.SETTINGS),
        "functions": [
            {"name": "rgai/{}".format(fn),
             "config": {"bindings": [
                 {"type": "queueTrigger", "queueName": q, "connection": "RETAIL_STORAGE"}
             ]}}
            for fn, q in validator.QUEUES.items()
        ] + [
            {"name": "rgai/recover_stale_jobs",
             "config": {"bindings": [{
                 "type": "timerTrigger", "schedule": "0 */2 * * * *",
                 "runOnStartup": False, "useMonitor": True,
             }]}}
        ],
        "queues": [{"name": "default/" + q} for q in validator.QUEUES.values()],
        "budgets": {"value": [{
            "properties": {
                "category": "Cost", "timeGrain": "Monthly", "amount": BUDGET_LIMIT,
                "notifications": {
                    "near": {"enabled": True, "threshold": 80,
                             "contactEmails": ["alerts@example.test"]},
                    "hard": {"enabled": True, "threshold": 100,
                             "contactEmails": ["alerts@example.test"]},
                },
            },
        }]},
    }


def run(snapshot, phase="runtime", **overrides):
    params = {
        "phase": phase, "subscription_id": SUB, "resource_group": RG,
        "principal_id": PRINCIPAL, "frontend_origin": ORIGIN,
        "monthly_budget_limit": BUDGET_LIMIT,
    }
    params.update(overrides)
    return validator.check(snapshot, **params)


class ReleasePreflightTests(unittest.TestCase):
    def test_iam_and_runtime_positive(self):
        self.assertEqual(run(inventory(), "iam"), [])
        self.assertEqual(run(inventory()), [])

    def test_iam_denies_wrong_subscription_scope_or_identity(self):
        for mutation in (
            lambda s: s.update(subscription_id="99999999-9999-4999-8999-999999999999"),
            lambda s: s["role_assignments"].clear(),
            lambda s: s["resource_group"]["tags"].update(environment="prod"),
            lambda s: s["account"].update(userType="user"),
            lambda s: s["role_assignments"][0].update(scope=f"/subscriptions/{SUB}"),
        ):
            snapshot = inventory()
            mutation(snapshot)
            with self.subTest(mutation=mutation):
                self.assertTrue(run(snapshot, "iam"))

    def test_subscription_wide_owner_contributor_or_custom_role_blocks(self):
        for role in ("Owner", "Contributor", "Unreviewed Custom Role"):
            snapshot = inventory()
            snapshot["role_assignments"].append({
                "roleDefinitionName": role, "scope": f"/subscriptions/{SUB}",
                "principalId": PRINCIPAL,
            })
            with self.subTest(role=role):
                self.assertIn("Unexpected inherited or out-of-group permission for deployment identity",
                              run(snapshot, "iam"))

    def test_inherited_subscription_reader_can_coexist_with_rg_contributor(self):
        snapshot = inventory()
        snapshot["role_assignments"].append({
            "roleDefinitionName": "Reader", "scope": f"/subscriptions/{SUB}",
            "principalId": PRINCIPAL,
        })
        self.assertEqual(run(snapshot, "iam"), [])

    def test_runtime_requires_every_queue_and_poison_trigger(self):
        for missing in validator.QUEUES:
            snapshot = inventory()
            snapshot["functions"] = [f for f in snapshot["functions"]
                                      if not f["name"].endswith("/" + missing)]
            with self.subTest(missing=missing):
                self.assertTrue(any("queue/poison trigger" in i for i in run(snapshot)))

    def test_timer_must_be_monitored_and_never_run_on_startup(self):
        snapshot = inventory()
        snapshot["functions"][-1]["config"]["bindings"][0]["runOnStartup"] = True
        self.assertTrue(any("timer" in i for i in run(snapshot)))

    def test_no_missing_poison_arm_queues(self):
        snapshot = inventory()
        snapshot["queues"].pop()
        self.assertTrue(any("queue resources" in i for i in run(snapshot)))

    def test_runtime_rejects_risky_flex_config_and_cors(self):
        for mutation in (
            lambda s: s["function_app"]["properties"]["functionAppConfig"]["scaleAndConcurrency"].update(maximumInstanceCount=10),
            lambda s: s["function_app"]["properties"]["functionAppConfig"]["scaleAndConcurrency"].update(alwaysReady=[{"name": "http", "instanceCount": 1}]),
            lambda s: s["function_app"]["properties"]["siteConfig"]["cors"].update(allowedOrigins=["*"]),
            lambda s: s["function_app"]["properties"]["siteConfig"].update(ftpsState="AllAllowed"),
            lambda s: s["storage"]["properties"].update(allowBlobPublicAccess=True),
        ):
            snapshot = inventory()
            mutation(snapshot)
            with self.subTest(mutation=mutation):
                self.assertTrue(run(snapshot))

    def test_runtime_requires_backend_keys_but_never_values(self):
        snapshot = inventory()
        snapshot["app_setting_names"].remove("RETAIL_SUPABASE_SERVICE_ROLE_KEY")
        self.assertTrue(any("app settings" in i for i in run(snapshot)))
        snapshot = inventory()
        snapshot["app_setting_names"].append("VITE_SUPABASE_SERVICE_ROLE_KEY")
        self.assertTrue(any("VITE_" in i for i in run(snapshot)))

    def test_cost_budget_requires_80_and_100_alerts_in_approved_amount(self):
        for mutation in (
            lambda s: s["budgets"]["value"].clear(),
            lambda s: s["budgets"]["value"][0]["properties"].update(amount=10000),
            lambda s: s["budgets"]["value"][0]["properties"]["notifications"]["hard"].update(enabled=False),
            lambda s: s["budgets"]["value"][0]["properties"]["notifications"]["near"].update(contactEmails=[]),
        ):
            snapshot = inventory()
            mutation(snapshot)
            with self.subTest(mutation=mutation):
                self.assertTrue(any("budget" in i for i in run(snapshot)))
        self.assertTrue(run(inventory(), monthly_budget_limit=None))

    def test_frontend_origin_must_be_exact_https(self):
        for origin in ("http://retailgrowth-dev.example.test", "https://*.example.test",
                       "https://example.test/path", "https://user:pass@example.test"):
            with self.subTest(origin=origin):
                self.assertTrue(run(inventory(), frontend_origin=origin))

    def test_preflight_script_does_not_contain_mutating_azure_commands(self):
        shell = (ROOT / "scripts/deploy/azure-readonly-preflight.sh").read_text()
        self.assertIn("az role assignment list", shell)
        self.assertIn("az rest --method get", shell)
        self.assertIn("trap 'rm -rf", shell)
        for verb in ("az deployment group create", "az functionapp deploy",
                     "az role assignment create", "az storage queue create"):
            self.assertNotIn(verb, shell)


class RollbackGuardTests(unittest.TestCase):
    def test_guard_rejects_missing_rollback_and_same_artifact(self):
        import importlib.util
        from tempfile import TemporaryDirectory
        import struct
        path = ROOT / "scripts/deploy/rollback_guard.py"
        spec = importlib.util.spec_from_file_location("rgai_rollback_guard", path)
        rollback = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(rollback)
        package_spec = importlib.util.spec_from_file_location(
            "rgai_test_package", ROOT / "scripts/deploy/package.py")
        package = importlib.util.module_from_spec(package_spec)
        package_spec.loader.exec_module(package)
        entries = package.source_files()
        elf = bytearray(100_000)
        elf[:7] = b"\x7fELF\x02\x01\x01"
        struct.pack_into("<H", elf, 18, 62)
        struct.pack_into("<Q", elf, 32, 64)
        struct.pack_into("<HH", elf, 54, 56, 1)
        struct.pack_into("<I", elf, 64, 1)
        entries.update({
            "bin/ffmpeg": bytes(elf), "bin/ffprobe": bytes(elf),
            "bin/THIRD_PARTY_NOTICES.txt": b"synthetic test fixture, not licensed production",
        })
        with TemporaryDirectory() as temp:
            first = Path(temp) / "first.zip"
            second = Path(temp) / "second.zip"
            package.write_zip(first, entries)
            entries["ai_agents/__init__.py"] += b"\n# distinct synthetic release\n"
            package.write_zip(second, entries)
            with self.assertRaises(ValueError):
                rollback.verify_pair(second, None, False)
            with self.assertRaises(ValueError):
                rollback.verify_pair(second, first, True)
            with self.assertRaises(ValueError):
                rollback.verify_pair(first, first, False)
            digest, previous = rollback.verify_pair(second, first, False)
            self.assertEqual(len(digest), 64)
            self.assertEqual(len(previous), 64)
            self.assertNotEqual(digest, previous)
            digest, previous = rollback.verify_pair(first, None, True)
            self.assertEqual(len(digest), 64)
            self.assertIsNone(previous)


if __name__ == "__main__":
    unittest.main()
