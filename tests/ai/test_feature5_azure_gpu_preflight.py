"""CPU-only, read-only Azure DEV GPU inventory policy tests."""
import sys
import unittest
from pathlib import Path
from unittest.mock import patch, Mock

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from feature5_motion.azure_gpu_preflight import assess_azure_a100_preflight
from feature5_motion.azure_gpu_readonly_cli import _read_az, inspect_current_dev
from feature5_motion.contracts import MotionError

SUB = "00000000-0000-4000-8000-000000000001"
RG = {"name": "rg-retailgrowth-dev", "location": "centralindia",
      "tags": {"app": "retailgrowthai", "environment": "dev"}}
ACCOUNT = {"id": SUB, "state": "Enabled"}
SUPPORTED = [{"name": "Consumption-GPU-NC24-A100"}]
ENVS = [{"name": "rgai-f5-gpu-canary-eastus", "location": "eastus",
         "provisioningState": "Succeeded",
         "tags": {"app": "RetailGrowthAI", "environment": "dev", "feature": "feature5"},
         "properties": {"workloadProfiles": [
             {"name": "Consumption", "workloadProfileType": "Consumption"}
         ]}}]
QUOTA = {"rgai-f5-gpu-canary-eastus": [
    {"name": {"value": "Managed Environment Consumption NCA100 GPUs"},
     "limit": 1, "currentValue": 0}]}


def check(**kwargs):
    params = dict(account=ACCOUNT, resource_group=RG,
                  supported_profiles=SUPPORTED, environments=ENVS,
                  usage_by_environment=QUOTA, expected_subscription_id=SUB)
    params.update(kwargs)
    return assess_azure_a100_preflight(**params)


class TestAzureGPUReadOnlyPreflight(unittest.TestCase):
    def test_matching_dev_identity_a100_profile_and_one_quota_are_inventory_only(self):
        result = check()
        self.assertEqual(result.status, "INSPECTION_PASS_ONLY")
        self.assertEqual(result.eligible_environment, "rgai-f5-gpu-canary-eastus")
        self.assertIn("No GPU has been created", " ".join(result.reasons))

    def test_wrong_subscription_or_prod_group_never_proceed(self):
        for params in ({"account": {"id": SUB[:-1]+"2", "state": "Enabled"}},
                       {"account": {"id": SUB, "state": "Disabled"}},
                       {"resource_group": {"name": "rg-retailgrowth-prod",
                                           "location": "centralindia", "tags": RG["tags"]}},
                       {"resource_group": {"name": RG["name"], "location": "centralindia",
                                           "tags": {"app": "retailgrowthai", "environment": "prod"}}}):
            with self.subTest(params=params), self.assertRaises(MotionError):
                check(**params)

    def test_t4_only_central_india_does_not_count_as_a100(self):
        self.assertEqual(check(supported_profiles=[{"name": "Consumption-GPU-T4"}]).status, "BLOCKED")
        e = [{"name": "rgai-centralindia", "location": "centralindia",
              "provisioningState": "Succeeded", "properties": {"workloadProfiles": [
                  {"workloadProfileType": "Consumption-GPU-T4"}]}}]
        # A T4-only environment in India does not supply the required
        # East US A100 environment; region-supported quota inspection still
        # needs a new, empty East US workload-profiles environment.
        self.assertEqual(check(environments=e).status, "ENVIRONMENT_REQUIRED")

    def test_no_env_or_duplicates_or_exhausted_quota_block(self):
        self.assertEqual(check(environments=[]).status, "ENVIRONMENT_REQUIRED")
        self.assertEqual(check(environments=ENVS + ENVS).status, "BLOCKED")
        self.assertEqual(check(usage_by_environment={}).status, "BLOCKED")
        exhausted = {"rgai-f5-gpu-canary-eastus": [
            {"name": {"value": "Managed Environment Consumption NCA100 GPUs"},
             "limit": 1, "currentValue": 1}]}
        self.assertEqual(check(usage_by_environment=exhausted).status, "BLOCKED")

    def test_wrong_env_tags_or_paid_gpu_profile_cannot_pass(self):
        foreign = __import__("copy").deepcopy(ENVS)
        foreign[0]["tags"]["environment"] = "prod"
        self.assertEqual(check(environments=foreign).status, "BLOCKED")
        paid = __import__("copy").deepcopy(ENVS)
        paid[0]["properties"]["workloadProfiles"].append(
            {"name": "A100", "workloadProfileType": "Consumption-GPU-NC24-A100"})
        self.assertEqual(check(environments=paid).status, "BLOCKED")

    def test_nonpositive_or_invalid_quota_blocks(self):
        for value in ("nan", "junk", -1, 1):
            usage = {"rgai-f5-gpu-canary-eastus": [
                {"name": {"value": "Managed Environment Consumption NCA100 GPUs"},
                 "limit": 1, "currentValue": value}]}
            self.assertEqual(check(usage_by_environment=usage).status, "BLOCKED")

    def test_nonfinite_fractional_boolean_or_missing_quota_never_passes(self):
        # These are untrusted Azure CLI JSON snapshots, not actual GPU quotas.
        for field, value in (
            ("limit", float("inf")), ("limit", "1e309"),
            ("limit", "NaN"), ("limit", True),
            ("limit", 1.5), ("limit", -1),
            ("currentValue", float("inf")), ("currentValue", "-Infinity"),
            ("currentValue", False), ("currentValue", 0.5),
            ("currentValue", 1e309), ("currentValue", None),
        ):
            row = {"name": {"value": "Managed Environment Consumption NCA100 GPUs"},
                   "limit": 2, "currentValue": 0}
            row[field] = value
            with self.subTest(field=field, value=value):
                self.assertEqual(check(usage_by_environment={
                    "rgai-f5-gpu-canary-eastus": [row]}).status, "BLOCKED")
        missing_usage = {"name": {"value": "Managed Environment Consumption NCA100 GPUs"},
                         "limit": 2}
        self.assertEqual(check(usage_by_environment={
            "rgai-f5-gpu-canary-eastus": [missing_usage]}).status, "BLOCKED")
        self.assertEqual(check(usage_by_environment=[]).status, "BLOCKED")

    def test_finite_integral_quota_fallback_value_is_inventory_only(self):
        row = {"name": {"value": "Managed Environment Consumption NCA100 GPUs"},
               "limit": "2", "value": "1"}
        self.assertEqual(check(usage_by_environment={
            "rgai-f5-gpu-canary-eastus": [row]}).status, "INSPECTION_PASS_ONLY")

    def test_readonly_cli_disallows_create_or_delete_invocations(self):
        with patch("feature5_motion.azure_gpu_readonly_cli.subprocess.run") as run:
            for operation in (("containerapp", "job", "create"),
                              ("group", "delete"),
                              ("containerapp", "env", "update"),
                              ("account", "set")):
                with self.subTest(operation=operation), self.assertRaises(MotionError):
                    _read_az(*operation)
            run.assert_not_called()

    def test_cli_inventory_uses_only_five_allowed_az_calls(self):
        docs = [ACCOUNT, RG, SUPPORTED, ENVS, QUOTA["rgai-f5-gpu-canary-eastus"]]
        calls = []
        def fake_run(cmd, **kwargs):
            calls.append(cmd)
            return Mock(stdout=__import__("json").dumps(docs[len(calls)-1]))
        with patch("feature5_motion.azure_gpu_readonly_cli.subprocess.run", side_effect=fake_run):
            result = inspect_current_dev(expected_subscription_id=SUB)
        self.assertEqual(result.status, "INSPECTION_PASS_ONLY")
        self.assertEqual(len(calls), 5)
        self.assertTrue(all(c[0] == "az" and
                            not any(t in ("create", "start", "update", "delete", "apply", "deploy")
                                    for t in c) for c in calls))

    def test_cli_account_mismatch_stops_before_resource_queries(self):
        bad = {"id": "00000000-0000-4000-8000-000000000002", "state": "Enabled"}
        with patch("feature5_motion.azure_gpu_readonly_cli.subprocess.run",
                   return_value=Mock(stdout=__import__("json").dumps(bad))) as runner:
            with self.assertRaises(MotionError):
                inspect_current_dev(expected_subscription_id=SUB)
            runner.assert_called_once()


if __name__ == "__main__":
    unittest.main()
