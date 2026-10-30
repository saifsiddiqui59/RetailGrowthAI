"""Cross-language curator packet compatibility and no-permission-escalation."""
from copy import deepcopy
import json
from pathlib import Path
import shutil
import subprocess
import sys
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "poster-engine"))
from openpeople_indian_review_v2 import (
    CANDIDATES, KINDS, UPSTREAM_REVISION,
    expected_review_packet, validate_review_packet, parse_review_packet_file,
)
from model_library_v2 import ModelLibraryDenied


class CandidateReviewTests(unittest.TestCase):
    def test_all_eight_are_source_pinned_and_default_unapproved(self):
        self.assertEqual(len(CANDIDATES), 8)
        self.assertEqual(len(UPSTREAM_REVISION), 40)
        for person_id, item in CANDIDATES.items():
            self.assertEqual(len(item), 4)
            self.assertIn("Indian", item[0])
            self.assertEqual(len(item[1]), 40)
            for kind in KINDS:
                packet = expected_review_packet(person_id, kind)
                self.assertIn("231f73aa43", packet["source_url"])
                self.assertEqual(packet["image_git_blob_sha"], item[KINDS[kind]])
                self.assertFalse(packet["commercially_reusable"])
                self.assertFalse(packet["saved_to_private_library"])
                self.assertEqual(packet["generation_gpu_calls"], 0)
                selection = parse_review_packet_file(
                    json.dumps(packet), dataset_root="/private/operator-staged")
                self.assertEqual(selection.person_id, person_id)
                self.assertEqual(selection.image_kind, kind)
                self.assertEqual(selection.expected_image_git_blob_sha,
                                 packet["image_git_blob_sha"])

    @unittest.skipUnless(shutil.which("node"), "Node is required for exact React/Python contract")
    def test_browser_js_and_python_generate_exact_identical_review_packets(self):
        script = """
        import {INDIAN_MODEL_CANDIDATES,createIndianModelReviewPacket}
          from './frontend/src/features/creative/feature3-indian-model-review.mjs';
        const all = INDIAN_MODEL_CANDIDATES.flatMap(c=>
          ['studio_posture','studio_portrait'].map(kind=>
            createIndianModelReviewPacket(c.id,kind)));
        console.log(JSON.stringify(all));
        """
        result = subprocess.run(["node", "--input-type=module", "-e", script],
                                capture_output=True, text=True, timeout=10,
                                check=True, cwd=ROOT)
        packets = json.loads(result.stdout)
        self.assertEqual(len(packets), 16)
        for packet in packets:
            expected = expected_review_packet(packet["person_id"],
                                              packet["image_kind"])
            self.assertEqual(packet, expected)
            validate_review_packet(packet, dataset_root="/private/curator")

    def test_browser_cannot_self_approve_relicense_repoint_or_change_model(self):
        base = expected_review_packet("P009", "studio_posture")
        mutations = [
            ("approved", True), ("licensed_for_retailgrowth", True),
            ("rights_evidence_verified", True), ("commercially_reusable", True),
            ("saved_to_private_library", True), ("published", True),
            ("generation_gpu_calls", 1),
            ("generation_gpu_calls", False),
            ("source_revision", "a"*40),
            ("image_git_blob_sha", "a"*40),
            ("metadata_git_blob_sha", "a"*40),
            ("person_id", "P001"), ("image_kind", "metadata.json"),
            ("source_url", "https://example.org/foreign.jpg"),
            ("source_repository", "malicious/repo"),
            ("source_license_claim", "MIT"),
            ("status", "APPROVED"),
            ("attribution", ""),
            ("source_profile_description", "verified Indian customer"),
        ]
        for name, value in mutations:
            with self.subTest(name=name, value=value):
                modified = {**base, name: value}
                with self.assertRaises(ModelLibraryDenied):
                    validate_review_packet(modified, dataset_root="/private/curator")
        with self.assertRaises(ModelLibraryDenied):
            validate_review_packet({**base, "admin": True},
                                   dataset_root="/private/curator")
        with self.assertRaises(ModelLibraryDenied):
            validate_review_packet(None, dataset_root="/private/curator")
        with self.assertRaises(ModelLibraryDenied):
            parse_review_packet_file("{" + "a"*7000, dataset_root="/private")
        with self.assertRaises(ModelLibraryDenied):
            parse_review_packet_file("{invalid}", dataset_root="/private")
        with self.assertRaises(ModelLibraryDenied):
            validate_review_packet(base, dataset_root=None)


if __name__ == "__main__":
    unittest.main()
