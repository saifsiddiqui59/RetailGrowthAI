"""Offline regression checks for bounded retained-shop media preparation."""
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "e2e"))
import f4_reusable_dev_media as m

UID = "11111111-1111-4111-8111-111111111111"
SHOP = m.fixtures.expected_shop("a", "Synthetic Boutique A", UID)
ASSET = "22222222-2222-4222-8222-222222222222"


class MediaTests(unittest.TestCase):
    def test_png_is_deterministic_and_distinct(self):
        a = m.png("a")
        self.assertTrue(a.startswith(b"\x89PNG\r\n\x1a\n"))
        self.assertGreater(len(a), 100)
        self.assertEqual(a, m.png("a"))
        self.assertNotEqual(a, m.png("b"))

    def test_path_is_scoped(self):
        self.assertTrue(m.object_path(SHOP["id"]).startswith(SHOP["id"] + "/uploads/"))
        self.assertNotEqual(m.object_path(SHOP["id"]), m.object_path(UID))
        with self.assertRaises(Exception):
            m.object_path("../bad")

    def test_existing_exact_media_is_read_only(self):
        expected = m.expected_metadata(SHOP)
        with patch.object(m, "metadata", return_value=[{"id": ASSET, **expected}]), \
             patch.object(m, "storage", return_value=(200, m.png("a"))) as s, \
             patch.object(m.fixtures, "user_call") as rpc:
            self.assertEqual(m.own_media({}, SHOP, "a"), expected)
            self.assertEqual(s.call_count, 1)
            rpc.assert_not_called()

    def test_refuses_wrong_bytes(self):
        with patch.object(m, "metadata", return_value=[]), \
             patch.object(m, "storage", return_value=(200, b"wrong")), \
             patch.object(m.fixtures, "user_call") as rpc:
            with self.assertRaisesRegex(RuntimeError, "EXISTING_MEDIA_BYTES_MISMATCH"):
                m.own_media({}, SHOP, "a")
            rpc.assert_not_called()

    def test_upload_requires_absence_and_registration_readback(self):
        expected = m.expected_metadata(SHOP)
        with patch.object(m, "metadata", side_effect=[[], [{"id": ASSET, **expected}]]), \
             patch.object(m, "storage", side_effect=[(404, b""), (201, b""), (200, m.png("a"))]) as s, \
             patch.object(m.fixtures, "user_call", side_effect=[[], ASSET]) as rpc:
            self.assertEqual(m.own_media({}, SHOP, "a"), expected)
            self.assertEqual(s.call_count, 3)
            self.assertEqual(rpc.call_count, 2)

    def test_does_not_retry_uncertain_upload(self):
        with patch.object(m, "metadata", return_value=[]), \
             patch.object(m, "storage", side_effect=[(404, b""), (503, b"")]) as s, \
             patch.object(m.fixtures, "user_call", return_value=[]) as rpc:
            with self.assertRaisesRegex(RuntimeError, "UPLOAD_FAILED_OR_UNCERTAIN"):
                m.own_media({}, SHOP, "a")
            self.assertEqual(s.call_count, 2)
            self.assertEqual(rpc.call_count, 1)

    def test_no_unapproved_execution(self):
        with patch.dict(m.os.environ, {}, clear=True), patch.object(m.fixtures, "preflight") as gate:
            with self.assertRaisesRegex(RuntimeError, "MEDIA_CONFIRM_REQUIRED"):
                m.main()
            gate.assert_not_called()
