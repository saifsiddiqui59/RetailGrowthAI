"""Offline tests: fail closed for contract, authorization, licensing, path traversal."""
import copy
import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "video-engine"))
from render import RenderError, load_job, escape_filter_path  # noqa: E402


class ValidationTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.campaign = json.loads((ROOT / "frontend/src/features/campaigns/fixtures/sample-campaign.json")
                                   .read_text(encoding="utf-8"))
        self.assets = {}
        for segment in self.campaign["days"][0]["instagram"]["reel"]["storyboard"]:
            aid = segment["asset_id"]
            (self.root / (aid + ".jpg")).write_bytes(b"fake source for static validation")
            self.assets[aid] = {
                "kind": "image", "path": aid + ".jpg",
                "rights": {"license": "owned", "commercial_use": True,
                           "source": "tenant uploaded", "evidence": "owner attestation 123"},
            }
        self.manifest = {"shop_id": self.campaign["shop_id"], "assets": self.assets}

    def load(self):
        cp = self.root / "campaign.json"
        mp = self.root / "manifest.json"
        cp.write_text(json.dumps(self.campaign))
        mp.write_text(json.dumps(self.manifest))
        return load_job(cp, mp, self.root, 1)

    def test_valid_canonical_v1_storyboard(self):
        segments, paths, audio, cta = self.load()
        self.assertEqual(len(segments), 3)
        self.assertEqual(len(paths), 3)
        self.assertIsNone(audio)
        self.assertEqual(cta, "Visit our store")

    def test_wrong_tenant_rejected(self):
        self.manifest["shop_id"] = "another-shop"
        with self.assertRaisesRegex(RenderError, "Cross-tenant"):
            self.load()

    def test_wrong_campaign_id_rejected(self):
        self.campaign["days"][0]["campaign_id"] = "another-campaign"
        with self.assertRaisesRegex(RenderError, "ownership"):
            self.load()

    def test_gap_rejected(self):
        self.campaign["days"][0]["instagram"]["reel"]["storyboard"][1]["start_seconds"] = 11
        with self.assertRaisesRegex(RenderError, "contiguous"):
            self.load()

    def test_wrong_total_rejected(self):
        self.campaign["days"][0]["instagram"]["reel"]["storyboard"][-1]["duration_seconds"] = 9
        with self.assertRaisesRegex(RenderError, "exactly 30"):
            self.load()

    def test_missing_rights_rejected(self):
        key = next(iter(self.assets))
        self.assets[key].pop("rights")
        with self.assertRaisesRegex(RenderError, "commercial-use"):
            self.load()

    def test_noncommercial_asset_rejected(self):
        key = next(iter(self.assets))
        self.assets[key]["rights"]["commercial_use"] = False
        with self.assertRaisesRegex(RenderError, "commercial-use"):
            self.load()

    def test_synthetic_rights_rejected_without_explicit_ci_flag(self):
        key = next(iter(self.assets))
        self.assets[key]["rights"]["license"] = "synthetic_test"
        with self.assertRaisesRegex(RenderError, "unsupported"):
            self.load()

    def test_unknown_asset_rejected(self):
        self.campaign["days"][0]["instagram"]["reel"]["storyboard"][0]["asset_id"] = "unknown"
        with self.assertRaisesRegex(RenderError, "Unknown"):
            self.load()

    def test_path_traversal_rejected(self):
        key = next(iter(self.assets))
        outside = self.root.parent / "outside-image.jpg"
        self.assets[key]["path"] = "../outside-image.jpg"
        with self.assertRaises((RenderError, FileNotFoundError)):
            self.load()

    def test_no_url_input(self):
        key = next(iter(self.assets))
        self.assets[key]["path"] = "https://example.org/image.jpg"
        with self.assertRaisesRegex(RenderError, "server-staged"):
            self.load()

    def test_missing_audio_license_rejected(self):
        self.campaign["days"][0]["instagram"]["reel"]["music_asset_id"] = "music1"
        (self.root / "music.wav").write_bytes(b"not decoded in validation")
        self.assets["music1"] = {"kind": "audio", "path": "music.wav"}
        with self.assertRaisesRegex(RenderError, "commercial-use"):
            self.load()

    def test_filter_path_escapes_delimiters(self):
        self.assertEqual(escape_filter_path("a:b,c"), "a\\:b\\,c")

    def test_invalid_overlay_control_character_rejected(self):
        self.campaign["days"][0]["instagram"]["reel"]["storyboard"][0]["overlay_text"] = "hello\rbad"
        with self.assertRaisesRegex(RenderError, "control"):
            self.load()


if __name__ == "__main__":
    unittest.main()
