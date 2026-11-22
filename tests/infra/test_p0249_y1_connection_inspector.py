"""Offline-only mock of exact Y1/Flex Azure connection inspection."""
import importlib.util
import json
import os
from pathlib import Path
from types import SimpleNamespace
import sys
import unittest
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[2]
DIR=ROOT / "ops/p0249-y1-cutover"
sys.path.insert(0, str(DIR))
spec=importlib.util.spec_from_file_location("p0249_azure_connection_inspector",
                                            DIR / "inspect_azure_connections_readonly.py")
tool=importlib.util.module_from_spec(spec)
spec.loader.exec_module(tool)


def fake_runner(overrides=None):
    calls=[]
    def run(cmd, **kwargs):
        calls.append(tuple(cmd))
        op=tuple(cmd[1:-2])
        if op[:2]==("account","show"):
            payload={"id":"trusted-subscription"}
        elif op[:2]==("group","show"):
            payload={"name":tool.RG,"location":"centralindia",
                     "tags":{"app":"RetailGrowthAI","environment":"dev"}}
        else:
            app=op[-1]
            if op[:2]==("functionapp","show"):
                payload={"name":app,"state":"Running",
                         "id":"/subscriptions/trusted-subscription/resourceGroups/"
                               +tool.RG+"/providers/Microsoft.Web/sites/"+app}
            elif op[:3]==("functionapp","config","appsettings"):
                payload=[{"name":key,
                          "value":("python" if key=="FUNCTIONS_WORKER_RUNTIME"
                                   else tool.EXPECTED_SUPABASE if key=="RETAIL_SUPABASE_URL"
                                   else "synthetic-unsafe-secret-never-log")}
                         for key in sorted(tool.CONNECTIONS)]
            elif op[:3]==("functionapp","function","list"):
                names=tool.CORE_FUNCTIONS if app==tool.Y1 else {"plan_campaign"}
                payload=[{"name":app+"/"+name} for name in sorted(names)]
            else:
                raise AssertionError("Unexpected Azure command")
        if overrides:
            payload=overrides(op,payload)
        return SimpleNamespace(returncode=0,stdout=json.dumps(payload),stderr="")
    return run,calls


class ReadonlyY1ConnectionInspection(unittest.TestCase):
    def setUp(self):
        self.env=patch.dict(os.environ,{"GITHUB_ACTIONS":"true",
                  "GITHUB_REPOSITORY":"saifsiddiqui59/RetailGrowthAI",
                  "GITHUB_REF":"refs/heads/main",
                  "AZURE_SUBSCRIPTION_ID":"trusted-subscription"})
        self.env.start()
        self.addCleanup(self.env.stop)

    def test_correct_development_connections_never_leave_process(self):
        run,calls=fake_runner()
        report=tool.inspect(run)
        self.assertTrue(report["y1_same_core_connection_values"])
        self.assertTrue(report["y1_core_http_complete"])
        self.assertTrue(report["y1_running"])
        self.assertFalse(report["y1_any_background_triggers"])
        self.assertEqual(report["y1_indexed_count"],len(tool.CORE_FUNCTIONS))
        self.assertEqual(len(calls),8)
        self.assertTrue(all(x[0]=="az" and x[-2:]==("--output","json")
                            for x in calls))
        self.assertFalse(any(x in {"stop","delete","set"}
                             for cmd in calls for x in cmd))

    def test_separate_y1_webjobs_host_storage_does_not_false_block_shared_queue(self):
        def changed(op,payload):
            if op[:3]==("functionapp","config","appsettings") and op[-1]==tool.Y1:
                for item in payload:
                    if item["name"]=="AzureWebJobsStorage":
                        item["value"]="dedicated-y1-internal-host-storage"
            return payload
        report=tool.inspect(fake_runner(changed)[0])
        self.assertTrue(report["y1_same_core_connection_values"])

    def test_changed_service_role_key_prevents_false_connection_parity(self):
        def changed(op, payload):
            if op[:3]==("functionapp","config","appsettings") and op[-1]==tool.Y1:
                for item in payload:
                    if item["name"]=="RETAIL_SUPABASE_SERVICE_ROLE_KEY":
                        item["value"]="not-matching"
            return payload
        run,_=fake_runner(changed)
        self.assertFalse(tool.inspect(run)["y1_same_core_connection_values"])

    def test_wrong_azure_subscription_or_group_is_denied(self):
        def foreign_sub(op,p):
            if op[:2]==("account","show"): p["id"]="foreign-subscription"
            return p
        with self.assertRaisesRegex(RuntimeError,"FOREIGN_AZURE_SUBSCRIPTION"):
            tool.inspect(fake_runner(foreign_sub)[0])
        def foreign_tags(op,p):
            if op[:2]==("group","show"): p["tags"]["app"]="WineShopPOS"
            return p
        with self.assertRaisesRegex(RuntimeError,"FOREIGN_AZURE_RESOURCE_GROUP"):
            tool.inspect(fake_runner(foreign_tags)[0])

    def test_missing_main_and_repo_prevents_any_azure_call(self):
        with patch.dict(os.environ,{"GITHUB_REF":"refs/heads/feature"},
                        clear=False):
            run,calls=fake_runner()
            with self.assertRaisesRegex(RuntimeError,"PROTECTED"):
                tool.inspect(run)
            self.assertEqual(calls,[])

    def test_unapproved_azure_cli_commands_and_duplicate_settings_rejected(self):
        for args in (("functionapp","stop","-g",tool.RG,"-n",tool.FLEX),
                     ("functionapp","config","appsettings","set",
                       "-g",tool.RG,"-n",tool.Y1),
                     ("group","delete","-g",tool.RG)):
            with self.subTest(args=args),self.assertRaises(ValueError):
                tool.read_azure(*args,runner=fake_runner()[0])
        with self.assertRaises(RuntimeError):
            tool.safe_setting_map([{"name":"X","value":"1"},
                                   {"name":"X","value":"2"}])
        with self.assertRaises(RuntimeError):
            tool.function_names([{"name":"other-app/create_campaign"}],tool.Y1)

    def test_failed_azure_calls_never_expose_stderr_or_appsetting_values(self):
        def fail(*_,**__):
            return SimpleNamespace(returncode=1,stdout="sensitive",
                                   stderr="secret=NEVER_PRINT")
        with self.assertRaisesRegex(RuntimeError,"AZURE_READ_ONLY_INVENTORY_FAILED") as err:
            tool.read_azure("account","show",runner=fail)
        self.assertNotIn("NEVER_PRINT",str(err.exception))
        self.assertNotIn("sensitive",str(err.exception))


if __name__=="__main__":
    unittest.main()
