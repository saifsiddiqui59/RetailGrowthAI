"""Offline safety checks for versioned external private Y1 package rollout."""
from pathlib import Path
import tempfile
import os
import sys
import unittest
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/"ops"))
import p0249_y1_external_private_package as x
import p0249_y1_remote_build_mode as mode


class FakeY1:
    def __init__(self):
        self.old="https://"+x.EXPECTED_URI_HOST+"/private/y1-two.zip?sig=TOPSECRET"
        self.settings={"WEBSITE_RUN_FROM_PACKAGE":self.old,
                       x.BACKUP:self.old,
                       x.OLD_OWNER:x.EXPECTED_FAILED_OWNER,
                       "SCM_DO_BUILD_DURING_DEPLOYMENT":"true"}
        self.names=mode.TWO
        self.writes=[]
        self.blob_size=4_000

    def az(self,*argv):
        prefix=tuple(argv[:3])
        if prefix==("storage","container","exists"):
            return {"exists":True}
        if prefix==("storage","blob","generate-sas"):
            return "sv=2026-11-02&sp=r&sig=REDACTEDTEST"
        if prefix==("storage","blob","upload"):
            self.writes.append("new-private-blob-upload")
            return {"etag":"opaque"}
        if prefix==("storage","blob","show"):
            return {"properties":{"contentLength":self.blob_size}}
        if prefix==("resource","invoke-action","-g"):
            self.writes.append("sync-only")
            return None
        raise AssertionError("unreviewed Azure path")

    def read(self):
        return dict(self.settings),frozenset(self.names)

    def set(self,**changes):
        self.writes.append(tuple(changes.keys()))
        self.settings.update(changes)
        if x.PACKAGE_KEY in changes:
            self.names=mode.FIVE if changes[x.PACKAGE_KEY]!=self.old else mode.TWO


class ExternalPrivatePackageTests(unittest.TestCase):
    def setUp(self):
        self.fake=FakeY1()
        patches=[patch.object(x,"_read_site",side_effect=self.fake.read),
                 patch.object(x,"azure",side_effect=lambda *args:self.fake.az(*args)),
                 patch.object(mode,"_settings",side_effect=lambda:dict(self.fake.settings)),
                 patch.object(mode,"_set",side_effect=self.fake.set),
                 patch.object(x.guard,"probe",return_value=None),
                 patch.object(x,"_wait_for",side_effect=lambda expected,**kwargs: frozenset(self.fake.names)==expected),
                 patch.dict(os.environ,{"GITHUB_RUN_ID":"44670001234"})]
        for p in patches:
            p.start();self.addCleanup(p.stop)

    def test_original_package_owner_and_exact_shape_required(self):
        old,container=x.scoped_baseline(*self.fake.read())
        self.assertEqual(old,self.fake.old)
        self.assertEqual(container,"private")
        for variant in ("wrong-owner","wrong-account","wrong-routes","unexpected-setting"):
            with self.subTest(variant=variant):
                f=FakeY1()
                if variant=="wrong-owner":f.settings[x.OLD_OWNER]="other"
                if variant=="wrong-account":
                    f.old="https://other.blob.core.windows.net/private/package.zip?secret"
                    f.settings[x.BACKUP]=f.old
                    f.settings[x.PACKAGE_KEY]=f.old
                if variant=="wrong-routes":f.names=frozenset((*mode.TWO,"queueTrigger"))
                if variant=="unexpected-setting":f.settings["RETAIL_SUPABASE_URL"]="SECRET"
                with self.assertRaises(RuntimeError):
                    x.scoped_baseline(*f.read())

    def test_preflight_fails_before_mutation_without_private_container_rights(self):
        with tempfile.TemporaryDirectory() as d:
            zipfile=Path(d)/"new.zip";zipfile.write_bytes(b"x"*4000)
            self.fake.az=lambda *argv: {"exists":False} if argv[:3]==("storage","container","exists") else None
            with self.assertRaisesRegex(RuntimeError,"private container"):
                x.preflight(zipfile)
            self.assertEqual(self.fake.writes,[])

    def test_publish_sets_new_owner_before_new_uri_and_sync_without_log_secrets(self):
        with tempfile.TemporaryDirectory() as d:
            z=Path(d)/"new.zip";z.write_bytes(b"x"*4000)
            self.fake.blob_size=4000
            x.publish(z)
            self.assertEqual(self.fake.writes[:3],["new-private-blob-upload",(x.NEW_OWNER,),(x.PACKAGE_KEY,)])
            self.assertEqual(self.fake.writes[-1],"sync-only")
            self.assertEqual(self.fake.settings[x.BACKUP],self.fake.old)
            self.assertNotEqual(self.fake.settings[x.PACKAGE_KEY],self.fake.old)
            self.assertTrue(self.fake.settings[x.PACKAGE_KEY].startswith("https://"+x.EXPECTED_URI_HOST+"/private/"))
            self.assertEqual(frozenset(self.fake.names),mode.FIVE)

    def test_rollback_restores_exact_original_even_if_new_owner_and_five_indexes(self):
        self.fake.settings[x.NEW_OWNER]="44670001234"
        self.fake.settings[x.PACKAGE_KEY]="https://"+x.EXPECTED_URI_HOST+"/private/new.zip?sig=NEW"
        self.fake.names=mode.FIVE
        x.rollback()
        self.assertEqual(self.fake.settings[x.PACKAGE_KEY],self.fake.old)
        self.assertEqual(frozenset(self.fake.names),mode.TWO)
        self.assertEqual(self.fake.settings[x.BACKUP],self.fake.old)

    def test_refuse_mismatched_new_owner_and_foreign_source_on_recovery(self):
        self.fake.settings[x.NEW_OWNER]="different"
        with self.assertRaisesRegex(RuntimeError,"Unowned"):
            x.rollback()
        self.assertEqual(self.fake.writes,[])
        self.fake.settings[x.NEW_OWNER]="44670001234"
        self.fake.names=frozenset((*mode.TWO,"secret_queue_trigger"))
        with self.assertRaisesRegex(RuntimeError,"Unknown"):
            x.rollback()
        self.assertEqual(self.fake.writes,[])

    def test_rollback_allows_owner_proven_zero_indexes_and_changed_build_flag(self):
        self.fake.settings[x.NEW_OWNER]="44670001234"
        self.fake.settings[x.PACKAGE_KEY]="https://"+x.EXPECTED_URI_HOST+"/private/other.zip?sig=SECRET"
        self.fake.settings["SCM_DO_BUILD_DURING_DEPLOYMENT"]="false"
        self.fake.names=frozenset()
        x.rollback()
        self.assertEqual(self.fake.settings[x.PACKAGE_KEY],self.fake.old)
        self.assertEqual(frozenset(self.fake.names),mode.TWO)

    def test_rollback_rejects_other_package_when_no_new_owner(self):
        self.fake.settings[x.PACKAGE_KEY]="https://"+x.EXPECTED_URI_HOST+"/private/unowned.zip"
        with self.assertRaisesRegex(RuntimeError,"Unowned"):
            x.rollback()
        self.assertEqual(self.fake.writes,[])

    def test_verify_requires_five_owned_originals_and_new_url(self):
        with self.assertRaisesRegex(RuntimeError,"five-function"):
            x.verify()
        self.fake.settings[x.NEW_OWNER]="44670001234"
        self.fake.settings[x.PACKAGE_KEY]="https://"+x.EXPECTED_URI_HOST+"/private/new.zip?sig=NEW"
        self.fake.names=mode.FIVE
        x.verify()

    def test_released_code_does_not_print_url_or_storage_account_keys(self):
        src=(ROOT/"ops/p0249_y1_external_private_package.py").read_text()
        for invalid in ('print(uri)','print(old)','print(sas)','keys list','--account-key','--overwrite", "true'):
            self.assertNotIn(invalid,src)
        self.assertIn('"--as-user"',src)
        self.assertIn('"--auth-mode", "login"',src)
        self.assertIn('raise RuntimeError("Y1 scoped Azure operation failed (redacted)")',src)

if __name__=="__main__":
    unittest.main()
