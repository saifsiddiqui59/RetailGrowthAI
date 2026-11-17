"""#249: original JWT verifier distinguishes JWKS outage from forged JWT.

Uses the actual project SupabaseJWTVerifier and original HTTPAPI. Entirely
offline synthetic signing-key client; no Azure, Supabase, user or worker writes.
"""
from pathlib import Path
import sys
import unittest
from unittest.mock import Mock

import jwt
from jwt.exceptions import PyJWKClientConnectionError, PyJWKClientError

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "ai-agents/src"))
sys.path.insert(0, str(ROOT / "azure-functions/campaign-api"))
from http_api import HTTPAPI  # noqa: E402
from security import (AuthenticationError, SigningKeysUnavailable,
                      SupabaseJWTVerifier)  # noqa: E402

ORIGIN = "https://synthetic-p0249.supabase.co"
CAMPAIGN = "11111111-1111-4111-8111-111111111111"
SYNTHETIC_TOKEN = "fake.header.signature"


class NoTenantCalls:
    def __getattr__(self, name):
        raise AssertionError("JWT must be verified before database access: " + name)


def api_with_error(error):
    key_lookup = Mock(side_effect=error)
    verifier = SupabaseJWTVerifier(
        ORIGIN, jwks_client=Mock(get_signing_key_from_jwt=key_lookup))
    return HTTPAPI(verifier, NoTenantCalls()), key_lookup


class JWKSOutageClassificationTests(unittest.TestCase):
    def test_temporary_jwks_connection_failure_returns_503_not_401(self):
        api, lookup = api_with_error(
            PyJWKClientConnectionError("fake upstream failure token=sensitive"))
        status, payload = api.handle("GET", "/campaigns/" + CAMPAIGN,
                                     "Bearer " + SYNTHETIC_TOKEN)
        self.assertEqual((status, payload),
                         (503, {"error": "SERVICE_UNAVAILABLE"}))
        lookup.assert_called_once_with(SYNTHETIC_TOKEN)
        self.assertNotIn("sensitive", str(payload))

    def test_original_verifier_distinguishes_network_and_invalid_signature(self):
        for error, kind in (
            (PyJWKClientConnectionError("fake JWKS timeout"), SigningKeysUnavailable),
            (PyJWKClientError("kid not found"), AuthenticationError),
            (jwt.InvalidSignatureError("signature invalid"), AuthenticationError),
        ):
            with self.subTest(error=type(error).__name__):
                client = Mock(get_signing_key_from_jwt=Mock(side_effect=error))
                verifier = SupabaseJWTVerifier(ORIGIN, jwks_client=client)
                with self.assertRaises(kind) as raised:
                    verifier(SYNTHETIC_TOKEN)
                self.assertNotIn("fake JWKS", str(raised.exception))

    def test_invalid_token_fails_before_jwks_and_returns_401(self):
        api, lookup = api_with_error(
            PyJWKClientConnectionError("unreachable JWKS"))
        for authorization in ("", "Basic synthetic", "Bearer ",
                              "Bearer " + "a" * 8193):
            with self.subTest(authorization=authorization[:20]):
                status, payload = api.handle("GET", "/campaigns/" + CAMPAIGN,
                                             authorization)
                self.assertEqual((status, payload),
                                 (401, {"error": "UNAUTHORIZED"}))
        lookup.assert_not_called()

    def test_invalid_kid_stays_401_without_database_access(self):
        api, lookup = api_with_error(PyJWKClientError("key id unavailable"))
        self.assertEqual(
            api.handle("GET", "/campaigns/" + CAMPAIGN,
                       "Bearer " + SYNTHETIC_TOKEN),
            (401, {"error": "UNAUTHORIZED"}))
        lookup.assert_called_once()


if __name__ == "__main__":
    unittest.main()
