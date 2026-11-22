"""Exercise exact DEV project URI normalization without live passwords."""
import importlib.util
from pathlib import Path
import os
import tempfile
import unittest
from unittest.mock import patch

SCRIPT = Path(__file__).resolve().parents[2] / "scripts/deploy/feature4_cpu_db_uri_guard.py"
spec = importlib.util.spec_from_file_location("f4_cpu_db_uri_guard_test", SCRIPT)
guard = importlib.util.module_from_spec(spec)
spec.loader.exec_module(guard)

POOLER = "aws-0-ap-northeast-1.pooler.supabase.com"
PROJECT = "jeearzffnjbvghwjjjrf"


class Feature4ExactDevUriGuardTests(unittest.TestCase):
    def test_session_pooler_preserves_raw_reserved_password(self):
        original = f"postgresql://postgres.{PROJECT}:my:secret@p#word@{POOLER}:5432/postgres"
        normalized = guard.normalize_uri(original)
        self.assertEqual(normalized,
                         f"postgresql://postgres.{PROJECT}:my%3Asecret%40p%23word@{POOLER}:5432/postgres")
        self.assertEqual(guard.normalize_uri(normalized), normalized)

    def test_session_pooler_legacy_encoded_password_and_ssl(self):
        raw = f"postgres://postgres.{PROJECT}:a%40b%2Fc@{POOLER}:6543/postgres?sslmode=require"
        self.assertEqual(guard.normalize_uri(raw), raw)

    def test_direct_exact_project_only(self):
        raw = f"postgresql://postgres:s%40fe@db.{PROJECT}.supabase.co:5432/postgres"
        self.assertEqual(guard.normalize_uri(raw), raw)

    def test_foreign_or_ambiguous_endpoints_denied(self):
        for raw in (
            "",
            "jdbc:postgresql://anything",
            f"postgresql://postgres.{PROJECT}:passwd@evil.example:5432/postgres",
            f"postgresql://postgres.other:passwd@{POOLER}:5432/postgres",
            f"postgresql://postgres.{PROJECT}:passwd@{POOLER}:5432/other",
            f"postgresql://postgres.{PROJECT}:passwd@{POOLER}:9999/postgres",
            f"postgresql://postgres.{PROJECT}:passwd@{POOLER}:5432/postgres?sslmode=disable",
            f"postgresql://postgres.{PROJECT}:YOUR-PASSWORD@{POOLER}:5432/postgres",
        ):
            with self.subTest(raw=raw.split('@')[-1]):
                with self.assertRaises(guard.ProjectUriError):
                    guard.normalize_uri(raw)

    def test_file_mode_and_no_credentials_in_stdout(self):
        with tempfile.TemporaryDirectory() as d:
            secret = f"postgresql://postgres.{PROJECT}:fake@secret@{POOLER}:5432/postgres"
            with patch.dict(os.environ, {"RUNNER_TEMP":d, "RETAIL_SUPABASE_DB_URL":secret}):
                self.assertEqual(guard.main(), 0)
                private = Path(d)/guard.SAFE_FILENAME
                self.assertTrue(private.is_file())
                self.assertEqual(private.stat().st_mode & 0o777, 0o600)
                self.assertNotIn("fake@secret", private.read_text())
                # Exclusive creation refuses a second ambiguous write.
                self.assertEqual(guard.main(), 3)


if __name__ == "__main__":
    unittest.main()
