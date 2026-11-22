"""Fail-closed source-only checks for the isolated six-file F4 DEV SQL bundle."""
import importlib.util
from pathlib import Path
import shutil
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[2]
MODULE = ROOT / "scripts" / "deploy" / "feature4_cpu_release_bundle.py"
SPEC = importlib.util.spec_from_file_location("feature4_cpu_release_bundle", MODULE)
bundle = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(bundle)


def copy_candidates(root):
    for name in bundle.CANDIDATES:
        src = ROOT / name
        dst = root / name
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst)


class Feature4CpuReleaseBundleTest(unittest.TestCase):
    def test_one_outer_transaction_and_exact_six_sources(self):
        sql, receipt = bundle.build_bundle(ROOT)
        self.assertEqual(sql.count("-- SOURCE: supabase/candidates/"), 6)
        self.assertTrue(sql.startswith("-- SOURCE-ONLY:"))
        self.assertTrue(sql.rstrip().endswith("commit;"))
        self.assertEqual(sql.lower().count("\nbegin;"), 1)
        self.assertEqual(sql.lower().count("\ncommit;"), 1)
        self.assertIn("partially installed schema detected", sql)
        self.assertEqual(receipt["expected_dev_project"], bundle.DEV_PROJECT)
        self.assertFalse(receipt["hosted_deployed"])
        self.assertEqual(len(receipt["files"]), 6)
        self.assertEqual({f["path"] for f in receipt["files"]},
                         set(bundle.CANDIDATES))

    def test_missing_source_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            copy_candidates(root)
            (root / bundle.CANDIDATES[0]).unlink()
            with self.assertRaisesRegex(bundle.ReleaseGuardError, "Missing or linked"):
                bundle.build_bundle(root)

    def test_sql_after_commit_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            copy_candidates(root)
            candidate = root / bundle.CANDIDATES[0]
            candidate.write_text(candidate.read_text() + "\nselect 1;\n")
            with self.assertRaisesRegex(bundle.ReleaseGuardError, "SQL after COMMIT"):
                bundle.build_bundle(root)

    def test_duplicate_begin_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            copy_candidates(root)
            candidate = root / bundle.CANDIDATES[1]
            candidate.write_text(candidate.read_text().replace("begin;", "begin;\nbegin;", 1))
            with self.assertRaisesRegex(bundle.ReleaseGuardError, "exactly one BEGIN/COMMIT"):
                bundle.build_bundle(root)

    def test_candidate_symlink_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            copy_candidates(root)
            candidate = root / bundle.CANDIDATES[0]
            outside = root / "outside.sql"
            shutil.copy2(candidate, outside)
            candidate.unlink()
            candidate.symlink_to(outside)
            with self.assertRaisesRegex(bundle.ReleaseGuardError, "Missing or linked"):
                bundle.build_bundle(root)

    def test_offline_build_has_no_write_side_effects(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            copy_candidates(root)
            sql, receipt = bundle.build_bundle(root)
            self.assertIn("create function", sql.lower())
            self.assertTrue(receipt["kind"].endswith("NOT_APPLIED"))
            self.assertFalse((root / "feature4_release.sql").exists())


if __name__ == "__main__":
    unittest.main()
