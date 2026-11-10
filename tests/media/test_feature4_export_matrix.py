"""F4-03 local 15/30/60 immutable encoded matrix; source test doubles never claim real render."""
from __future__ import annotations

import hashlib
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "video-engine"))
from feature4_export_matrix import MatrixEvidenceError, verify_export_matrix


HEAD = "a" * 40


class OfflineExportMatrixTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory(prefix="f4-matrix-")
        self.addCleanup(temp.cleanup)
        self.root = Path(temp.name)
        self.rows = []
        for duration in (15, 30, 60):
            name = f"synthetic-{duration}s.mp4"
            data = bytes([duration]) * 4096
            (self.root / name).write_bytes(data)
            self.rows.append({"seconds": duration, "path": name,
                              "sha256": hashlib.sha256(data).hexdigest()})
        self.manifest = {"schema": "feature4_export_matrix_inputs_v1",
                         "source_commit": HEAD, "renders": self.rows}

    def proof(self):
        def local_probe(path, *, duration, width, height, fps):
            self.assertEqual((width, height, fps), (1080, 1920, 24))
            self.assertTrue(path.name.endswith(f"{duration}s.mp4"))
            return {"bytes": path.stat().st_size, "duration_seconds": duration,
                    "width": width, "height": height, "fps": fps,
                    "video_codec": "h264", "audio_codec": "aac"}
        with patch("feature4_export_matrix.verify_mp4", side_effect=local_probe):
            return verify_export_matrix(self.manifest, self.root, expected_head=HEAD)

    def test_all_three_actual_filenames_sha_bound_without_release_approval(self):
        result = self.proof()
        self.assertEqual(result["status"],
                         "ALL_THREE_LOCAL_ENCODED_PROFILES_TECHNICALLY_CHECKED")
        self.assertEqual([x["seconds"] for x in result["renders"]], [15, 30, 60])
        self.assertTrue(all(len(x["sha256"]) == 64 for x in result["renders"]))
        self.assertFalse(result["commercial_release_eligible"])
        self.assertFalse(result["code_commit_attested_by_ci"])
        self.assertFalse(result["human_visual_approval"])

    def test_incomplete_duplicate_forged_or_stale_head_denied(self):
        for variant in ("missing", "duplicate", "stale", "tamper", "fake_sha"):
            with self.subTest(variant=variant):
                self.setUp_case(variant)
                with self.assertRaises(MatrixEvidenceError):
                    self.proof()

    def setUp_case(self, variant):
        import copy
        # Restore records from local media, not a previously mutated list.
        self.rows = [{"seconds": x, "path": f"synthetic-{x}s.mp4",
                      "sha256": hashlib.sha256(bytes([x]) * 4096).hexdigest()}
                     for x in (15, 30, 60)]
        self.manifest = {"schema": "feature4_export_matrix_inputs_v1",
                         "source_commit": HEAD, "renders": copy.deepcopy(self.rows)}
        if variant == "missing":
            self.manifest["renders"].pop()
        elif variant == "duplicate":
            self.manifest["renders"][2]["seconds"] = 30
        elif variant == "stale":
            self.manifest["source_commit"] = "b" * 40
        elif variant == "tamper":
            (self.root / "synthetic-30s.mp4").write_bytes(b"changed" * 700)
        elif variant == "fake_sha":
            self.manifest["renders"][1]["sha256"] = "f" * 64

    def test_cross_shop_path_and_symlink_denied_before_probe(self):
        for invalid in ("../foreign.mp4", "/tmp/foreign.mp4", "dir/other.mp4",
                        "http://example.invalid/clip.mp4", "other\\foreign.mp4"):
            with self.subTest(path=invalid):
                self.manifest["renders"][0]["path"] = invalid
                with patch("feature4_export_matrix.verify_mp4") as inspect:
                    with self.assertRaises(MatrixEvidenceError):
                        self.proof()
                    inspect.assert_not_called()
        self.manifest["renders"][0]["path"] = "symlink.mp4"
        (self.root / "symlink.mp4").symlink_to(self.root / "synthetic-15s.mp4")
        with self.assertRaisesRegex(MatrixEvidenceError, "unsafe"):
            self.proof()

    def test_modified_during_ffprobe_denied_by_rehash(self):
        original = self.root / "synthetic-30s.mp4"
        def modify(path, *, duration, width, height, fps):
            if duration == 30:
                with original.open("ab") as out:
                    out.write(b"tamper")
            return {"bytes": (path.stat().st_size - (6 if duration == 30 else 0))}
        with patch("feature4_export_matrix.verify_mp4", side_effect=modify):
            with self.assertRaises(MatrixEvidenceError):
                verify_export_matrix(self.manifest, self.root, expected_head=HEAD)


if __name__ == "__main__":
    unittest.main()
