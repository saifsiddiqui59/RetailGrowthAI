"""Composite no-GPU image-build gate, using SYNTHETIC wheel/source bytes."""
from __future__ import annotations

import json
import os

import copy
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
                                                "Unreadable reviewed manifest"):
                        _private_review_json(path)


    def test_review_json_symlink_hardlink_and_same_byte_path_swap_denied(self):
        with TemporaryDirectory() as td:
            root = Path(td)
            approved = root / "review.json"
            approved.write_text('{"source_commit":"original"}')
            linked = root / "linked.json"
            linked.symlink_to(approved)
            with self.assertRaises(WanCompatibilityError):
                _private_review_json(linked)
            hardlink = root / "hardlink.json"
            os.link(approved, hardlink)
            with self.assertRaises(WanCompatibilityError):
                _private_review_json(approved)
            hardlink.unlink()

            replacement = root / "replacement.json"
            displaced = root / "displaced.json"
            replacement.write_bytes(approved.read_bytes())
            real_fstat = os.fstat
            calls = 0

            def replace_on_final_stat(fd):
                nonlocal calls
                calls += 1
                if calls == 2:
                    os.replace(approved, displaced)
                    os.replace(replacement, approved)
                return real_fstat(fd)

            with patch("feature5_motion.infra.wan22_build_context_gate.os.fstat",
                       side_effect=replace_on_final_stat):
                with self.assertRaisesRegex(WanCompatibilityError,
                                            "Unreadable reviewed manifest"):
                    _private_review_json(approved)
            self.assertEqual(calls, 2)
            self.assertNotEqual(approved.stat().st_ino, displaced.stat().st_ino)


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


if __name__=="__main__":
    unittest.main()
