"""Offline synthetic source-manifest tests. NOT an official ComfyUI checkout."""
from __future__ import annotations

import hashlib
import os
from unittest.mock import patch
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from feature5_motion.infra import wan22_source_audit as audit
from feature5_motion.infra.wan22_source_audit import (
    COMFY_SOURCE_COMMIT, REQUIRED, SourceAuditError,
    validate_source_manifest, audit_complete_vendor_checkout, main,
)


def fixture(root):
    base=Path(root)
    files={}
    for name in sorted(REQUIRED):
        data=(COMFY_SOURCE_COMMIT+"\n" if name=="REVIEWED_SOURCE_COMMIT"
              else "test-only fake ComfyUI source path "+name+"\n").encode()
        p=base/name
        p.parent.mkdir(parents=True,exist_ok=True)
        p.write_bytes(data)
        files[name]=hashlib.sha256(data).hexdigest()
    return {"schema":"retailgrowth.wan22.comfyui-source-lock.v1",
            "source_commit":COMFY_SOURCE_COMMIT,"files":files}


class SourceAuditTests(unittest.TestCase):
    def test_complete_actual_bytes_are_checked_not_only_commit_marker(self):
        with TemporaryDirectory() as td:
            manifest=fixture(td)
            result=audit_complete_vendor_checkout(td,reviewed_manifest=manifest)
            self.assertEqual(result["file_count"],len(REQUIRED))
            self.assertTrue(result["actual_source_sha256_checked"])
            self.assertFalse(result["network_used"])
            self.assertFalse(result["gpu_started"])
            self.assertEqual(validate_source_manifest(manifest),manifest["files"])

    def test_changed_extra_missing_and_linked_file_denials(self):
        with TemporaryDirectory() as td:
            m=fixture(td)
            target=Path(td)/"comfy_extras/nodes_video.py"
            target.write_text("tampered fake node\n")
            with self.assertRaisesRegex(SourceAuditError,"bytes changed"):
                audit_complete_vendor_checkout(td,reviewed_manifest=m)
        with TemporaryDirectory() as td:
            m=fixture(td)
            (Path(td)/"unreviewed_backdoor.py").write_text("print('oops')")
            with self.assertRaisesRegex(SourceAuditError,"unreviewed"):
                audit_complete_vendor_checkout(td,reviewed_manifest=m)
        with TemporaryDirectory() as td:
            m=fixture(td)
            (Path(td)/"nodes.py").unlink()
            with self.assertRaisesRegex(SourceAuditError,"Incomplete"):
                audit_complete_vendor_checkout(td,reviewed_manifest=m)
        with TemporaryDirectory() as td:
            m=fixture(td)
            p=Path(td)/"nodes.py"
            p.unlink()
            p.symlink_to(Path(td)/"main.py")
            with self.assertRaisesRegex(SourceAuditError,"linked"):
                audit_complete_vendor_checkout(td,reviewed_manifest=m)
        with TemporaryDirectory() as td:
            m=fixture(td)
            p=Path(td)/"rogue"
            p.symlink_to(Path(td)/"comfy_extras",target_is_directory=True)
            with self.assertRaisesRegex(SourceAuditError,"Symlinked"):
                audit_complete_vendor_checkout(td,reviewed_manifest=m)

    def test_external_hardlink_of_reviewed_source_is_denied(self):
        """A valid digest does not make mutable multiply-linked source safe."""
        with TemporaryDirectory() as td:
            vendor = Path(td) / "vendor"
            vendor.mkdir()
            manifest = fixture(vendor)
            os.link(vendor / "nodes.py", Path(td) / "outside-alias.py")
            with self.assertRaisesRegex(SourceAuditError, "linked"):
                audit_complete_vendor_checkout(vendor, reviewed_manifest=manifest)

    def test_source_path_replaced_after_descriptor_open_is_denied(self):
        """The hash of a displaced inode must not attest its old pathname."""
        with TemporaryDirectory() as td:
            vendor = Path(td) / "vendor"
            vendor.mkdir()
            manifest = fixture(vendor)
            target = vendor / "nodes.py"
            displaced = Path(td) / "displaced.py"
            replacement = Path(td) / "replacement.py"
            replacement.write_bytes(target.read_bytes())
            original_inode = target.stat().st_ino
            original_fstat = os.fstat
            target_calls = 0

            def replace_on_final_fstat(fd):
                nonlocal target_calls
                opened = original_fstat(fd)
                if opened.st_ino == original_inode:
                    target_calls += 1
                    if target_calls == 2:
                        os.replace(target, displaced)
                        os.replace(replacement, target)
                return original_fstat(fd)

            with patch.object(audit.os, "fstat", side_effect=replace_on_final_fstat):
                with self.assertRaisesRegex(SourceAuditError, "changed"):
                    audit_complete_vendor_checkout(vendor, reviewed_manifest=manifest)
            self.assertEqual(target_calls, 2)
            self.assertNotEqual(target.stat().st_ino, displaced.stat().st_ino)

    def test_pinned_commit_marker_is_not_sufficient_and_unsafe_paths_denied(self):
        with TemporaryDirectory() as td:
            m=fixture(td)
            m["files"]["../rogue.py"]="b"*64
            with self.assertRaisesRegex(SourceAuditError,"Unsafe"):
                audit_complete_vendor_checkout(td,reviewed_manifest=m)
        with TemporaryDirectory() as td:
            m=fixture(td)
            m["source_commit"]="0"*40
            with self.assertRaisesRegex(SourceAuditError,"pinned"):
                audit_complete_vendor_checkout(td,reviewed_manifest=m)
        with TemporaryDirectory() as td:
            m=fixture(td)
            marker=Path(td)/"REVIEWED_SOURCE_COMMIT"
            marker.write_text("different commit\n")
            m["files"]["REVIEWED_SOURCE_COMMIT"]=hashlib.sha256(marker.read_bytes()).hexdigest()
            with self.assertRaisesRegex(SourceAuditError,"marker"):
                audit_complete_vendor_checkout(td,reviewed_manifest=m)
        with TemporaryDirectory() as td:
            m=fixture(td)
            m["files"]["comfy_extras//nodes_video.py"]="a"*64
            with self.assertRaisesRegex(SourceAuditError,"Unsafe"):
                audit_complete_vendor_checkout(td,reviewed_manifest=m)

    def test_real_offline_cli_exit_and_zero_network(self):
        with TemporaryDirectory() as td:
            source=Path(td)/"vendor"
            source.mkdir()
            manifest=fixture(source)
            spec=Path(td)/"source.sha256.json"
            spec.write_text(json.dumps(manifest))
            self.assertEqual(main(["--source",str(source),"--manifest",str(spec)]),0)
            spec.write_text("{}")
            with self.assertRaises(SystemExit):
                main(["--source",str(source),"--manifest",str(spec)])


if __name__ == "__main__":
    unittest.main()
