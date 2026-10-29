"""GPU-OFF real byte-level hash regression with tiny TEST-ONLY weight files.

The full production auditor retains immutable 18GB EXPECTED manifest; this
suite replaces the validator's local expected size/hash ONLY for fake files.
It is not a model-weight provenance/cost/license attestation.
"""
import hashlib
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from feature5_motion.infra import wan22_local_weight_audit as audit
from feature5_motion.shared_model_mount import EXPECTED, PreflightError
from test_feature5_shared_model_mount import sample


class FullWeightByteAuditTests(unittest.TestCase):
    def test_unmounted_or_malformed_private_manifest_denied(self):
        with tempfile.TemporaryDirectory() as td:
            with self.assertRaises(PreflightError):
                audit.audit_full_wan_model_bytes(
                    mounted_share_root=td, trusted_private_manifest={})
            with self.assertRaises(PreflightError):
                audit.audit_full_wan_model_bytes(
                    mounted_share_root=Path(td)/"missing",
                    trusted_private_manifest=sample())

    def test_small_real_file_bytes_match_only_independently_supplied_hashes(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td)
            expected=dict(EXPECTED)
            for i,name in enumerate(audit.WAN_FILES):
                content=(b"NON-WAN-TEST-FIXTURE-"+bytes([i]))*9
                f=root/name
                f.parent.mkdir(parents=True,exist_ok=True)
                f.write_bytes(content)
                old=EXPECTED[name]
                expected[name]=(len(content),hashlib.sha256(content).hexdigest(),old[2])
            with patch.object(audit,"EXPECTED",expected):
                report=audit.audit_full_wan_model_bytes(
                    mounted_share_root=root,trusted_private_manifest=sample())
                self.assertEqual(report["checkpoint_count"],3)
                self.assertEqual(report["checkpoint_bytes_sha256_verified"],
                                 sum(expected[k][0] for k in audit.WAN_FILES))
                self.assertFalse(report["license_approved"])
                self.assertFalse(report["read_only_mount_proven"])
                self.assertFalse(report["gpu_started"])
                self.assertFalse(report["image_built"])
                self.assertFalse(report["comfyui_runtime_validated"])
                f=root/audit.WAN_FILES[0]
                f.write_bytes(b"x"*expected[audit.WAN_FILES[0]][0])
                with self.assertRaises(PreflightError):
                    audit.audit_full_wan_model_bytes(
                        mounted_share_root=root,trusted_private_manifest=sample())

    def test_changed_length_hardlink_symlink_and_directory_traversal_denied(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td)
            name=audit.WAN_FILES[0]
            file=root/name
            file.parent.mkdir(parents=True)
            content=b"not a checkpoint"*32
            file.write_bytes(content)
            digest=hashlib.sha256(content).hexdigest()
            self.assertEqual(audit._actual_full_sha(file,len(content),digest),len(content))
            with self.assertRaises(PreflightError):
                audit._actual_full_sha(file,len(content)+1,digest)
            with self.assertRaises(PreflightError):
                audit._actual_full_sha(file,len(content),"0"*64)
            other=root/"hardlink.safetensors"
            os.link(file,other)
            with self.assertRaises(PreflightError):
                audit._actual_full_sha(file,len(content),digest)
            other.unlink()
            linked=root/"linked.safetensors"
            linked.symlink_to(file)
            with self.assertRaises(PreflightError):
                audit._actual_full_sha(linked,len(content),digest)
            with self.assertRaises(PreflightError):
                audit._actual_full_sha(file,len(content),"INVALID")
