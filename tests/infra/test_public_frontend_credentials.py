"""Public credential gate rejects secrets, not exact token-rejection guards."""
import base64
import json
import sys
import tempfile
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts" / "deploy"))
import scan_public_frontend_credentials as m

class PublicCredentialScan(unittest.TestCase):
    def test_known_rejection_checks(self):
        for data in (b'token.startsWith("sb_secret_")', b"t.startsWith('sb_secret_')", b't.startsWith( "sb_secret_" )'):
            m.check_bytes(data, javascript=True)

    def test_other_contexts_and_actual_secret_shapes_denied(self):
        for data in (b'const key="sb_secret_example_test_value";', b't.startsWith("sb_secret_example_test_value")', b'const prefix="sb_secret_"', b'RETAIL_SUPABASE_SERVICE_ROLE_KEY', b'RETAIL_FOUNDRY_API_KEY', b't.startsWith("sb_secret_");let leak="sb_secret_example"'):
            with self.assertRaises(ValueError):
                m.check_bytes(data, javascript=True)
        with self.assertRaises(ValueError):
            m.check_bytes(b't.startsWith("sb_secret_")', javascript=False)

    def test_legacy_role_jwt_denied(self):
        def enc(obj):
            return base64.urlsafe_b64encode(json.dumps(obj).encode()).rstrip(b"=")
        header = enc({"alg":"HS256"})
        sig = b"not_a_real_signature"
        with self.assertRaisesRegex(ValueError, "SERVICE_ROLE_JWT"):
            m.check_bytes(b".".join((header,enc({"role":"service_role"}),sig)), javascript=True)
        m.check_bytes(b".".join((header,enc({"role":"anon"}),sig)), javascript=True)

    def test_dist_scan(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d)
            (root/"index.html").write_text("<html></html>")
            (root/"index.js").write_text('t.startsWith("sb_secret_")')
            self.assertEqual(m.scan(root),2)
            (root/"leak.txt").write_text("sb_secret_example_test_value")
            with self.assertRaises(ValueError):
                m.scan(root)
