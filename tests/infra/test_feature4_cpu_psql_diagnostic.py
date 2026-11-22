"""No DEV DB secret or hostile psql text may be exposed by diagnostics."""
import contextlib
import io
from pathlib import Path
import tempfile
import unittest

from scripts.deploy.feature4_cpu_psql_diagnostic import classify, main


class Feature4PsqlRedactedDiagnosticsTests(unittest.TestCase):
    def test_expected_fixed_codes(self):
        cases = {
            "FATAL: password authentication failed for user X": "PASSWORD_AUTHENTICATION_FAILED",
            "FATAL: Tenant or user not found": "POOLER_USER_NOT_FOUND",
            "FATAL: no pg_hba.conf entry for host": "DATABASE_ACCESS_DENIED",
            "ERROR: permission denied for schema supabase_migrations": "DATABASE_ACCESS_DENIED",
            "ERROR: permission denied for relation": "DATABASE_PERMISSION_DENIED",
            "could not translate host name": "HOSTNAME_RESOLUTION",
            "SSL error: certificate verify failed": "TLS_CONNECTION_FAILURE",
            "connection timed out": "NETWORK_TIMEOUT",
            "connection refused": "DATABASE_NETWORK_UNREACHABLE",
            "ERROR: relation X does not exist": "SCHEMA_OBJECT_NOT_FOUND",
            "ERROR: syntax error at or near": "READONLY_SQL_SYNTAX_FAILURE",
            "invalid connection option": "INVALID_LIBPQ_URI",
            "FATAL secret=topsecret token=eyJabc": "DATABASE_CONNECTION_OR_SQL_UNCLASSIFIED",
        }
        for sample, expected in cases.items():
            with self.subTest(code=expected):
                self.assertEqual(classify(sample), expected)

    def test_never_prints_raw_error_or_password_and_cleans_temp(self):
        secret = "password:DO_NOT_PRINT; URL:postgresql://operator@secret.example/path"
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / "error.txt"
            path.write_text(secret)
            out = io.StringIO()
            with contextlib.redirect_stdout(out):
                rc = main([str(path)])
            self.assertEqual(rc, 3)
            self.assertIn("DATABASE_CONNECTION_OR_SQL_UNCLASSIFIED", out.getvalue())
            self.assertNotIn(secret, out.getvalue())
            self.assertNotIn("DO_NOT_PRINT", out.getvalue())
            self.assertFalse(path.exists())

    def test_missing_diagnostic_is_bounded(self):
        with tempfile.TemporaryDirectory() as d:
            out = io.StringIO()
            with contextlib.redirect_stdout(out):
                code = main([str(Path(d) / "absent")])
            self.assertEqual(code, 3)
            self.assertIn("PRIVATE_DIAGNOSTIC_UNAVAILABLE", out.getvalue())


if __name__ == "__main__":
    unittest.main()
