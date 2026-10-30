"""Bounded 30s encoded mock editor parity and untrusted-source negatives."""
import hashlib
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "video-engine"))
from feature4_edited_export_qa import EditorExportProofError, verify_mock_editor_output
import feature4_edited_export_qa as qa


class EncodedEditorParityTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory(prefix="f4-edit-parity-")
        self.addCleanup(temp.cleanup)
        self.root = Path(temp.name)
        self.file = self.root / "mock-only.mp4"
        self.file.write_bytes(b"encoded-mock-packets" * 200)
        self.profile = {"width": 540, "height": 960, "seconds": 30.0}
        self.valid = (bytes([20])*9216, bytes([70])*9216,
                      bytes([24])*9216, bytes([120])*9216)

    def prove(self, frames=None):
        with patch.object(qa, "inspect_mp4", return_value=self.profile), \
             patch.object(qa, "_frame", side_effect=list(frames or self.valid)):
            return verify_mock_editor_output(self.file)

    def test_valid_decoded_pattern_is_source_sha_bound_not_product_approval(self):
        proof = self.prove()
        self.assertEqual(proof["timeline_starts_seconds"], [0, 4, 14, 20])
        self.assertEqual(proof["source_sha256"],
                         hashlib.sha256(self.file.read_bytes()).hexdigest())
        self.assertFalse(proof["exact_inpoint_frame_verified"])
        self.assertFalse(proof["human_visual_approval"])
        self.assertFalse(proof["commercial_release_eligible"])

    def test_replayed_video_or_wrong_scene_order_denied(self):
        v1, p1, v2, p2 = self.valid
        for frames in ((v1,p1,v1,p2), (p1,v1,v2,p2),
                       (v1,p1,p2,p2), (v1,v1,v2,p2), (v1,p1,v2,p1)):
            with self.subTest(variant=frames[:1]), \
                 self.assertRaises(EditorExportProofError):
                self.prove(frames)

    def test_malformed_decoded_frames_cannot_pass_pixel_parity(self):
        v1, p1, v2, p2 = self.valid
        for name, frames in (
            ("truncated-first-video", (v1[:-1], p1, v2, p2)),
            ("oversized-product-frame", (v1, p1 + b"\x00", v2, p2)),
            ("wrong-decoder-type", (v1, p1, bytearray(v2), p2)),
            ("empty-frame", (v1, p1, b"", p2)),
        ):
            with self.subTest(case=name), self.assertRaisesRegex(
                    EditorExportProofError, "Malformed encoded editor grayscale frame"):
                self.prove(frames)

    def test_mutated_input_and_wrong_duration_denied(self):
        frames = list(self.valid)
        def decode(src, at):
            if at == 2.0:
                with self.file.open("ab") as handle:
                    handle.write(b"tamper")
            return frames.pop(0)
        with patch.object(qa, "inspect_mp4", return_value=self.profile), \
             patch.object(qa, "_frame", side_effect=decode):
            with self.assertRaisesRegex(EditorExportProofError, "changed"):
                verify_mock_editor_output(self.file)
        self.profile["seconds"] = 29.0
        with self.assertRaisesRegex(EditorExportProofError, "30s"):
            self.prove()

    def test_nonvideo_and_symlink_source_denied(self):
        with self.assertRaises(EditorExportProofError):
            verify_mock_editor_output(self.file)
        backing = self.root / "real-mock.mp4"
        self.file.rename(backing)
        self.file.symlink_to(backing)
        with self.assertRaises(EditorExportProofError):
            verify_mock_editor_output(self.file)


if __name__ == "__main__":
    unittest.main()
