"""Actual SHA256 wheelhouse audit tests: all local fake wheels, no CUDA/network."""
from __future__ import annotations

import hashlib
from pathlib import Path
from tempfile import TemporaryDirectory
from zipfile import ZipFile, ZIP_DEFLATED
import unittest

from feature5_motion.infra.wan22_native_preflight import (
    REQUIRED_PACKAGES, audit_offline_wheelhouse,
    render_reviewed_require_hashes, validate_offline_requirements_file,
)
from feature5_motion.wan22_motion_adapter import WanCompatibilityError


def fake_wheels(folder):
    """Produce real but intentionally NON-INSTALLABLE dummy wheel fixtures."""
    base=Path(folder)
    reviews={}
    for name in sorted(REQUIRED_PACKAGES):
        slug=name.replace("-","_").lower()
        version="1.2.3"
        path=base/(slug+"-"+version+"-py3-none-any.whl")
        with ZipFile(path,"w",compression=ZIP_DEFLATED) as archive:
            dist=slug+"-"+version+".dist-info"
            archive.writestr(dist+"/METADATA",
                "Metadata-Version: 2.1\nName: "+name+"\nVersion: "+version+"\n")
            archive.writestr(dist+"/WHEEL","Wheel-Version: 1.0\nGenerator: synthetic-test\nRoot-Is-Purelib: true\nTag: py3-none-any\n")
            archive.writestr(slug+"/__init__.py","__synthetic_fixture_only__ = True\n")
        reviews[name]={"version":version,"sha256":hashlib.sha256(path.read_bytes()).hexdigest()}
    return reviews


def fake_wheels_in_memory():
    return {name:{"version":"1.2.3","sha256":"a"*64}
            for name in REQUIRED_PACKAGES}


class WanOfflineWheelhouseTest(unittest.TestCase):
    def test_real_byte_sha256_audit_of_full_synthetic_wheelhouse(self):
        with TemporaryDirectory() as td:
            approved=fake_wheels(td)
            proof=audit_offline_wheelhouse(td,reviewed_wheel_sha256=approved)
            self.assertEqual(proof["wheel_count"],len(REQUIRED_PACKAGES))
            self.assertTrue(proof["actual_file_hashes_checked"])
            self.assertTrue(proof["offline_no_network"])
            self.assertFalse(proof["gpu_started"])

    def test_hash_mismatch_and_unexpected_wheel_fail_closed(self):
        with TemporaryDirectory() as td:
            approved=fake_wheels(td)
            wheel=next(Path(td).glob("torch-*.whl"))
            wheel.write_bytes(wheel.read_bytes()+b"attacker")
            with self.assertRaisesRegex(WanCompatibilityError,"SHA256"):
                audit_offline_wheelhouse(td,reviewed_wheel_sha256=approved)
        with TemporaryDirectory() as td:
            approved=fake_wheels(td)
            (Path(td)/"unreviewed-1.0-py3-none-any.whl").write_bytes(b"arbitrary")
            with self.assertRaises(WanCompatibilityError):
                audit_offline_wheelhouse(td,reviewed_wheel_sha256=approved)

    def test_missing_one_approved_wheel_and_symlink_denied(self):
        with TemporaryDirectory() as td:
            approved=fake_wheels(td)
            next(Path(td).glob("torch-*.whl")).unlink()
            with self.assertRaisesRegex(WanCompatibilityError,"missing"):
                audit_offline_wheelhouse(td,reviewed_wheel_sha256=approved)
        with TemporaryDirectory() as td:
            approved=fake_wheels(td)
            original=next(Path(td).glob("torch-*.whl"))
            replacement=Path(td)/"torch_shadow.whl"
            original.rename(replacement)
            original.symlink_to(replacement)
            with self.assertRaises(WanCompatibilityError):
                audit_offline_wheelhouse(td,reviewed_wheel_sha256=approved)

    def test_embedded_package_metadata_tampered_even_with_forged_digest(self):
        with TemporaryDirectory() as td:
            approved=fake_wheels(td)
            path=next(Path(td).glob("torch-*.whl"))
            with ZipFile(path,"w") as archive:
                archive.writestr("torch-1.2.3.dist-info/METADATA","Name: other-package\nVersion: 1.2.3\n")
                archive.writestr("torch-1.2.3.dist-info/WHEEL","Wheel-Version: 1.0\n")
            approved["torch"]["sha256"]=hashlib.sha256(path.read_bytes()).hexdigest()
            with self.assertRaisesRegex(WanCompatibilityError,"identity"):
                audit_offline_wheelhouse(td,reviewed_wheel_sha256=approved)

    def test_wheelhouse_cannot_be_symlink_or_unreviewed_manifest(self):
        with TemporaryDirectory() as td:
            approved=fake_wheels(td)
            lnk=Path(td).parent/(Path(td).name+"_link")
            try:
                lnk.symlink_to(td,target_is_directory=True)
                with self.assertRaises(WanCompatibilityError):
                    audit_offline_wheelhouse(lnk,reviewed_wheel_sha256=approved)
            finally:
                lnk.unlink(missing_ok=True)
            with self.assertRaises(WanCompatibilityError):
                audit_offline_wheelhouse(td,reviewed_wheel_sha256={"torch":approved["torch"]})


    def test_lockfile_matches_entire_actual_sha_checked_wheel_inventory(self):
        with TemporaryDirectory() as td:
            approved=fake_wheels(td)
            proof=audit_offline_wheelhouse(td,reviewed_wheel_sha256=approved)
            self.assertEqual(proof["wheel_count"],len(approved))
            text=render_reviewed_require_hashes(approved)
            # Store lock outside wheel directory: no unexpected wheelhouse entries.
            target=Path(td).parent/(Path(td).name+".require-hashes.txt")
            try:
                target.write_text(text,encoding="utf8")
                self.assertTrue(validate_offline_requirements_file(
                    target,reviewed_wheel_sha256=approved))
                target.write_text(text+"--extra-index-url https://external.invalid\n")
                with self.assertRaisesRegex(WanCompatibilityError,"differ"):
                    validate_offline_requirements_file(target,reviewed_wheel_sha256=approved)
                target.unlink()
                target.symlink_to(Path(td)/"torch-1.2.3-py3-none-any.whl")
                with self.assertRaises(WanCompatibilityError):
                    validate_offline_requirements_file(target,reviewed_wheel_sha256=approved)
            finally:
                target.unlink(missing_ok=True)

    def test_reject_injected_pip_option_and_normalized_dependency_alias(self):
        manifest=fake_wheels_in_memory()
        bad=dict(manifest)
        bad["--extra-index-url"]=dict(manifest["torch"])
        with self.assertRaisesRegex(WanCompatibilityError,"Unsafe"):
            render_reviewed_require_hashes(bad)
        bad=dict(manifest)
        bad["TORCH"]=dict(manifest["torch"])
        with self.assertRaisesRegex(WanCompatibilityError,"Alias"):
            render_reviewed_require_hashes(bad)


if __name__ == "__main__":
    unittest.main()
