"""Source-only fail-closed original Flex deployment backup inventory."""
from copy import deepcopy
from pathlib import Path
import importlib.util
import unittest

ROOT=Path(__file__).resolve().parents[2]
SRC=ROOT/'scripts/deploy/feature4_original_package_inventory.py'
WF=ROOT/'.github/workflows/retail-dev-feature4-original-restore-inventory-once.yml'
spec=importlib.util.spec_from_file_location('f4_inventory',SRC)
m=importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)

SUB='11111111-2222-3333-4444-555555555555'

def fixture():
    original={
      'id':f'/subscriptions/{SUB}/resourceGroups/{m.DEV_RG}/providers/Microsoft.Web/sites/{m.DEV_SITE}',
      'name':m.DEV_SITE,
      'tags':{'app':'retailgrowthai','environment':'dev'},
      'properties':{'functionAppConfig':{'deployment':{
          'storage':{'type':'blobContainer',
                     'value':'https://'+m.STORAGE+'.blob.core.windows.net/private-container'}}}},
    }
    settings=[
        {'name':'RETAIL_SUPABASE_URL','value':'https://jeearzffnjbvghwjjjrf.supabase.co'},
        {'name':'AzureWebJobsStorage','value':'private-host-connection'},
        {'name':'RETAIL_STORAGE','value':'private-queue-connection'},
    ]
    functions=[{'name':m.DEV_SITE+'/'+n} for n in sorted(m.REQUIRED_LEGACY)]
    return original,settings,functions

class OriginalPackageInventory(unittest.TestCase):
    def test_readonly_flex_package_mode_cannot_be_called_rollback(self):
        app,settings,functions=fixture()
        got=m.classify(app,settings,functions,SUB)
        self.assertEqual(got['baseline_storage_mode'],
                         'flex-blob-container-no-pinned-active-package')
        self.assertEqual(got['feature4_index_missing_count'],7)
        self.assertFalse(got['exact_active_package_backed_up'])
        self.assertFalse(got['mutation_permitted'])

    def test_hosted_f4_index_does_not_equal_backed_up_package(self):
        app,settings,functions=fixture()
        functions.extend({'name':m.DEV_SITE+'/'+n} for n in sorted(m.REQUIRED_F4))
        got=m.classify(app,settings,functions,SUB)
        self.assertEqual(got['feature4_index_missing_count'],0)
        self.assertFalse(got['exact_active_package_backed_up'])

    def test_declared_private_package_uri_still_not_proof_of_restore(self):
        app,settings,functions=fixture()
        settings.append({'name':'WEBSITE_RUN_FROM_PACKAGE',
                         'value':'https://'+m.STORAGE+'.blob.core.windows.net/active/current.zip?sv=redacted'})
        got=m.classify(app,settings,functions,SUB)
        self.assertEqual(got['baseline_storage_mode'],'private-blob-uri')
        self.assertFalse(got['mutation_permitted'])
        settings[-1]['value']='https://foreign.example/active/current.zip'
        self.assertEqual(m.classify(app,settings,functions,SUB)['baseline_storage_mode'],
                         'unverified')

    def test_foreign_or_unverified_original_denied_before_any_release(self):
        mutations=[
            lambda a,s,f: a.update(id='foreign'),
            lambda a,s,f: a['tags'].update(environment='prod'),
            lambda a,s,f: s[0].update(value='https://foreign.example'),
            lambda a,s,f: s.append({'name':'RETAIL_FEATURE4_CPU_RENDER_ENABLED','value':'true'}),
            lambda a,s,f: s.pop(1),
            lambda a,s,f: f.pop(0),
            lambda a,s,f: s.append(deepcopy(s[0])),
        ]
        for mutate in mutations:
            with self.subTest(change=str(mutate)):
                a,s,f=fixture()
                mutate(a,s,f)
                with self.assertRaises(m.Denied):
                    m.classify(a,s,f,SUB)

    def test_no_write_capabilities_in_protected_readonly_workflow(self):
        text=WF.read_text()
        self.assertIn('environment: dev',text)
        self.assertIn('id-token: write',text)
        self.assertIn('feature4_original_package_inventory.py',text)
        self.assertIn("az functionapp function list -g",text)
        self.assertIn("az functionapp config appsettings list -g",text)
        self.assertNotIn('az functionapp config appsettings set',text)
        self.assertNotIn('az functionapp deployment source config-zip',text)
        self.assertNotIn('az storage blob delete',text)
        self.assertNotIn('az role assignment create',text)
        self.assertNotIn('WEBSITE_RUN_FROM_PACKAGE=',text)

if __name__=='__main__':
    unittest.main()
