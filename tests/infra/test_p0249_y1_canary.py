"""No-Azure regression tests for isolated Y1 hosting control plan."""
import ast
import os
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "ops"))
import p0249_y1_canary_guard as guard


def resource_id(kind, name):
    return ("/subscriptions/00000000-0000-4000-8000-000000000000"
            "/resourceGroups/rg-retailgrowth-dev/providers/Microsoft.Web/"
            + kind + "/" + name)


class Y1CanaryGuardTests(unittest.TestCase):
    def test_exact_two_arm_creations(self):
        data = {"changes": [
            {"changeType": "Create", "resourceId":
             resource_id("serverfarms", guard.PLAN)},
            {"changeType": "Create", "resourceId":
             resource_id("sites", guard.SITE)},
            {"changeType": "NoChange", "resourceId":
             resource_id("sites", guard.FLEX_SITE)},
        ]}
        self.assertTrue(guard.expected_two_creations(data))

    def test_reject_modification_of_original_flex(self):
        data = {"changes": [
            {"changeType": "Create", "resourceId": resource_id("sites", guard.SITE)},
            {"changeType": "Create", "resourceId": resource_id("serverfarms", guard.PLAN)},
            {"changeType": "Modify", "resourceId": resource_id("sites", guard.FLEX_SITE)},
        ]}
        with self.assertRaises(RuntimeError):
            guard.expected_two_creations(data)

    def test_reject_extra_creates_even_in_dev_rg(self):
        data = {"changes": [
            {"changeType": "Create", "resourceId": resource_id("sites", guard.SITE)},
            {"changeType": "Create", "resourceId": resource_id("serverfarms", guard.PLAN)},
            {"changeType": "Create", "resourceId": resource_id("sites", "bad-extra")},
        ]}
        with self.assertRaises(RuntimeError):
            guard.expected_two_creations(data)

    def test_reject_missing_one_resource(self):
        with self.assertRaises(RuntimeError):
            guard.expected_two_creations({"changes": [
                {"changeType": "Create", "resourceId": resource_id("sites", guard.SITE)}
            ]})

    def test_preflight_refuses_existing_canary(self):
        with patch.object(guard, "group_scoped", return_value="dummy"), \
             patch.object(guard, "command", return_value=[
                 {"name": guard.SITE, "type": "Microsoft.Web/sites"}
             ]) as azure, \
             self.assertRaises(RuntimeError):
            guard.preflight()
        self.assertEqual(azure.call_count, 1)

    def test_arm_403_cannot_be_interpreted_as_resource_absent(self):
        with patch.object(guard, "group_scoped", return_value="dummy"), \
             patch.object(guard, "command", side_effect=RuntimeError("403")) as azure, \
             self.assertRaises(RuntimeError):
            guard.preflight()
        azure.assert_called_once_with(
            "resource", "list", "-g", guard.RG,
            "--resource-type", "Microsoft.Web/sites"
        )

    def test_invalid_arm_inventory_fails_closed(self):
        for response in (None, {}, [None], [{"bad": 1}, "unexpected"]):
            with self.subTest(response=response), \
                 patch.object(guard, "command", return_value=response), \
                 self.assertRaises(RuntimeError):
                guard.assert_absent(guard.SITE, "Microsoft.Web/sites")

    def test_successful_arm_inventory_returns_empty(self):
        with patch.object(guard, "command", return_value=[
            {"name": guard.FLEX_SITE}, {"name": "unrelated"}
        ]) as azure:
            guard.assert_absent(guard.SITE, "Microsoft.Web/sites")
        azure.assert_called_once_with("resource", "list", "-g", guard.RG,
                                      "--resource-type", "Microsoft.Web/sites")

    def test_mismatched_subscription_aborts_before_rg_calls(self):
        with patch.dict(os.environ, {"RGAI_DEV_EXPECTED_SUBSCRIPTION": "expected"}), \
             patch.object(guard, "command", return_value={"id": "wrong"}) as azure, \
             self.assertRaises(RuntimeError):
            guard.group_scoped()
        azure.assert_called_once_with("account", "show")

    def test_verify_enforces_y1_sku_and_tags(self):
        with patch.object(guard, "group_scoped"), \
             patch.object(guard, "resource", side_effect=[
                 {"name":guard.SITE,"location":"centralindia",
                  "properties":{"reserved":True},
                  "tags":{"app":"RetailGrowthAI","environment":"dev",
                          "purpose":"p0249-http-ingress-isolation"}},
                 {"name":guard.PLAN,"location":"centralindia",
                  "sku":{"name":"Y1","tier":"Dynamic"}},
             ]), \
             patch.object(guard,"command",return_value={"linuxFxVersion":"PYTHON|3.12"}):
            guard.verify()

    def test_probe_requires_20_of_20_hosted_responses(self):
        results = [(200,True,0.4)] + [
            (200,True,0.5) if i % 2==0 else (404,False,0.6)
            for i in range(20)
        ]
        with patch.object(guard,"get",side_effect=results) as fetch, \
             patch.object(guard.time,"sleep"):
            guard.probe()
        self.assertEqual(fetch.call_count,21)

    def test_probe_rejects_prehandler_timeout(self):
        results = [(200, True, 0.5)] + [
            (0, False, 18.0) if i==3 else
            ((200,True,0.5) if i % 2 == 0 else (404,False,0.5))
            for i in range(20)
        ]
        with patch.object(guard,"get",side_effect=results), \
             self.assertRaises(RuntimeError):
            guard.probe()

    def test_canary_is_one_anonymous_http_route_no_jobs(self):
        source=(ROOT/"ops"/"p0249-y1-canary"/"function_app.py").read_text()
        tree=ast.parse(source)
        routes=[n for n in ast.walk(tree) if isinstance(n,ast.Call)
                and isinstance(n.func,ast.Attribute) and n.func.attr=="route"]
        self.assertEqual(len(routes),1)
        self.assertIn('route="p0249/health"',source)
        self.assertNotIn("@app.queue_trigger",source)
        self.assertNotIn("@app.timer_trigger",source)
        self.assertNotIn("Supabase",source)
        self.assertNotIn("AZURE_CLIENT_SECRET",source)

    def test_bicep_creates_only_isolated_y1_and_refers_to_existing_storage(self):
        b=(ROOT/"infra"/"azure"/"p0249-classic-y1-dev-canary.bicep").read_text()
        self.assertEqual(b.count("resource canaryPlan"),1)
        self.assertEqual(b.count("resource canaryApp"),1)
        self.assertIn("sku: {",b)
        self.assertIn("name: 'Y1'",b)
        self.assertIn("tier: 'Dynamic'",b)
        self.assertIn("resource storage 'Microsoft.Storage/storageAccounts@2023-05-01' existing",b)
        self.assertNotIn("rgai-dev-functions-d4e5ddbd",b)
        self.assertNotIn("rgai-dev-flex",b)

    def test_workflow_needs_protected_dev_and_explicit_merge_trigger(self):
        w=(ROOT/".github"/"workflows"/"p0249-dev-y1-isolated-canary-once.yml").read_text()
        self.assertIn("environment: dev",w)
        self.assertIn("id-token: write",w)
        self.assertIn("workflow_dispatch:",w)
        self.assertIn("YES-P0249-ISOLATED-Y1",w)
        self.assertIn("startsWith(github.event.head_commit.message",w)
        self.assertIn("python3 -u ops/p0249_y1_canary_guard.py preflight",w)
        self.assertIn("python3 -u ops/p0249_y1_canary_guard.py verify",w)
        self.assertIn("python3 -u ops/p0249_y1_canary_guard.py probe",w)


if __name__ == "__main__":
    unittest.main()
