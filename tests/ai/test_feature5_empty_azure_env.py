"""Offline checks for one-resource, zero-active-compute Azure DEV plan."""
import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from feature5_motion.empty_env_template import (
    TARGET_ENV, TARGET_RG, TEMPLATE, validate_template, validate_what_if,
)
from feature5_motion.contracts import MotionError

SUB = "00000000-0000-4000-8000-000000000003"
RID = f"/subscriptions/{SUB}/resourceGroups/{TARGET_RG}/providers/Microsoft.App/managedEnvironments/{TARGET_ENV}"


class TestFeature5ZeroComputeARM(unittest.TestCase):
    def test_source_contains_only_unused_v2_consumption_environment(self):
        plan = validate_template()
        self.assertEqual(len(plan["resources"]), 1)
        resource = plan["resources"][0]
        self.assertEqual(resource["type"], "Microsoft.App/managedEnvironments")
        self.assertEqual(resource["location"], "eastus")
        self.assertEqual(resource["tags"]["environment"], "dev")
        self.assertEqual(resource["properties"]["appLogsConfiguration"], {"destination": "none"})
        self.assertEqual(resource["properties"]["workloadProfiles"], [
            {"name": "Consumption", "workloadProfileType": "Consumption"}])
        self.assertEqual(resource["name"], TARGET_ENV)
        self.assertNotIn("Microsoft.ContainerRegistry", json.dumps(plan))
        self.assertNotIn("LogAnalytics", json.dumps(plan))

    def test_billing_addons_or_prod_edits_are_rejected(self):
        original = validate_template()
        cases = []
        a = json.loads(json.dumps(original))
        a["resources"].append({"type": "Microsoft.Compute/virtualMachines"})
        cases.append(a)
        for key, value in [
            ("location", "centralindia"),
            ("properties", {"workloadProfiles": [
                {"name": "gpu", "workloadProfileType": "Consumption-GPU-NC24-A100"}]}),
            ("properties", {"appLogsConfiguration": {"destination": "log-analytics"}}),
            ("tags", {"environment": "prod"}),
        ]:
            a = json.loads(json.dumps(original))
            a["resources"][0][key] = value
            cases.append(a)
        with tempfile.TemporaryDirectory() as d:
            source = Path(d) / "changed.json"
            for case in cases:
                with self.subTest(case=case["resources"]):
                    source.write_text(json.dumps(case), encoding="utf-8")
                    with self.assertRaises(MotionError):
                        validate_template(source)

    def test_what_if_accepts_exact_new_resource_only(self):
        validate_what_if({"changes": [{"resourceId": RID, "changeType": "Create"}]}, SUB)
        for bad in (
            {"changes": []},
            {"changes": [{"resourceId": RID, "changeType": "Modify"}]},
            {"changes": [{"resourceId": RID, "changeType": "Delete"}]},
            {"changes": [{"resourceId": RID, "changeType": "Ignore"}]},
            {"changes": [{"resourceId": RID + "-other", "changeType": "Create"}]},
            {"changes": [{"resourceId": RID, "changeType": "Create"},
                         {"resourceId": RID + "2", "changeType": "Create"}]},
        ):
            with self.subTest(change=bad), self.assertRaises(MotionError):
                validate_what_if(bad, SUB)


if __name__ == "__main__":
    unittest.main()
