"""Regression tests for fail-closed Gate2 ZIP membership preflight.

These use only synthetic bytes; no approved binaries, Azure, or provider calls.
"""
from __future__ import annotations

import importlib.util
import contextlib
import io
from unittest.mock import patch
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
            with self.assertRaisesRegex(ValueError, "exceeds 120 members") as failure:
                package.write_zip(destination, entries)
            self.assertIn("ai_agents/module_000.py", str(failure.exception))
            self.assertIn("ai_agents/module_120.py", str(failure.exception))
            self.assertFalse(destination.exists())
            self.assertFalse(destination.parent.exists())

    def test_unsafe_paths_rejected_before_artifact_creation(self):
        for unsafe in ("../escape.py", "/absolute.py", "nested/../escape.py",
                       "nested\\\\escape.py", ".env", "local.settings.json",
                       "nested/secret.env", ""):
            with self.subTest(name=unsafe), tempfile.TemporaryDirectory() as temp:
                destination = Path(temp) / "nested" / "functions.zip"
                with self.assertRaisesRegex(ValueError, "Unsafe or secret-like ZIP member"):
                    package.write_zip(destination, {unsafe: b"fixture"})
                self.assertFalse(destination.exists())
                self.assertFalse(destination.parent.exists())

    def test_source_only_check_rejects_oversized_deployable_manifest(self):
        # 118 source members + three required binary/license files exceed 120.
        entries = {f"ai_agents/module_{i:03d}.py": b"x" for i in range(118)}
        entries.update({
            "azure-functions/campaign-api/render_worker.py": b"x",
            "video-engine/render.py": b"x",
            "poster-engine/render.py": b"x",
            "ai_agents/schemas.py": b"x",
        })
        stdout, stderr = io.StringIO(), io.StringIO()
        with patch.object(package, "source_files", return_value=entries), \
             contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
            with self.assertRaisesRegex(ValueError, "120 maximum"):
                package.main(["--check"])
        self.assertIn("125/120", stdout.getvalue())
        self.assertIn("ai_agents=", stderr.getvalue())

    def test_source_only_check_accepts_exact_full_member_budget(self):
        entries = {f"ai_agents/module_{i:03d}.py": b"x" for i in range(113)}
        entries.update({
            "azure-functions/campaign-api/render_worker.py": b"x",
            "video-engine/render.py": b"x",
            "poster-engine/render.py": b"x",
            "ai_agents/schemas.py": b"x",
        })
        stdout = io.StringIO()
        with patch.object(package, "source_files", return_value=entries), \
             contextlib.redirect_stdout(stdout):
            self.assertEqual(package.main(["--check"]), 0)
        self.assertIn("120/120", stdout.getvalue())

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
