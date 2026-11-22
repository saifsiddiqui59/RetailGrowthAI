"""Offline safety contract for disabled-by-default Y1 Container Apps CPU Job.

No real Azure deployment/ARM credentials or paid resources are invoked.
"""
import pathlib
import re
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[2]
BICEP = ROOT / "infra/azure/p0249-y1-cpu-render-disabled.bicep"
WORKER = ROOT / "ops/p0249-y1-cutover/cpu_render_job.py"


class Y1DisabledCpuInfraContract(unittest.TestCase):
    def test_accurate_dev_only_scope_and_manual_disabled_job(self):
        source = BICEP.read_text()
        self.assertIn("targetScope = 'resourceGroup'", source)
        self.assertIn("@allowed(['centralindia'])", source)
        self.assertIn("rgai-dev-y1-cpu-render-disabled", source)
        self.assertIn("triggerType: 'Manual'", source)
        self.assertNotIn("triggerType: 'Event'", source)
        self.assertNotIn("eventTriggerConfig:", source)
        self.assertNotIn("scale:", source)
        self.assertIn("replicaRetryLimit: 0", source)
        self.assertIn("parallelism: 1", source)
        self.assertIn("replicaTimeout: 1380", source)
        self.assertNotIn("RGAI_CPU_RENDER_SINGLE_OWNER_ACTIVATED', value:", source)
        self.assertNotIn("RGAI_CPU_RENDER_SINGLE_OWNER_ACTIVATED', secretRef:", source)

    def test_existing_shared_queue_and_private_credentials_only(self):
        source = BICEP.read_text()
        for expected in ("retailStorageConnection", "retailSupabaseServiceKey",
                         "RETAIL_STORAGE", "RETAIL_SUPABASE_SERVICE_ROLE_KEY",
                         "https://jeearzffnjbvghwjjjrf.supabase.co",
                         "retail-reel-render", "rg-retailgrowth-dev",
                         "environment: 'dev'", "@secure()",
                         "containerAppsEnvironmentId",
                         "immutableCpuImage", "image: immutableCpuImage"):
            self.assertIn(expected, source)
        self.assertEqual(source.count("@secure()"), 2)
        self.assertNotIn("WineShopPOS", source)
        self.assertNotIn("AzureWebJobsStorage", source)
        self.assertNotIn("az functionapp stop", source)
        self.assertNotIn("output ", source)

    def test_worker_still_requires_disabled_flex_and_budget(self):
        content = WORKER.read_text()
        for expected in ("VERIFIED_FLEX_RENDER_CONSUMER_DISABLED",
                         'CONTAINER_REPLICA_TIMEOUT_SECONDS = 1380',
                         'QUEUE = "retail-reel-render"',
                         'POISON_QUEUE = "retail-reel-render-poison"',
                         "preflight(os.environ)", "admin.render_status"):
            self.assertIn(expected, content)
        self.assertNotIn("create_queue(", content)
        self.assertNotIn("while True:", content)


if __name__ == "__main__":
    unittest.main()
