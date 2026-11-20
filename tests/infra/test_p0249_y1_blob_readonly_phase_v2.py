"""Secret-proof fixed category classification for Y1 Blob incident diagnosis."""
from pathlib import Path
import sys,unittest
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/"ops"))
import p0249_y1_blob_readonly_phase_v2 as probe

class BlobPhaseTests(unittest.TestCase):
    def test_only_fixed_nonsecret_error_classes(self):
        data={
            "AuthorizationPermissionMismatch signed https://store.invalid/?sig=SECRET":"ACCESS_DENIED",
            "This az command returned BlobNotFound sig=NEVER":"NOT_FOUND",
            "error: unrecognized arguments --flag?key=TOPSECRET":"CLI_COMMAND",
            "InvalidResourceName https://secret/?sig=PIN":"INVALID_BLOB_NAME",
            "Azure failed sig=IMPORTANT":"OTHER_REDACTED",
        }
        for raw,expected in data.items():
            observed=probe.error_class(raw)
            self.assertEqual(observed,expected)
            for secret in ("SECRET","NEVER","TOPSECRET","PIN","IMPORTANT","https"):
                self.assertNotIn(secret,observed)

    def test_baseline_mismatch_stops_even_after_sanitized_health_probe(self):
        from unittest.mock import patch
        from contextlib import redirect_stdout
        from io import StringIO
        import p0249_y1_remote_build_mode as mode
        output=StringIO()
        with patch.object(probe.guard, 'verify', return_value=None), \
             patch.object(probe.mode, '_settings', return_value={}), \
             patch.object(probe.mode, '_index', return_value=mode.TWO), \
             patch.object(probe.pkg, 'scoped_baseline', side_effect=RuntimeError('SECRET URI')), \
             patch.object(probe.guard, 'probe', return_value=None) as health, \
             patch.object(probe, 'read_blob') as read, redirect_stdout(output):
            with self.assertRaisesRegex(RuntimeError, 'Original Y1 baseline mismatch'):
                probe.main()
        health.assert_called_once()
        read.assert_not_called()
        self.assertIn('ORIGINAL_BASELINE_NOT_MATCHED', output.getvalue())
        self.assertNotIn('SECRET', output.getvalue())

    def test_script_and_one_shot_only_read_existing_blob(self):
        s=(ROOT/"ops/p0249_y1_blob_readonly_phase_v2.py").read_text()
        wf=(ROOT/".github/workflows/p0249-y1-failed-blob-phase-readonly-once.yml").read_text()
        for bad in ("blob upload","appsettings set","appsettings delete",
                    "config-zip","az rest --method post","account keys list"):
            self.assertNotIn(bad,s)
            self.assertNotIn(bad,wf)
        self.assertIn("subprocess.run",s)
        self.assertIn("P0249_Y1_BLOB_EXISTS_RESULT=",s)
        self.assertIn("guard.probe()",s)
        self.assertIn("environment: dev",wf)
        self.assertIn("id-token: write",wf)
        self.assertIn("github.event_name == 'push'",wf)

if __name__=="__main__":
    unittest.main()
