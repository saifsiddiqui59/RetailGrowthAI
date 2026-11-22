"""Guard the precise allowed ARM Bicep what-if resource set for new F4 CPU."""
from pathlib import Path
import unittest

WORKFLOW = Path(__file__).resolve().parents[2]/".github/workflows/retail-dev-feature4-cpu-host-once.yml"
BICEP = Path(__file__).resolve().parents[2]/"infra/azure/feature4-cpu-worker-dev.bicep"


class F4HostWhatifExplicitResourceScopeTests(unittest.TestCase):
    def test_new_worker_child_config_exact_name_only(self):
        text=WORKFLOW.read_text()
        self.assertIn("'/providers/microsoft.web/sites/rgai-dev-f4cpu-d4e5ddbd/config/web'", text)
        self.assertIn("'/providers/microsoft.web/sites/rgai-dev-f4cpu-d4e5ddbd'", text)
        self.assertIn("'/providers/microsoft.web/serverfarms/rgai-dev-f4cpu-plan'", text)
        self.assertIn("'/providers/microsoft.storage/storageaccounts/rgaid4e5ddbdf0d21d96/blobservices/default/containers/retailgrowth-f4cpu-packages'", text)
        self.assertIn("if not any(rid.endswith(v) for v in allowed)",text)
        self.assertIn("if action not in ('Create','NoChange','Ignore')",text)
        self.assertIn("if allowed[0] not in created or allowed[1] not in created",text)
        self.assertNotIn("if 'microsoft.web' in rid:",text)
        self.assertNotIn("if 'storageaccounts' in rid:",text)

    def test_whatif_diagnostic_keeps_names_out_of_logs(self):
        text=WORKFLOW.read_text()
        self.assertIn("kind='/'.join(raw[0::2])",text)
        self.assertIn("TYPE=' + kind + ' action='",text)
        self.assertNotIn("'BLOCKED: unexpected resource ' + rid",text)
        self.assertIn("raise SystemExit('BLOCKED: unexpected resource in F4 what-if')",text)

    def test_flags_and_migration_fences_not_bypassed(self):
        code=WORKFLOW.read_text()
        bicep=BICEP.read_text()
        self.assertIn("retail-feature4-cpu-render retail-feature4-cpu-render-poison",code)
        self.assertIn("environment: dev",code)
        self.assertIn("az deployment group what-if",code)
        self.assertIn("az deployment group create",code)
        self.assertIn("RETAIL_FEATURE4_CPU_WORKER_ENABLED', value: 'false'",bicep)
        self.assertIn("RETAIL_FEATURE4_CPU_RENDER_ENABLED', value: 'false'",bicep)


if __name__ == "__main__":
    unittest.main()
