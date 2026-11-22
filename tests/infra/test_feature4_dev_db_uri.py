"""Offline negative tests for protected DEV DB connection URI normalization."""
import unittest

from scripts.deploy.feature4_dev_db_uri import (
    DevDatabaseUriError, POOLER, PROJECT, normalize_dev_url,
)


class Feature4DevUriTests(unittest.TestCase):
    def test_exact_legacy_pooler_uri_is_supported(self):
        raw = f"postgresql://postgres.{PROJECT}:supersecret@{POOLER}:5432/postgres"
        self.assertEqual(normalize_dev_url(raw), raw)

    def test_raw_reserved_password_is_encoded_not_exposed(self):
        raw = f"postgresql://postgres.{PROJECT}:a/b#c:d@{POOLER}:5432/postgres"
        result = normalize_dev_url(raw)
        self.assertEqual(result, f"postgresql://postgres.{PROJECT}:a%2Fb%23c%3Ad@{POOLER}:5432/postgres")

    def test_valid_direct_host(self):
        uri = f"postgresql://postgres:test-secret@db.{PROJECT}.supabase.co:5432/postgres"
        self.assertEqual(normalize_dev_url(uri), uri)

    def test_valid_pooler_transaction_port(self):
        uri = f"postgresql://postgres.{PROJECT}:test-secret@{POOLER}:6543/postgres"
        self.assertEqual(normalize_dev_url(uri), uri)

    def test_deny_cross_project_and_foreign_host(self):
        invalid = [
            f"postgresql://postgres.foreign:secret@{POOLER}:5432/postgres",
            f"postgresql://postgres.{PROJECT}:secret@evil.example:5432/postgres",
            f"postgresql://postgres.{PROJECT}:secret@{POOLER}:5432/other",
            f"postgresql://postgres.{PROJECT}:secret@{POOLER}:5432/postgres#fragment",
            f"postgresql://postgres.{PROJECT}:secret@{POOLER}:5432/postgres?sslmode=disable",
            f"postgresql://postgres.{PROJECT}:YOUR-PASSWORD@{POOLER}:5432/postgres",
            f"postgresql://postgres.{PROJECT}:@{POOLER}:5432/postgres",
            "not a URL",
        ]
        for uri in invalid:
            with self.subTest(uri=uri), self.assertRaises(DevDatabaseUriError):
                normalize_dev_url(uri)


if __name__ == "__main__":
    unittest.main()
