"""Offline synthetic source-manifest tests. NOT an official ComfyUI checkout."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch
import unittest

from feature5_motion.infra import wan22_source_audit as source_audit
from feature5_motion.infra.wan22_source_audit import (
    COMFY_SOURCE_COMMIT, REQUIRED, SourceAuditError,
    validate_source_manifest, audit_complete_vendor_checkout,
    read_reviewed_source_manifest, main,
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

    def test_standalone_containerfile_source_reader_rejects_ambiguous_json(self):
        with TemporaryDirectory() as td:
            source = Path(td) / "vendor"
            source.mkdir()
            reviewed = fixture(source)
            manifest = Path(td) / "manifest.json"
            manifest.write_text(json.dumps(reviewed), encoding="utf8")
            self.assertEqual(read_reviewed_source_manifest(manifest), reviewed)
            cases = (
                '{"files":{"main.py":"first","main.py":"second"}}',
                '{"outer":{"reviewed":true,"reviewed":false}}',
                '{"size":NaN}',
                '{"size":-Infinity}',
                "null",
                "[]",
                "[" * 20000 + "0" + "]" * 20000,
            )
            for bad in cases:
                with self.subTest(input_head=bad[:24]):
                    manifest.write_text(bad, encoding="utf8")
                    with self.assertRaisesRegex(SourceAuditError, "ambiguous"):
                        read_reviewed_source_manifest(manifest)
                    with self.assertRaises(SystemExit):
                        main(["--source", str(source), "--manifest", str(manifest)])
            manifest.write_text("{}", encoding="utf8")
            linked = Path(td) / "manifest.link"
            linked.symlink_to(manifest)
            with self.assertRaises(SourceAuditError):
                read_reviewed_source_manifest(linked)

    def test_replaced_same_byte_inode_after_first_hash_is_denied(self):
        """All source paths must remain the exact verified files through audit end."""
        with TemporaryDirectory() as td:
            manifest = fixture(td)
            target = Path(td) / "nodes.py"
            real_hash = source_audit._hash_verified_source
            changed = []

            def replace_after_hash(item, expected_sha):
                identity = real_hash(item, expected_sha)
                if Path(item) == target and not changed:
                    replacement = target.with_suffix(".replacement")
                    replacement.write_bytes(target.read_bytes())
                    replacement.replace(target)
                    changed.append(True)
                return identity

            with patch.object(source_audit, "_hash_verified_source",
                              side_effect=replace_after_hash):
                with self.assertRaisesRegex(SourceAuditError, "identity changed"):
                    audit_complete_vendor_checkout(td, reviewed_manifest=manifest)
            self.assertEqual(changed, [True])

    def test_same_size_in_place_mutation_after_hash_is_denied(self):
        with TemporaryDirectory() as td:
            manifest = fixture(td)
            target = Path(td) / "nodes.py"
            real_hash = source_audit._hash_verified_source
            changed = []

            def mutate_after_hash(item, expected_sha):
                identity = real_hash(item, expected_sha)
                if Path(item) == target and not changed:
                    original = target.read_bytes()
                    target.write_bytes(b"X" + original[1:])
                    changed.append(True)
                return identity

            with patch.object(source_audit, "_hash_verified_source",
                              side_effect=mutate_after_hash):
                with self.assertRaisesRegex(SourceAuditError, "identity changed"):
                    audit_complete_vendor_checkout(td, reviewed_manifest=manifest)
            self.assertEqual(changed, [True])

    def test_symlink_swap_between_path_stat_and_open_is_denied(self):
        with TemporaryDirectory() as td:
            manifest = fixture(td)
            target = Path(td) / "nodes.py"
            replacement = Path(td) / "main.py"
            real_open = source_audit.os.open
            swapped = []

            def swap_then_open(path, flags, *args, **kwargs):
                if Path(path) == target and not swapped:
                    target.unlink()
                    target.symlink_to(replacement)
                    swapped.append(True)
                return real_open(path, flags, *args, **kwargs)

            with patch.object(source_audit.os, "open", side_effect=swap_then_open):
                with self.assertRaises(SourceAuditError):
                    audit_complete_vendor_checkout(td, reviewed_manifest=manifest)
            self.assertEqual(swapped, [True])

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
