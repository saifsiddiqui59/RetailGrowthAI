"""Read-only failed-versioned-Blob diagnosis parser and scope gates."""
from pathlib import Path
import sys,unittest
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/"ops"))
import p0249_y1_failed_private_blob_probe as probe


class Y1FailedBlobProbeTests(unittest.TestCase):
    def test_only_nonsecret_boolean_shape_is_exposed(self):
        good=probe.safe_blob_shape({"properties":{"contentLength":6500000,
                       "url":"https://secret/?sig=SECRET",
                       "metadata":{"key":"NEVER"}}},exists=True)
        self.assertEqual(good,{"exists":True,"size_reported":True,"size_in_zip_bounds":True})
        self.assertNotIn("SECRET",str(good))
        self.assertNotIn("NEVER",str(good))
        self.assertFalse(probe.safe_blob_shape({},exists=False)["exists"])
        self.assertFalse(probe.safe_blob_shape({"properties":{}},exists=True)["size_reported"])
        with self.assertRaises(RuntimeError):
            probe.safe_blob_shape(None,exists=True)

    def test_readonly_probe_never_writes_and_pins_original_scope(self):
        source=(ROOT/"ops/p0249_y1_failed_private_blob_probe.py").read_text()
        wf=(ROOT/".github/workflows/p0249-y1-failed-private-blob-readonly-once.yml").read_text()
        self.assertIn("44670935079",source)
        self.assertIn("pkg.scoped_baseline(settings,indexed)",source)
        self.assertIn("guard.verify()",source)
        self.assertIn("guard.probe()",source)
        for forbidden in ("appsettings set","appsettings delete","blob upload",
                          "config-zip","resource invoke-action","az rest"):
            self.assertNotIn(forbidden,source)
            self.assertNotIn(forbidden,wf)
        self.assertIn("environment: dev",wf)
        self.assertIn("id-token: write",wf)
        self.assertIn("github.event_name == 'push'",wf)
        self.assertNotIn("password",wf)

if __name__=="__main__":
    unittest.main()
