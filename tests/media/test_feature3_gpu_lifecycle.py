"""Feature3 GPU lifecycle: mocked CLI only, never an actual Azure start."""
from pathlib import Path
from types import SimpleNamespace
from uuid import uuid4
import json
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts/ops"))
from feature3_flux_gpu import execute, GPUControlDenied

SUB = str(uuid4())
JOB = "rgai-feature3-flux-job"
ENV_ID = ("/subscriptions/" + SUB + "/resourceGroups/rg-retailgrowth-dev/providers/"
          "Microsoft.App/managedEnvironments/rgai-f5-gpu-canary-eastus")
GOOD_JOB = {
    "tags": {"project": "retailgrowthai", "environment": "dev", "feature": "feature3"},
    "properties": {
        "environmentId": ENV_ID,
        "configuration": {
            "triggerType": "Manual", "replicaTimeout": 900, "replicaRetryLimit": 0,
            "manualTriggerConfig": {"parallelism": 1, "replicaCompletionCount": 1},
        },
        "template": {
            "containers": [{"image": "registry.invalid/feature3-flux@sha256:" + "a" * 64}],
        },
    },
}


class GPUControls(unittest.TestCase):
    def setUp(self):
        self.calls = []
        self.data = GOOD_JOB
        self.executions = []
        self.env = {"RETAIL_FEATURE3_GPU_ENABLED": "1",
                    "RETAIL_FEATURE3_FLUX_START_APPROVED": "YES"}

    def runner(self, argv, **kwargs):
        self.calls.append(argv)
        if argv[1:3] == ["account", "show"]:
            val = {"id": SUB}
        elif argv[1:4] == ["containerapp", "job", "show"]:
            val = self.data
        elif argv[1:5] == ["containerapp", "job", "execution", "list"]:
            val = self.executions
        elif argv[1:4] == ["containerapp", "job", "start"]:
            val = {"name": "running-1"}
        elif argv[1:4] == ["containerapp", "job", "stop"]:
            val = {"name": "running-1"}
        else:
            raise AssertionError("Unknown or unsafe az command: " + str(argv))
        return SimpleNamespace(returncode=0, stdout=json.dumps(val), stderr="")

    def args(self, action="start", **kwargs):
        obj = {
            "action": action, "subscription": SUB, "job": JOB,
            "rate_usd_per_sec": "0.0005", "max_usd": "0.50",
            "execute": False, "execution": None,
        }
        obj.update(kwargs)
        return SimpleNamespace(**obj)

    def invoke(self, action="start", **kwargs):
        return execute(self.args(action, **kwargs), runner=self.runner, environ=self.env)

    def test_default_dry_run_never_calls_azure(self):
        p = self.invoke()
        self.assertEqual(p["mode"], "DRY_RUN")
        self.assertEqual(p["worst_case_usd"], "0.4500")
        self.assertEqual(self.calls, [])
        p = self.invoke("stop", execution="running-1")
        self.assertEqual(p["mode"], "DRY_RUN")
        self.assertEqual(self.calls, [])

    def test_disabled_gpu_does_not_even_lookup_job(self):
        for key in ("RETAIL_FEATURE3_GPU_ENABLED", "RETAIL_FEATURE3_FLUX_START_APPROVED"):
            old = self.env.pop(key)
            with self.subTest(key=key), self.assertRaises(GPUControlDenied):
                self.invoke(execute=True)
            self.env[key] = old
        self.assertEqual(self.calls, [])

    def test_invalid_subscription_cost_and_max_cap_denied_before_az(self):
        for changes in ({"subscription": "not-a-uuid"}, {"rate_usd_per_sec": "NaN"},
                        {"rate_usd_per_sec": "0.5", "max_usd": "2.50"},
                        {"max_usd": "3.0"}, {"job": "invalid JOB"}):
            with self.subTest(changes=changes), self.assertRaises(GPUControlDenied):
                self.invoke(execute=True, **changes)
        self.assertEqual(self.calls, [])

    def test_existing_exact_job_one_execution_only(self):
        receipt = self.invoke(execute=True)
        self.assertEqual(receipt["result"], "COMMAND_SUBMITTED_NOT_VERIFIED")
        self.assertTrue(any(x[1:4] == ["containerapp", "job", "start"] for x in self.calls))
        self.assertFalse(any("create" in x for argv in self.calls for x in argv))

    def test_no_duplicate_or_unknown_job_execution(self):
        for state in ("Running", "Pending", "Unknown"):
            self.calls.clear()
            self.executions = [{"name": "running-1", "status": state}]
            with self.subTest(state=state), self.assertRaises(GPUControlDenied):
                self.invoke(execute=True)
            self.assertFalse(any(x[1:4] == ["containerapp", "job", "start"] for x in self.calls))

    def test_wrong_tenant_job_metadata_or_mutable_image_denied(self):
        bad = [
            {"tags": {"project": "other", "environment": "dev", "feature": "feature3"}},
            {"properties": {**GOOD_JOB["properties"], "environmentId": "unrelated"}},
            {"properties": {**GOOD_JOB["properties"], "configuration": {
                **GOOD_JOB["properties"]["configuration"], "replicaRetryLimit": 1}}},
            {"properties": {**GOOD_JOB["properties"], "template": {
                "containers": [{"image": "latest:unreviewed"}]}}},
        ]
        for patch in bad:
            self.data = {**GOOD_JOB, **patch}
            self.calls.clear()
            with self.subTest(patch=str(patch)[:50]), self.assertRaises(GPUControlDenied):
                self.invoke(execute=True)
            self.assertFalse(any(x[1:4] == ["containerapp", "job", "start"] for x in self.calls))
        self.data = GOOD_JOB

    def test_exact_stop_allowed_even_when_gpu_start_disabled(self):
        self.env.clear()
        self.executions = [{"name": "running-1", "status": "Running"}]
        out = self.invoke("stop", execute=True, execution="running-1")
        self.assertEqual(out["result"], "COMMAND_SUBMITTED_NOT_VERIFIED")
        cmd = next(x for x in self.calls if x[1:4] == ["containerapp", "job", "stop"])
        self.assertIn("--job-execution-name", cmd)
        self.assertEqual(cmd[cmd.index("--job-execution-name") + 1], "running-1")

    def test_stop_requires_named_execution_and_does_not_bulk_stop(self):
        with self.assertRaises(GPUControlDenied):
            self.invoke("stop", execute=True)
        with self.assertRaises(GPUControlDenied):
            self.invoke("stop", execute=True, execution="foreign-run")
        self.assertFalse(any(x[1:4] == ["containerapp", "job", "stop"] for x in self.calls))

    def test_completed_stop_is_noop(self):
        self.executions = [{"name": "old-run", "status": "Succeeded"}]
        out = self.invoke("stop", execute=True, execution="old-run")
        self.assertEqual(out["result"], "ALREADY_TERMINAL")
        self.assertFalse(any(x[1:4] == ["containerapp", "job", "stop"] for x in self.calls))


if __name__ == "__main__":
    unittest.main()
