"""No-network unit checks for dedicated Feature4 DEV queue provisioning."""
import importlib.util
import json
from pathlib import Path
import unittest
from unittest.mock import Mock


ROOT = Path(__file__).resolve().parents[2]
SPEC = importlib.util.spec_from_file_location(
    "feature4_cpu_dev_queues", ROOT / "scripts" / "deploy" / "feature4_cpu_dev_queues.py"
)
gate = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(gate)


class QueueTests(unittest.TestCase):
    def setUp(self):
        self.env = {
            "RGAI_DEV_PROJECT_REF": gate.DEV_REF,
            "RETAIL_FEATURE4_CPU_QUEUE_APPLY": "YES",
            "AZURE_SUBSCRIPTION_ID": "synthetic-sub",
            "RETAIL_FEATURE4_CPU_RENDER_ENABLED": "false",
        }
        self.calls = []
        self.created = []
        self.present = set()

    def fake_cli(self, args, **kwargs):
        self.calls.append(args)
        assert args[0] == "az" and kwargs.get("check") is False
        if args[1:3] == ["account", "show"]:
            response = {"id": "synthetic-sub"}
        elif args[1:3] == ["group", "show"]:
            response = {"id": "/subscriptions/synthetic-sub/resourceGroups/rg-retailgrowth-dev",
                        "name": gate.DEV_RG, "location": "centralindia",
                        "tags": {"app": "RetailGrowthAI", "environment": "DEV"}}
        elif args[1:4] == ["storage", "account", "show"]:
            response = {
                "name": gate.DEV_STORAGE,
                "id": "/subscriptions/synthetic-sub/resourceGroups/rg-retailgrowth-dev"
                      "/providers/Microsoft.Storage/storageAccounts/" + gate.DEV_STORAGE}
        elif args[1:4] == ["storage", "queue", "exists"]:
            name = args[args.index("--name") + 1]
            response = {"exists": name in self.present}
        elif args[1:4] == ["storage", "queue", "create"]:
            name = args[args.index("--name") + 1]
            self.present.add(name)
            self.created.append(name)
            response = {"created": True}
        else:
            raise AssertionError("Unexpected Azure CLI command")
        return Mock(returncode=0, stdout=json.dumps(response), stderr="")

    def test_default_never_queries_or_writes_cloud(self):
        result = gate.stage_queues({"RGAI_DEV_PROJECT_REF": gate.DEV_REF},
                                   runner=self.fake_cli)
        self.assertFalse(result["azure_changed"])
        self.assertEqual(self.calls, [])

    def test_apply_requires_explicit_guard_before_read(self):
        for bad in ({"RGAI_DEV_PROJECT_REF": gate.DEV_REF},
                    {"RGAI_DEV_PROJECT_REF": "foreign",
                     "RETAIL_FEATURE4_CPU_QUEUE_APPLY": "YES"}):
            with self.assertRaises(gate.QueueGateError):
                gate.stage_queues(bad, apply=True, runner=self.fake_cli)
        self.assertEqual(self.calls, [])

    def test_two_only_new_queues_created(self):
        result = gate.stage_queues(self.env, apply=True, runner=self.fake_cli)
        self.assertTrue(result["azure_changed"])
        self.assertEqual(tuple(self.created), gate.QUEUE_NAMES)
        self.assertEqual(len([a for a in self.calls if a[1:4] ==
                              ["storage", "queue", "create"]]), 2)
        self.assertTrue(all("--auth-mode" in cmd for cmd in self.calls
                            if cmd[1:3] == ["storage", "queue"]))

    def test_partial_existing_queue_denies_all_writes(self):
        self.present.add(gate.QUEUE_NAMES[0])
        with self.assertRaisesRegex(gate.QueueGateError, "Existing or partial"):
            gate.stage_queues(self.env, apply=True, runner=self.fake_cli)
        self.assertEqual(self.created, [])

    def test_render_flag_on_denies_without_azure(self):
        self.env["RETAIL_FEATURE4_CPU_RENDER_ENABLED"] = "true"
        with self.assertRaisesRegex(gate.QueueGateError, "render must remain disabled"):
            gate.stage_queues(self.env, apply=True, runner=self.fake_cli)
        self.assertEqual(self.calls, [])

    def test_wrong_subscription_blocks_queue_creation(self):
        self.env["AZURE_SUBSCRIPTION_ID"] = "foreign-sub"
        with self.assertRaisesRegex(gate.QueueGateError, "subscription mismatch"):
            gate.stage_queues(self.env, apply=True, runner=self.fake_cli)
        self.assertEqual(self.created, [])


if __name__ == "__main__":
    unittest.main()
