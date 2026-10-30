"""CPU-only tests for Feature5 Azure A100 job safety; all Azure interactions mocked."""
import os
import unittest
from unittest.mock import patch
from feature5_motion import gpu_job_control as m
from feature5_motion import shared_model_mount as models

SUB = "12345678-1234-1234-1234-123456789abc"
ENV_ID = f"/subscriptions/{SUB}/resourceGroups/{m.GROUP}/providers/Microsoft.App/managedEnvironments/{m.ENV}"

def valid_job():
    return {"name":m.JOB,"tags":{"app":"retailgrowthai","environment":"dev","feature":"feature5"},
            "properties":{"environmentId":ENV_ID,"workloadProfileName":"f5-a100",
            "configuration":{"triggerType":"Manual","replicaRetryLimit":0,"replicaTimeout":900,
                            "manualTriggerConfig":{"parallelism":1,"replicaCompletionCount":1}},
            "template":{"containers":[{"image":"example.azurecr.io/f5@sha256:" + "a"*64,
                "volumeMounts":[{"volumeName":models.VOLUME_NAME,"mountPath":models.MOUNT_PATH}]}],
                "volumes":[{"name":models.VOLUME_NAME,"storageType":"AzureFile","storageName":models.STORAGE_NAME}]}}}

def valid_env():
    return {"name":m.ENV,"location":"eastus",
            "tags":{"app":"retailgrowthai","environment":"dev","feature":"feature5"},
            "properties":{"workloadProfiles":[
                {"name":"Consumption","workloadProfileType":"Consumption"},
                {"name":"f5-a100","workloadProfileType":m.PROFILE_TYPE}]}}

class SafetyTests(unittest.TestCase):
    def setUp(self):
        self.j = valid_job()
        self.env = valid_env()
    def test_v100_guard_before_azure(self):
        with patch.object(m,"subscription") as sub:
            self.assertEqual(m.main(["start","--execute","--gpu","V100"]),3)
            sub.assert_not_called()
    def test_missing_job_is_safe_to_stop(self):
        with patch.object(m,"job",return_value=None), patch.object(m,"az") as az:
            m.stop(SUB)
            az.assert_not_called()
        with patch.object(m,"job",return_value=None),self.assertRaises(m.SafetyError):
            m.start(SUB,True,True)
    def test_fail_closed_on_unsafe_configs(self):
        def read(*args):
            if "list-usages" in args:
                return [{"name":{"value":"ManagedEnvironmentConsumptionNCA100Gpus"},
                         "limit":2,"currentValue":0}]
            if "storage" in args and "show" in args:
                return {"properties":{"azureFile":{"accountName":models.ACCOUNT,
                         "shareName":models.SHARE,"accessMode":"ReadOnly"}}}
            return self.env
        with patch.object(m,"az",side_effect=read):
            m.check_preflight(SUB,self.j)
            for key,value in [("replicaRetryLimit",1),("replicaTimeout",3600),("triggerType","Schedule")]:
                corrupt=valid_job()
                corrupt["properties"]["configuration"][key]=value
                with self.assertRaises(m.SafetyError):
                    m.check_preflight(SUB,corrupt)
            corrupt=valid_job()
            corrupt["properties"]["template"]["containers"][0]["image"]="untrusted:latest"
            with self.assertRaises(m.SafetyError):
                m.check_preflight(SUB,corrupt)
            self.env["properties"]["workloadProfiles"][1]["workloadProfileType"]="V100"
            with self.assertRaises(m.SafetyError):
                m.check_preflight(SUB,self.j)
    def test_model_mount_must_be_present_and_read_only(self):
        def azure(*args):
            if "storage" in args and "show" in args:
                return {"properties":{"azureFile":{"accountName":models.ACCOUNT,
                           "shareName":models.SHARE,"accessMode":"ReadOnly"}}}
            return self.env
        with patch.object(m, "az", side_effect=azure):
            m.check_model_share_mount(SUB, valid_job())
            bad = valid_job()
            bad["properties"]["template"]["volumes"] = []
            with self.assertRaises(m.SafetyError):
                m.check_model_share_mount(SUB, bad)
            bad = valid_job()
            bad["properties"]["template"]["containers"][0]["volumeMounts"][0]["subPath"] = "feature5"
            with self.assertRaises(m.SafetyError):
                m.check_model_share_mount(SUB, bad)
        with patch.object(m, "az", return_value={"properties":{"azureFile":{
                "accountName":models.ACCOUNT, "shareName":models.SHARE, "accessMode":"ReadWrite"}}}):
            with self.assertRaises(m.SafetyError):
                m.check_model_share_mount(SUB, valid_job())

    def test_start_is_dry_run_by_default(self):
        with patch.object(m,"job",return_value=self.j), patch.object(m,"check_preflight"),\
             patch.object(m,"executions",return_value=[]),patch.object(m,"az") as az:
            m.start(SUB,False,False)
            az.assert_not_called()
    def test_paid_start_requires_explicit_approval(self):
        with patch.object(m,"job",return_value=self.j),patch.object(m,"check_preflight"),\
             patch.object(m,"executions",return_value=[]),patch.object(m,"az") as az,\
             patch.dict(os.environ,{"RETAIL_F5_PAID_RUN_APPROVED":"NO","RETAIL_F5_MODEL_LICENSE_APPROVED":"YES"}):
            with self.assertRaises(m.SafetyError):
                m.start(SUB,True,True)
            az.assert_not_called()
        with patch.object(m,"job",return_value=self.j),patch.object(m,"check_preflight"),\
             patch.object(m,"executions",return_value=[]),patch.object(m,"az") as az,\
             patch.dict(os.environ,{"RETAIL_F5_PAID_RUN_APPROVED":"YES",
                        "RETAIL_F5_MODEL_LICENSE_APPROVED":"YES",
                        "RETAIL_F5_COST_QUOTE_CURRENCY":"USD",
                        "RETAIL_F5_COST_QUOTE_REFERENCE":"official-reviewed-quote-20261028",
                        "RETAIL_F5_QUOTED_ALL_IN_USD_PER_GPU_SECOND":"0.0001",
                        "RETAIL_F5_QUOTED_FIXED_OVERHEAD_USD":"0.01",
                        "RETAIL_F5_OWNER_APPROVED_PER_TEST_MAX_USD":"0.20",
                        "RETAIL_F5_REVIEWED_RUNTIME_IMAGE":"example.azurecr.io/f5@sha256:"+"a"*64}):
            m.start(SUB,True,True)
            self.assertEqual(az.call_args.args[:3],("containerapp","job","start"))
    def test_paid_cost_envelope_is_required_and_worst_case_bounded(self):
        values = {"RETAIL_F5_COST_QUOTE_CURRENCY":"USD",
                  "RETAIL_F5_COST_QUOTE_REFERENCE":"official-reviewed-quote-20261028",
                  "RETAIL_F5_QUOTED_ALL_IN_USD_PER_GPU_SECOND":"0.0001",
                  "RETAIL_F5_QUOTED_FIXED_OVERHEAD_USD":"0.01",
                  "RETAIL_F5_OWNER_APPROVED_PER_TEST_MAX_USD":"0.20"}
        with patch.dict(os.environ, {}, clear=True), self.assertRaises(m.SafetyError):
            m.require_priced_test_envelope(valid_job())
        with patch.dict(os.environ, values, clear=True):
            self.assertEqual(str(m.require_priced_test_envelope(valid_job())), "0.1000")
        with patch.dict(os.environ, dict(values, RETAIL_F5_OWNER_APPROVED_PER_TEST_MAX_USD="0.01"), clear=True), self.assertRaises(m.SafetyError):
            m.require_priced_test_envelope(valid_job())
        with patch.dict(os.environ, dict(values, RETAIL_F5_QUOTED_ALL_IN_USD_PER_GPU_SECOND="NaN"), clear=True), self.assertRaises(m.SafetyError):
            m.require_priced_test_envelope(valid_job())

    def test_paid_start_requires_exact_reviewed_runtime_image(self):
        j = valid_job()
        good = j["properties"]["template"]["containers"][0]["image"]
        with patch.dict(os.environ, {}, clear=True), self.assertRaises(m.SafetyError):
            m.require_approved_runtime_image(j)
        with patch.dict(os.environ, {"RETAIL_F5_REVIEWED_RUNTIME_IMAGE": good}):
            self.assertEqual(m.require_approved_runtime_image(j), good)
        with patch.dict(os.environ, {"RETAIL_F5_REVIEWED_RUNTIME_IMAGE": good.replace("a"*64, "b"*64)}), self.assertRaises(m.SafetyError):
            m.require_approved_runtime_image(j)
        with patch.dict(os.environ, {"RETAIL_F5_REVIEWED_RUNTIME_IMAGE": "example.azurecr.io/f5:latest"}), self.assertRaises(m.SafetyError):
            m.require_approved_runtime_image(j)

    def test_paid_start_fails_without_reviewed_image_even_if_price_valid(self):
        j = valid_job()
        quote = {"RETAIL_F5_PAID_RUN_APPROVED":"YES","RETAIL_F5_MODEL_LICENSE_APPROVED":"YES",
                 "RETAIL_F5_COST_QUOTE_CURRENCY":"USD",
                 "RETAIL_F5_COST_QUOTE_REFERENCE":"official-reviewed-quote-20261028",
                 "RETAIL_F5_QUOTED_ALL_IN_USD_PER_GPU_SECOND":"0.0001",
                 "RETAIL_F5_QUOTED_FIXED_OVERHEAD_USD":"0.01",
                 "RETAIL_F5_OWNER_APPROVED_PER_TEST_MAX_USD":"0.20"}
        with patch.object(m,"job",return_value=j), patch.object(m,"check_preflight"), patch.object(m,"executions",return_value=[]), patch.object(m,"az") as az, patch.dict(os.environ,quote,clear=True):
            with self.assertRaises(m.SafetyError):
                m.start(SUB,True,True)
            az.assert_not_called()

    def test_running_job_blocks_duplicate_start(self):
        with patch.object(m,"job",return_value=self.j),patch.object(m,"check_preflight"),\
             patch.object(m,"executions",return_value=[("e1","running")]),patch.object(m,"az") as az:
            with self.assertRaises(m.SafetyError):
                m.start(SUB,True,True)
            az.assert_not_called()
    def test_emergency_stop_does_not_require_valid_runtime(self):
        self.j["properties"]["configuration"]["replicaRetryLimit"]=7
        with patch.object(m,"job",return_value=self.j),patch.object(m,"executions",return_value=[]),patch.object(m,"az") as az:
            m.stop(SUB)
            self.assertEqual(az.call_args.args[:3],("containerapp","job","stop"))
    def test_unknown_execution_never_claims_stopped(self):
        with patch.object(m,"az",return_value=[{"name":"x","properties":{"status":"strange"}}]):
            with self.assertRaises(m.SafetyError):
                m.executions(SUB)
    def test_unconfirmed_stop_propagates_error(self):
        with patch.object(m,"job",return_value=self.j),patch.object(m,"executions",side_effect=m.SafetyError("unknown")),\
             patch.object(m,"az"):
            with self.assertRaises(m.SafetyError):
                m.stop(SUB)

if __name__ == "__main__":
    unittest.main()
