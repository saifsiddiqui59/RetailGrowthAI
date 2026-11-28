"""Offline verifier must reject stale or mixed deployed builds."""
import sys
import tempfile
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts" / "deploy"))
import verify_mobile_approval_swa as m

class MobileReleaseVerification(unittest.TestCase):
    def fixture(self):
        return {
            **{r: b'<div id="root"></div><script src="/assets/index-abc.js"></script><link href="/assets/index-def.css">' for r in m.ROUTES},
            "/assets/index-abc.js": (m.FLEX + ' "./PlatformAdmin-ghi.js"').encode(),
            "/assets/PlatformAdmin-ghi.js": m.HINT,
            "/assets/index-def.css": m.CSS_MARKER + b"{grid-template-columns:minmax(0,1fr)}",
        }

    def test_exact_build_and_live_origin(self):
        data = self.fixture()
        self.assertEqual(m.verify(data.__getitem__), 3)
        with tempfile.TemporaryDirectory() as d:
            for path, body in data.items():
                if path.startswith("/assets/"):
                    f = Path(d) / path.lstrip("/")
                    f.parent.mkdir(exist_ok=True)
                    f.write_bytes(body)
            self.assertEqual(m.verify(data.__getitem__, d), 3)
            data["/assets/PlatformAdmin-ghi.js"] = b"old approval"
            with self.assertRaisesRegex(RuntimeError, "DEPLOYED_ASSET_BYTES_DIFFER"):
                m.verify(data.__getitem__, d)

    def test_mixed_or_wrong_origin_denied(self):
        data = self.fixture()
        data["/assets/PlatformAdmin-ghi.js"] += b" https://rgai-dev-y1-p0249-d4e5ddbd.azurewebsites.net"
        with self.assertRaisesRegex(RuntimeError, "LIVE_API_ORIGIN"):
            m.verify(data.__getitem__)

    def test_missing_root_denied(self):
        data = self.fixture()
        data["/account"] = b"<html>old</html>"
        with self.assertRaisesRegex(RuntimeError, "SPA_ENTRY_MISSING"):
            m.verify(data.__getitem__)
