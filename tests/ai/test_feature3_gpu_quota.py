"""No-cloud negative coverage for T4 quota; Feature5 A100=0 is irrelevant."""
import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts" / "ci"))
from feature3_gpu_quota import probe_feature3_t4, CapacityBlocked

ENV = {
 "name":"rgai-f5-gpu-canary-eastus","location":"East US",
 "properties":{"provisioningState":"Succeeded","workloadProfiles":[
    {"name":"Consumption","workloadProfileType":"Consumption"}]}
}
def quota(t4=1,used=0):
 return [{"name":{"value":"ManagedEnvironmentConsumptionNCA100Gpus"},"limit":0,"currentValue":0},
         {"name":{"value":"ManagedEnvironmentConsumptionT4Gpus"},"limit":t4,"currentValue":used}]
class Feature3GpuQuotaTests(unittest.TestCase):
 def test_existing_feature5_environment_reused_if_t4_available(self):
  r=probe_feature3_t4(ENV,quota())
  self.assertTrue(r["eligible_for_future_deployment_review"])
  self.assertFalse(r["gpu_allocated_by_this_check"])
  self.assertFalse(r["deployment_executed"])
  self.assertEqual(r["profile"],"Consumption-GPU-NC8as-T4")
 def test_no_t4_quota_does_not_assume_a100_transfer(self):
  r=probe_feature3_t4(ENV,quota(t4=0))
  self.assertFalse(r["eligible_for_future_deployment_review"])
  self.assertEqual(r["t4_available"],0)
 def test_all_capacity_used(self):
  self.assertFalse(probe_feature3_t4(ENV,quota(t4=1,used=1))["eligible_for_future_deployment_review"])
 def test_malformed_unknown_or_forged_environments_fail_closed(self):
  for e,q in (
    ({**ENV,"name":"WineShopPOS"},quota()),
    ({**ENV,"location":"centralindia"},quota()),
    ({**ENV,"properties":{**ENV["properties"],"provisioningState":"Failed"}},quota()),
    (ENV,quota()[:1]),
    (ENV,quota()+quota()[-1:]),
    (ENV,quota(t4=0,used=1)),
  ):
   with self.assertRaises(CapacityBlocked):
    probe_feature3_t4(e,q)

if __name__=="__main__": unittest.main()
