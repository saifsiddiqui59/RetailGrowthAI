"""Regression tests for fail-closed Gate2 ZIP membership preflight.

These use only synthetic bytes; no approved binaries, Azure, or provider calls.
"""
from __future__ import annotations

import importlib.util
from pathlib import Path
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[2]
SPEC = importlib.util.spec_from_file_location(
    "retailgrowth_zip_package", ROOT / "scripts" / "deploy" / "package.py"
)
package = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(package)


class Gate2ManifestPreflightTests(unittest.TestCase):
    def test_oversized_manifest_rejected_without_creating_artifact(self):
        with tempfile.TemporaryDirectory() as temp:
            destination = Path(temp) / "nested" / "functions.zip"
            entries = {f"ai_agents/module_{i:03d}.py": b"fixture" for i in range(121)}
            with self.assertRaisesRegex(ValueError, "exceeds 120 members"):
                package.write_zip(destination, entries)
            self.assertFalse(destination.exists())
            self.assertFalse(destination.parent.exists())

    def test_exact_member_limit_still_writes_deterministic_archive(self):
        with tempfile.TemporaryDirectory() as temp:
            destination = Path(temp) / "functions.zip"
            entries = {f"ai_agents/module_{i:03d}.py": b"fixture" for i in range(120)}
            package.write_zip(destination, entries)
            from zipfile import ZipFile
            with ZipFile(destination) as archive:
                self.assertEqual(len(archive.infolist()), 120)
                self.assertEqual(len(set(archive.namelist())), 120)


if __name__ == "__main__":
    unittest.main()
