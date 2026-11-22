"""Source-only positive/negative contracts for eventual Y1 CPU Event cutover.

Never runs Bicep deployment or touches Azure; protected review and live handoff
are REQUIRED before activating this candidate on the existing disabled job.
"""
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[2]
EVENT = ROOT / "infra/azure/p0249-y1-cpu-render-event-guarded.bicep"
DISABLED = ROOT / "infra/azure/p0249-y1-cpu-render-disabled.bicep"
RUNTIME = ROOT / "ops/p0249-y1-cutover/cpu_render_job.py"

class EventWorkerCutoverContract(unittest.TestCase):
    def test_event_template_is_isolated_and_explicitly_activated(self):
        source = EVENT.read_text()
        self.assertIn("targetScope = 'resourceGroup'", source)
        self.assertIn("@allowed(['centralindia'])", source)
        self.assertIn("triggerType: 'Event'", source)
        self.assertIn("eventTriggerConfig:", source)
        self.assertIn("type: 'azure-queue'", source)
        self.assertIn("queueName: 'retail-reel-render'", source)
        self.assertIn("triggerParameter: 'connection'", source)
        self.assertIn("secretRef: 'retail-storage'", source)
        self.assertIn("maxExecutions: 1", source)
        self.assertIn("minExecutions: 0", source)
        self.assertIn("pollingInterval: 60", source)
        self.assertIn("parallelism: 1", source)
        self.assertIn("replicaTimeout: 1380", source)
        self.assertIn("replicaRetryLimit: 0", source)
        self.assertIn("@secure()", source)
        self.assertIn("@allowed(['VERIFIED_FLEX_RENDER_CONSUMER_DISABLED'])", source)
        self.assertIn("RGAI_CPU_RENDER_SINGLE_OWNER_ACTIVATED", source)
        self.assertIn("value: verifiedSingleOwnerHandoff", source)
        self.assertIn("jobName string = 'rgai-dev-y1-cpu-render-disabled'", source)
        self.assertNotIn("AzureWebJobs.render_campaign_reel.Disabled=false", source)
        self.assertNotIn("Microsoft.Web/sites", source)
        self.assertNotIn("WineShopPOS", source)

    def test_default_candidate_stays_inert_and_runtime_has_longer_lease(self):
        disabled = DISABLED.read_text()
        runtime = RUNTIME.read_text()
        self.assertIn("triggerType: 'Manual'", disabled)
        self.assertNotIn("eventTriggerConfig:", disabled)
        self.assertNotIn("RGAI_CPU_RENDER_SINGLE_OWNER_ACTIVATED', value:", disabled)
        self.assertIn("VISIBILITY_SECONDS = 2100", runtime)
        self.assertIn("CONTAINER_REPLICA_TIMEOUT_SECONDS = 1380", runtime)
        self.assertIn("VISIBILITY_SECONDS <= CONTAINER_REPLICA_TIMEOUT_SECONDS", runtime)

if __name__ == "__main__":
    unittest.main()
