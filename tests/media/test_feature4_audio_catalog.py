"""Fail-closed audio catalog regression tests; no commercial tracks distributed."""
import copy
import datetime as dt
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "video-engine"))
from audio_catalog import authorized_track, AudioCatalogError  # noqa E402

NOW = dt.datetime(2026, 10, 26, tzinfo=dt.timezone.utc)
BASE = {
    "id": "original_test_tone", "asset_id": "asset_approved_1",
    "title": "Operator-owned test track", "source": "https://example.invalid/original-audio",
    "creator": "RetailGrowthAI fixture author", "license_url": "https://example.invalid/license",
    "license_evidence_id": "internal-review-document-00001",
    "reviewed_by": "Internal legal curator", "reviewed_at": "2026-10-20T00:00:00Z",
    "status": "approved", "allowed_platforms": ["instagram", "youtube"],
    "allowed_territories": ["IN"], "permitted_uses": ["embedded_ad"],
    "attribution_required": False, "expires_at": None,
}


class AudioCatalogTests(unittest.TestCase):
    def test_explicit_approved_track_context(self):
        self.assertEqual(authorized_track(BASE, "instagram", "IN", "embedded_ad", NOW),
                         "asset_approved_1")

    def test_unreviewed_and_revoked_fail_closed(self):
        for status in ("pending", "revoked", "restricted"):
            record = dict(BASE, status=status)
            with self.assertRaises(AudioCatalogError):
                authorized_track(record, "youtube", "IN", "embedded_ad", NOW)

    def test_platform_territory_organic_and_standalone_denied(self):
        for platform, territory, usage in (
            ("facebook", "IN", "embedded_ad"),
            ("youtube", "US", "embedded_ad"),
            ("youtube", "IN", "embedded_organic"),
            ("youtube", "IN", "standalone_export"),
        ):
            with self.assertRaises(AudioCatalogError):
                authorized_track(BASE, platform, territory, usage, NOW)

    def test_expiry_future_review_and_missing_evidence_denied(self):
        for overrides in (
            {"expires_at": "2026-10-25T00:00:00Z"},
            {"reviewed_at": "2026-10-27T00:00:00Z"},
            {"license_evidence_id": ""},
            {"source": "http://untrusted.invalid/file"},
            {"allowed_platforms": []},
        ):
            record = copy.deepcopy(BASE)
            record.update(overrides)
            with self.assertRaises(AudioCatalogError):
                authorized_track(record, "instagram", "IN", "embedded_ad", NOW)

    def test_timestamp_requires_timezone(self):
        record = dict(BASE, reviewed_at="2026-10-20T00:00:00")
        with self.assertRaises(AudioCatalogError):
            authorized_track(record, "instagram", "IN", "embedded_ad", NOW)


if __name__ == "__main__":
    unittest.main()
