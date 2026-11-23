"""Flex Consumption runtime settings must be in functionAppConfig, not app settings."""
from pathlib import Path
import unittest

ROOT=Path(__file__).resolve().parents[2]
BICEP=ROOT/"infra/azure/feature4-cpu-worker-dev.bicep"
WORKFLOW=ROOT/".github/workflows/retail-dev-feature4-cpu-host-once.yml"


class F4FlexRuntimeConfigTests(unittest.TestCase):
    def test_no_platform_managed_or_forbidden_runtime_app_settings(self):
        source=BICEP.read_text()
        self.assertNotIn("{ name: 'FUNCTIONS_WORKER_RUNTIME'",source)
        self.assertNotIn("{ name: 'FUNCTIONS_EXTENSION_VERSION'",source)
        self.assertIn("functionAppConfig: {",source)
        self.assertIn("runtime: {",source)
        self.assertIn("name: 'python'",source)
        self.assertIn("version: '3.11'",source)
        self.assertIn("maximumInstanceCount: 1",source)
        self.assertIn("instanceMemoryMB: 2048",source)
        self.assertIn("RETAIL_FEATURE4_CPU_WORKER_ENABLED', value: 'false'",source)
        self.assertIn("RETAIL_FEATURE4_CPU_RENDER_ENABLED', value: 'false'",source)

    def test_failing_partial_deployment_must_not_be_adopted_without_proof(self):
        workflow=WORKFLOW.read_text()
        self.assertIn("Reject any existing app and verify only tagged partial DEV plan/container",workflow)
        self.assertIn("F4 app already exists; no mutation",workflow)
        self.assertIn("verify_tagged_partial_plan",workflow)
        self.assertIn("verify_private_existing_container",workflow)
        self.assertIn("f4cpu-partial-safe-state.json",workflow)
        self.assertIn("required_reuse_action(action,previously_present)",workflow)
        self.assertIn("environment: dev",workflow)
        self.assertIn("if rid not in allowed:",workflow)
        self.assertIn("if allowed[0] not in created or allowed[1] not in observed or allowed[2] not in observed",workflow)
        self.assertIn("az deployment group what-if",workflow)
        self.assertNotIn("az role assignment create",workflow)


if __name__=="__main__":
    unittest.main()
