"""Composite no-GPU image-build gate, using SYNTHETIC wheel/source bytes."""
from __future__ import annotations

import copy
import json
import os
from types import SimpleNamespace
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

from feature5_motion.infra.wan22_native_preflight import (
    render_reviewed_require_hashes,
)
from feature5_motion.infra.wan22_build_context_gate import (
    audit_wan22_build_context, _private_review_json,
)
from feature5_motion.wan22_motion_adapter import WanCompatibilityError
from test_feature5_wan22_source_audit import fixture as source_fixture
from test_feature5_wan22_wheelhouse_audit import fake_wheels

BASE="nvcr.io/nvidia/pytorch@sha256:"+"a"*64


def build_fixture(root):
    base=Path(root)
    vendor=base/"ComfyUI"
    vendor.mkdir()
    source=source_fixture(vendor)
    wheelhouse=base/"wheelhouse"
    wheelhouse.mkdir()
    reviewed=fake_wheels(wheelhouse)
    lock=base/"requirements.lock"
    lock.write_text(render_reviewed_require_hashes(reviewed))
    return dict(vendored_comfyui=vendor,source_manifest=source,
                wheelhouse=wheelhouse,reviewed_wheel_sha256=reviewed,
                require_hashes_file=lock,selected_base_image=BASE,
                independently_approved_base_image=BASE)


class PrivateBuildManifestInputTests(unittest.TestCase):
    def test_valid_non_authorizing_private_json_can_be_read(self):
        with TemporaryDirectory() as td:
            path = Path(td) / "review.json"
            path.write_text(json.dumps({"source_commit": "a" * 40, "files": []}))
            self.assertEqual(_private_review_json(path)["files"], [])

    def test_ambiguous_nonfinite_nondict_or_recursive_manifest_denied(self):
        cases = (
            '{"manifest":{"sha256":"original","sha256":"rewritten"}}',
            '{"cost":NaN}',
            '{"size":Infinity}',
            'null',
            '[]',
            "[" * 20000 + "0" + "]" * 20000,
        )
        with TemporaryDirectory() as td:
            path = Path(td) / "review.json"
            for raw in cases:
                with self.subTest(size=len(raw), prefix=raw[:24]):
                    path.write_text(raw)
                    with self.assertRaisesRegex(WanCompatibilityError,
                                                "Unreadable or ambiguous reviewed manifest"):
                        _private_review_json(path)


    def test_reviewed_manifest_path_swap_denied_even_when_bytes_match(self):
        with TemporaryDirectory() as td:
            root = Path(td)
            manifest = root / "review.json"
            manifest.write_text('{"approved":"test-only"}')
            other = root / "other.json"
            other.write_bytes(manifest.read_bytes())
            displaced = root / "displaced.json"
            original_fstat = os.fstat
            reads = []

            def replace_on_final_fstat(fd):
                reads.append(1)
                if len(reads) == 2:
                    os.replace(manifest, displaced)
                    os.replace(other, manifest)
                return original_fstat(fd)

            with patch(
                "feature5_motion.infra.wan22_build_context_gate.os.fstat",
                side_effect=replace_on_final_fstat,
            ), self.assertRaisesRegex(WanCompatibilityError, "Unreadable"):
                _private_review_json(manifest)
            self.assertEqual(len(reads), 2)
            self.assertNotEqual(displaced.stat().st_ino, manifest.stat().st_ino)

    def test_symlink_hardlink_and_ctime_drift_rejected_before_review(self):
        with TemporaryDirectory() as td:
            root = Path(td)
            manifest = root / "review.json"
            manifest.write_text('{"source":"synthetic"}')
            linked = root / "link.json"
            linked.symlink_to(manifest)
            with self.assertRaises(WanCompatibilityError):
                _private_review_json(linked)
            hardlinked = root / "hardlink.json"
            os.link(manifest, hardlinked)
            with self.assertRaises(WanCompatibilityError):
                _private_review_json(manifest)
            hardlinked.unlink()

            real_fstat = os.fstat
            calls = []
            def changed_ctime_on_second_fstat(fd):
                actual = real_fstat(fd)
                calls.append(1)
                if len(calls) != 2:
                    return actual
                # Same inode, bytes, size and mtime; only ctime has changed.
                fields = {
                    field: getattr(actual, field) for field in (
                        "st_dev", "st_ino", "st_mode", "st_nlink",
                        "st_size", "st_mtime_ns", "st_ctime_ns"
                    )
                }
                fields["st_ctime_ns"] += 1
                return SimpleNamespace(**fields)

            # Construct the ctime-drift stat surrogate without retaining any
            # customer file or changing the original reviewed manifest.
            with patch("feature5_motion.infra.wan22_build_context_gate.os.fstat",
                       side_effect=changed_ctime_on_second_fstat), self.assertRaises(
                           WanCompatibilityError):
                _private_review_json(manifest)
            self.assertEqual(len(calls), 2)

class ComfyOfflineImageBuildGateTests(unittest.TestCase):
    def test_complete_real_byte_audit_of_synthetic_artifacts_is_explicitly_gpu_off(self):
        with TemporaryDirectory() as td:
            evidence=audit_wan22_build_context(**build_fixture(td))
            self.assertEqual(evidence["schema"],"retailgrowth.feature5.wan22.offline-build-input-audit.v1")
            self.assertGreater(evidence["source_files_byte_hash_checked"],5)
            self.assertGreater(evidence["wheel_files_byte_hash_checked"],5)
            self.assertTrue(evidence["offline_exact_require_hashes_checked"])
            for key in ("actual_cuda_base_bytes_verified","licensing_and_cost_approved",
                        "image_built","comfyui_running","gpu_started",
                        "real_wan_output_generated"):
                self.assertFalse(evidence[key],key)

    def test_deny_wrong_base_digest_and_mutated_source_wheels_requirements(self):
        with TemporaryDirectory() as td:
            k=build_fixture(td)
            bad={**k,"selected_base_image":"nvidia/cuda:latest"}
            with self.assertRaisesRegex(WanCompatibilityError,"immutable"):
                audit_wan22_build_context(**bad)
            bad={**k,"independently_approved_base_image":"other.invalid/img@sha256:"+"b"*64}
            with self.assertRaisesRegex(WanCompatibilityError,"immutable"):
                audit_wan22_build_context(**bad)
            (k["vendored_comfyui"]/"nodes.py").write_text("corrupted")
            with self.assertRaises(ValueError):
                audit_wan22_build_context(**k)
        with TemporaryDirectory() as td:
            k=build_fixture(td)
            next(k["wheelhouse"].glob("torch-*.whl")).write_bytes(b"changed")
            with self.assertRaises(WanCompatibilityError):
                audit_wan22_build_context(**k)
        with TemporaryDirectory() as td:
            k=build_fixture(td)
            k["require_hashes_file"].write_text("torch\n--extra-index-url http://not-allowed\n")
            with self.assertRaisesRegex(WanCompatibilityError,"differ"):
                audit_wan22_build_context(**k)

    def test_manifest_is_not_auto_commercial_approval(self):
        with TemporaryDirectory() as td:
            k=build_fixture(td)
            copied=copy.deepcopy(k)
            copied["source_manifest"]["source_commit"]="0"*40
            with self.assertRaises(ValueError):
                audit_wan22_build_context(**copied)


    def test_review_manifest_rejects_duplicate_nonfinite_linked_and_non_object_json(self):
        """Synthetic review inputs must not turn into an ambiguous OCI approval."""
        with TemporaryDirectory() as td:
            root = Path(td)
            manifest = root / "review.json"
            for raw in (
                '{"source_commit":"a","source_commit":"b"}',
                '{"nested":{"sha":"a","sha":"b"}}',
                '{"digest":NaN}',
                '{"digest":Infinity}',
                '["not", "a", "manifest"]',
                'null',
                '{} trailing',
            ):
                with self.subTest(raw=raw):
                    manifest.write_text(raw, encoding="utf-8")
                    with self.assertRaises(WanCompatibilityError):
                        _private_review_json(manifest)
            manifest.write_text('{"sha":"synthetic-test-only"}', encoding="utf-8")
            self.assertEqual(
                _private_review_json(manifest), {"sha": "synthetic-test-only"}
            )
            symlink = root / "linked.json"
            symlink.symlink_to(manifest)
            with self.assertRaises(WanCompatibilityError):
                _private_review_json(symlink)
            import os
            hardlink = root / "hardlinked.json"
            os.link(manifest, hardlink)
            with self.assertRaises(WanCompatibilityError):
                _private_review_json(manifest)
            with self.assertRaises(WanCompatibilityError):
                _private_review_json(hardlink)


if __name__=="__main__":
    unittest.main()
