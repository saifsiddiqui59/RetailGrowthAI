"""Static fail-closed contract for protected F4 private-trigger rollback audit."""
from pathlib import Path
import unittest
WF=Path(__file__).resolve().parents[2]/".github/workflows/retail-dev-feature4-cpu-rollback-audit-once.yml"

class F4RollbackAuditContract(unittest.TestCase):
    def test_main_only_dev_oidc_read_only(self):
        s=WF.read_text()
        for token in (
          "branches: [main]", "environment: dev", "id-token: write",
          "uses: azure/login@v3", "persist-credentials: false",
          "rg-retailgrowth-dev", "rgai-dev-f4cpu-d4e5ddbd",
          "rgai-dev-functions-d4e5ddbd", "az resource show",
          "az functionapp function list", "az functionapp config appsettings list",
          "BLOCKED: rollback failed to disable private CPU worker",
          "BLOCKED: temporary protected service key not cleared",
          "BLOCKED: original customer API active unexpectedly",
          "BLOCKED: private functions remain indexed with worker OFF",
          "expected={'feature4_cpu_render_message','feature4_cpu_poison_message','feature4_cpu_dispatch_timer'}",
        ):
            self.assertIn(token,s)
        for forbidden in ("az role assignment create","az functionapp config appsettings set",
                          "az functionapp config appsettings delete",
                          "az deployment group create","az storage queue create",
                          "--auth-mode key","schedule:","pull_request:","actions/upload-artifact"):
            self.assertNotIn(forbidden,s)
        self.assertNotIn("print(values)",s)
        self.assertNotIn("print(settings)",s)
        self.assertNotIn("print(original)",s)

if __name__=="__main__":
    unittest.main()
