"""Feature5 ARM what-if policy: no foreign change, even Ignore must be reviewed."""
import copy
import sys
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT))
from scripts.ci.feature5_arm_whatif_policy import (
    ALLOWED_IGNORED, TARGET_NAME, UnsafeWhatIf, validate_what_if,
)

SUB="00000000-0000-4000-8000-000000000007"
RG="rg-retailgrowth-dev"
PREFIX=f"/subscriptions/{SUB}/resourceGroups/{RG}/providers/"
CREATE=PREFIX+"Microsoft.App/managedEnvironments/"+TARGET_NAME


def sample():
    return {
        "status":"Succeeded","error":None,"potentialChanges":[],
        "changes":[{"changeType":"Create","resourceId":CREATE}]+[
            {"changeType":"Ignore","resourceId":PREFIX+"Microsoft.Dummy/"+tail}
            for tail in sorted(ALLOWED_IGNORED)
        ],
    }


class TestFeature5ExactARMWhatIf(unittest.TestCase):
    def test_one_create_eight_known_ignore_is_safe(self):
        self.assertEqual(validate_what_if(sample(),SUB,RG),{
            "creates":1,"ignored":8,"target":TARGET_NAME})

    def test_ignore_entries_not_authorization_to_mutate(self):
        for action in ("Modify","Delete","Deploy","NoChange","Unsupported","Create"):
            with self.subTest(action=action):
                payload=sample()
                payload["changes"][1]["changeType"]=action
                with self.assertRaises(UnsafeWhatIf):
                    validate_what_if(payload,SUB,RG)

    def test_rejects_all_extra_creates_and_missing_resource(self):
        for change in (
            {"changeType":"Create","resourceId":PREFIX+"Microsoft.Compute/virtualMachines/unexpected"},
            {"changeType":"Ignore","resourceId":PREFIX+"Microsoft.Dummy/unknown/sidecar"},
            {"changeType":"Ignore","resourceId":"/subscriptions/"+SUB+"/resourceGroups/wineshopPOS/providers/Microsoft.Dummy/sites/foo"},
            {"changeType":"Ignore","resourceId":PREFIX+"Microsoft.Dummy/"+sorted(ALLOWED_IGNORED)[0]},
        ):
            p=sample()
            p["changes"].append(change)
            with self.subTest(change=change), self.assertRaises(UnsafeWhatIf):
                validate_what_if(p,SUB,RG)
        p=sample()
        p["changes"].pop()
        with self.assertRaises(UnsafeWhatIf):
            validate_what_if(p,SUB,RG)

    def test_rejects_failed_or_uncertain_whatif(self):
        p=sample()
        for key,value in (("status","Failed"),("error",{"message":"failure"}),
                          ("potentialChanges",[{"changeType":"Modify"}]),
                          ("changes",None)):
            q=copy.deepcopy(p)
            q[key]=value
            with self.subTest(key=key),self.assertRaises(UnsafeWhatIf):
                validate_what_if(q,SUB,RG)

    def test_wrong_subscription_or_wrong_environment_blocks(self):
        with self.assertRaises(UnsafeWhatIf):
            validate_what_if(sample(),"00000000-0000-4000-8000-000000000008",RG)
        with self.assertRaises(UnsafeWhatIf):
            validate_what_if(sample(),SUB,"rg-retailgrowth-prod")
        with self.assertRaises(UnsafeWhatIf):
            validate_what_if(sample(),SUB,RG,"a100-prod")

    def test_workflow_invokes_checked_policy_and_still_no_gpu(self):
        s=(ROOT/".github/workflows/retail-dev-feature5-empty-env-once.yml").read_text()
        self.assertIn("from scripts.ci.feature5_arm_whatif_policy import validate_what_if",s)
        self.assertIn("az deployment group what-if",s)
        self.assertEqual(s.count("az deployment group create"),1)
        self.assertNotIn("az containerapp job create",s)
        self.assertIn("environment: dev",s)


if __name__=="__main__":
    unittest.main()
