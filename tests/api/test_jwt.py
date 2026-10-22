"""Local RSA signature verification including malicious and malformed token cases."""
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from uuid import uuid4

import jwt
import pytest
from cryptography.hazmat.primitives.asymmetric import rsa

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "azure-functions" / "campaign-api"))
from security import AuthenticationError, SupabaseJWTVerifier


KEY = rsa.generate_private_key(public_exponent=65537, key_size=2048)
BAD_KEY = rsa.generate_private_key(public_exponent=65537, key_size=2048)
ISSUER = "https://retail-test.supabase.co/auth/v1"
USER = str(uuid4())


class TestJWK:
    key = KEY.public_key()


class FakeJWKClient:
    def get_signing_key_from_jwt(self, token):
        return TestJWK()


def signed(**updates):
    claims = {
        "sub": USER, "role": "authenticated", "iss": ISSUER,
        "aud": "authenticated",
        "iat": datetime.now(timezone.utc),
        "exp": datetime.now(timezone.utc) + timedelta(minutes=10),
    }
    claims.update(updates)
    return jwt.encode(claims, KEY, algorithm="RS256", headers={"kid": "local-test"})


def test_valid_signed_token_accepted():
    verify = SupabaseJWTVerifier("https://retail-test.supabase.co", jwks_client=FakeJWKClient())
    assert verify(signed()) == USER


@pytest.mark.parametrize("mutation", [
    {"iss": "https://other.supabase.co/auth/v1"},
    {"aud": "another-service"}, {"role": "service_role"},
    {"is_anonymous": True},
    {"sub": str(uuid4()) + "-x"},
    {"exp": datetime.now(timezone.utc) - timedelta(minutes=2)},
])
def test_wrong_claims_rejected(mutation):
    verify = SupabaseJWTVerifier("https://retail-test.supabase.co", jwks_client=FakeJWKClient())
    with pytest.raises(AuthenticationError):
        verify(signed(**mutation))


def test_signature_tampering_and_none_algorithm_rejected():
    verify = SupabaseJWTVerifier("https://retail-test.supabase.co", jwks_client=FakeJWKClient())
    bogus = jwt.encode({"sub": USER, "iss": ISSUER, "aud": "authenticated",
                       "role": "authenticated", "iat": datetime.now(timezone.utc),
                       "exp": datetime.now(timezone.utc) + timedelta(minutes=5)},
                      BAD_KEY, algorithm="RS256")
    for token in (bogus, jwt.encode({"sub": USER}, key="", algorithm="none"), "broken"):
        with pytest.raises(AuthenticationError):
            verify(token)


def test_invalid_supabase_url_rejected():
    for origin in ("http://retail-test.supabase.co", "https://retail-test.supabase.co/evil",
                   "https://user:secret@retail-test.supabase.co"):
        with pytest.raises(ValueError):
            SupabaseJWTVerifier(origin, jwks_client=FakeJWKClient())
