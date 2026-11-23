"""Never print sensitive partial-plan fields during protected diagnostics."""
from pathlib import Path
import unittest
W=Path(__file__).resolve().parents[2]/".github/workflows/retail-dev-feature4-cpu-resume-once.yml"

class PartialPlanFieldDiagnostics(unittest.TestCase):
    def test_all_constraints_are_retained_and_only_labels_printed(self):
        x=W.read_text()
        for text in (
            "'id': str(plan.get('id') or '').lower()==scope",
            "'name': plan.get('name')=='rgai-dev-f4cpu-plan'",
            "'location': plan.get('location')=='centralindia'",
            "'tag-app': tags.get('app')=='retailgrowthai'",
            "'tag-environment': tags.get('environment')=='dev'",
            "'tag-purpose': tags.get('purpose')=='feature4-cpu-private-worker'",
            "'sku-name': sku.get('name')=='FC1'",
            "'sku-tier': sku.get('tier')=='FlexConsumption'",
            "'linux-reserved': (plan.get('properties') or {}).get('reserved') is True",
            "mismatches=sorted(",
            "BLOCKED: existing FC1 plan identity unverified fields=",
            "if mismatches:",
        ):
            self.assertIn(text,x)
        for bad in ("print(plan)","print(tags)","print(sku)","print(container)","print(os.environ)"):
            self.assertNotIn(bad,x)
        self.assertLess(x.index("mismatches=sorted("),x.index("az deployment group create"))
        self.assertIn("if allowed[0] not in created:",x)

if __name__=="__main__":
    unittest.main()
