"""No-cloud Azure GPU VM quota negative tests: SKU listing != capacity."""
import sys
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/"scripts"/"ci"))
from feature3_vm_gpu_probe import capacity

def row(name,limit,used=0):return {"name":{"value":name},"limit":limit,"currentValue":used}
def sku(name,blocked=False):return {"name":name,"restrictions":[{"type":"Location","reasonCode":"NotAvailableForSubscription"}] if blocked else []}

class VmQuotaTests(unittest.TestCase):
 def test_exact_gpu_family_and_regional_quota_can_be_eligible(self):
  usage=[row("cores",10),row("standardNVADSA10v5Family",6),row("standardNCasT4v3Family",4)]
  usage[0]["name"]["value"]="cores";usage.append(row("Total Regional vCPUs",10))
  result=capacity(usage,[sku("Standard_NV6ads_A10_v5"),sku("Standard_NC4as_T4_v3")],"eastus")
  self.assertEqual(len(result["gpu_vm_candidates"]),2)
  self.assertTrue(all(v["passes_quota_for_review"] for v in result["gpu_vm_candidates"]))
  self.assertTrue(all(not v["vm_created"] for v in result["gpu_vm_candidates"]))
 def test_unrestricted_sku_not_usable_with_zero_family_quota(self):
  result=capacity([row("Total Regional vCPUs",10),row("standardNVADSA10v5Family",0)],
     [sku("Standard_NV6ads_A10_v5")],"eastus")
  nv=next(x for x in result["gpu_vm_candidates"] if x["sku"].startswith("Standard_NV"))
  self.assertFalse(nv["passes_quota_for_review"])
  self.assertTrue(nv["sku_unrestricted"])
  self.assertEqual(nv["gpu_family_vcpus_remaining"],0)
 def test_insufficient_regional_quota_and_sku_restriction(self):
  result=capacity([row("Total Regional vCPUs",3),row("standardNVADSA10v5Family",36)],
     [sku("Standard_NV6ads_A10_v5",blocked=True)],"centralindia")
  self.assertFalse(result["gpu_vm_candidates"][1]["passes_quota_for_review"])
 def test_missing_or_invalid_input_rejected(self):
  for region in ("nonsense","wineshoppos"):
   with self.assertRaises(ValueError):capacity([],[],region)
  with self.assertRaises(ValueError):capacity({},[],"eastus")
if __name__=="__main__":unittest.main()
