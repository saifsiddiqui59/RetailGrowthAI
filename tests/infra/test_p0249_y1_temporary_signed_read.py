"""#249: offline safety regression for isolated DEV Y1 one-user signed JWT trial."""
import json
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch
from uuid import uuid4

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "ops"))
import p0249_y1_public_shadow_guard as guard
import p0249_y1_signed_disposable_read as signed

WORKFLOW = ROOT / ".github/workflows/p0249-dev-y1-temporary-signed-read-once.yml"
ENV = {"GITHUB_RUN_ID":"9102","GITHUB_RUN_ATTEMPT":"1"}


class P0249Y1TemporarySignedReadTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.marker=str(Path(self.temp.name)/"absent.json")
        p=patch.dict(os.environ,ENV)
        p.start()
        self.addCleanup(p.stop)

    def snapshot(self):
        Path(self.marker).write_text(json.dumps({
            "schema":guard.MARKER_SCHEMA,
            "run_id":"9102",
            "run_attempt":"1",
            "initial_absent":list(guard.KEYS),
        }))

    def test_exact_public_values_and_no_privileged_function_setting(self):
        self.assertEqual(set(guard.SETTING_VALUES), {
            "RETAIL_SUPABASE_URL", "RETAIL_SUPABASE_PUBLISHABLE_KEY",
            "RGAI_P0249_READONLY_SHADOW"})
        self.assertEqual(guard.SETTING_VALUES["RGAI_P0249_READONLY_SHADOW"],"true")
        self.assertEqual(guard.SETTING_VALUES["RETAIL_SUPABASE_URL"],signed.SUPABASE)
        self.assertEqual(guard.SETTING_VALUES["RETAIL_SUPABASE_PUBLISHABLE_KEY"],signed.PUBLIC)
        self.assertNotIn("RETAIL_SUPABASE_SERVICE_ROLE_KEY",guard.SETTING_VALUES)

    def test_preflight_creates_run_bound_marker_only_when_all_three_absent(self):
        with patch.object(guard,"read_only_scope",return_value={}), \
             patch.object(guard.scope,"command",side_effect=AssertionError("no Azure writes")):
            guard.preflight(self.marker)
        self.assertEqual(guard.require_marker(self.marker)["initial_absent"],list(guard.KEYS))

    def test_preflight_aborts_on_existing_key_without_changes(self):
        with patch.object(guard,"read_only_scope",return_value={
            "RGAI_P0249_READONLY_SHADOW":"false"}), \
             patch.object(guard.scope,"command",side_effect=AssertionError("no Azure writes")), \
             self.assertRaises(RuntimeError):
            guard.preflight(self.marker)
        self.assertFalse(Path(self.marker).exists())

    def test_wrong_marker_prevents_all_mutations(self):
        Path(self.marker).write_text('{"run_id":"wrong"}')
        with patch.object(guard.scope,"command",side_effect=AssertionError("no Azure writes")), \
             self.assertRaises(RuntimeError):
            guard.activate(self.marker)
        with patch.object(guard.scope,"command",side_effect=AssertionError("no Azure writes")), \
             self.assertRaises(RuntimeError):
            guard.rollback(self.marker)

    def test_activation_only_sets_three_public_keys_after_recheck(self):
        self.snapshot()
        with patch.object(guard,"read_only_scope",side_effect=[{},guard.SETTING_VALUES]), \
             patch.object(guard.scope,"command",return_value=[]) as azure:
            guard.activate(self.marker)
        self.assertEqual(azure.call_count,1)
        args=azure.call_args.args
        self.assertEqual(args[:4],("functionapp","config","appsettings","set"))
        self.assertEqual(args[args.index("-n")+1],guard.scope.SITE)
        settings=args[args.index("--settings")+1:]
        self.assertEqual(set(settings),{k+"="+v for k,v in guard.SETTING_VALUES.items()})
        self.assertFalse(any("service_role" in x.lower() for x in settings))

    def test_cleanup_removes_only_all_three_initially_absent_public_keys(self):
        self.snapshot()
        with patch.object(guard,"read_only_scope",side_effect=[guard.SETTING_VALUES,{}]), \
             patch.object(guard.scope,"command",return_value=[]) as azure:
            guard.rollback(self.marker)
        self.assertEqual(azure.call_count,1)
        args=azure.call_args.args
        self.assertEqual(args[:4],("functionapp","config","appsettings","delete"))
        self.assertEqual(set(args[args.index("--setting-names")+1:]),set(guard.KEYS))

    def test_external_change_aborts_cleanup_instead_of_clobbering(self):
        self.snapshot()
        with patch.object(guard,"read_only_scope",return_value={
            "RGAI_P0249_READONLY_SHADOW":"external-change"}), \
             patch.object(guard.scope,"command",side_effect=AssertionError("never clobber")), \
             self.assertRaises(RuntimeError):
            guard.rollback(self.marker)

    def test_uncertain_auth_create_cleanup_is_exact_synthetic_only(self):
        marker=signed.PREFIX+uuid4().hex[:16]
        uid=str(uuid4())
        with patch.object(signed,"request",side_effect=[
            (200,{"users":[{"id":uid,"email":marker+"@example.invalid"},
                           {"id":str(uuid4()),"email":"owner@example.com"}]}, {},0.1),
            (204,None,{},0.1),
        ]) as request:
            signed.cleanup_exact_test_user("dummy-key",marker,None)
        self.assertEqual(request.call_count,2)
        self.assertEqual(request.call_args.args[0],signed.SUPABASE+"/auth/v1/admin/users/"+uid)
        self.assertEqual(request.call_args.kwargs["method"],"DELETE")

    def test_no_untrusted_test_user_can_be_deleted(self):
        with patch.object(signed,"request",side_effect=AssertionError("do not contact Auth")), \
             self.assertRaises(RuntimeError):
            signed.cleanup_exact_test_user("key","real-owner",str(uuid4()))

    def test_workflow_uses_three_jobs_independent_cleanup_and_no_other_resources(self):
        w=WORKFLOW.read_text()
        for token in (
            "environment: dev", "id-token: write", "refs/heads/main",
            "YES-DEV-Y1-TEMP-SIGNED-READ", "independent-rollback:",
            "actions/upload-artifact@v4", "actions/download-artifact@v4",
            "p0249_y1_public_shadow_guard.py preflight",
            "p0249_y1_public_shadow_guard.py activate",
            "p0249_y1_public_shadow_guard.py rollback",
            "RGAI_DEV_SERVICE_KEY:", "p0249_y1_signed_disposable_read.py",
        ):
            with self.subTest(required=token):
                self.assertIn(token,w)
        for forbidden in (
            "az deployment group create","az functionapp create",
            "az resource delete","az storage queue","az functionapp deployment source",
            "az functionapp scale config always-ready set",
            "-n rgai-dev-functions-d4e5ddbd",
        ):
            with self.subTest(forbidden=forbidden):
                self.assertNotIn(forbidden,w)
        self.assertNotIn("RGAI_DEV_SERVICE_KEY: __GH__", w)

    def test_auth_script_only_creates_and_deletes_synthetic_user_not_shops(self):
        s=(ROOT/"ops/p0249_y1_signed_disposable_read.py").read_text()
        self.assertIn('email = marker + "@example.invalid"',s)
        self.assertIn("email_confirm",s)
        self.assertIn("finally:",s)
        self.assertIn("cleanup_exact_test_user(key, marker, uid)",s)
        self.assertNotIn("/rest/v1/",s)
        self.assertNotIn("/storage/v1/",s)
        self.assertNotIn("DELETE FROM",s)
        self.assertNotIn("auth.users",s.replace("auth.users SQL",""))
        self.assertNotIn("log(token)",s)


if __name__=="__main__":
    unittest.main()
