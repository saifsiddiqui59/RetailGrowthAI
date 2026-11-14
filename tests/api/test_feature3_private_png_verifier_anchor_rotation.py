"""F3-08 synthetic-only regression: rotating JWT trust anchors deny private bytes."""
import sys
import unittest
from pathlib import Path
from unittest.mock import patch
from uuid import uuid4

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "azure-functions" / "campaign-api"))
from feature3_private_png_runtime import build_private_png_reader_factory
from feature3_private_png_reader import PrivateGeneratedDownloadDenied

ORIGIN = "https://synthetic-dev-project.supabase.co"
KEY = "sb_publishable_synthetic_test_only_12345"


class Store:
    origin = ORIGIN
    key = KEY


class Client:
    def __init__(self, uri):
        self.uri = uri


class Verifier:
    def __init__(self, *, rotate_client=False, rotate_uri=False):
        self.issuer = ORIGIN + "/auth/v1"
        self.good = Client(ORIGIN + "/auth/v1/.well-known/jwks.json")
        self.bad = Client("https://foreign-project.supabase.co/auth/v1/.well-known/jwks.json")
        self.rotate_client = rotate_client
        self.rotate_uri = rotate_uri
        self.reads = 0

    @property
    def client(self):
        self.reads += 1
        if self.rotate_client and self.reads % 2 == 0:
            return self.bad
        if self.rotate_uri and self.reads % 2 == 0:
            self.good.uri = "https://foreign-project.supabase.co/auth/v1/.well-known/jwks.json"
        return self.good

    def __call__(self, token):
        raise AssertionError("untrusted JWT verifier must not run")


class CountingReader:
    calls = 0

    def __init__(self, **kwargs):
        pass

    def read(self, **kwargs):
        self.__class__.calls += 1
        return b"synthetic-only"


class StableTrustAnchorTests(unittest.TestCase):
    def build(self, verifier):
        return build_private_png_reader_factory(
            supabase_origin=ORIGIN, publishable_key=KEY,
            authoritative_rights_read=lambda *args: None,
            jwt_verifier=verifier, tenant_store=Store())

    def test_rotating_client_is_denied_before_reader_construction(self):
        CountingReader.calls = 0
        with patch("feature3_private_png_runtime.SupabaseJWTVerifier", Verifier), patch(
                "feature3_private_png_runtime.Feature3RevocablePNGReader", CountingReader):
            verifier = Verifier()
            factory = self.build(verifier)
            verifier.rotate_client = True
            with self.assertRaises(ValueError):
                factory(str(uuid4()), str(uuid4()))
        self.assertEqual(CountingReader.calls, 0)

    def test_rotating_uri_is_denied_before_private_byte_read(self):
        CountingReader.calls = 0
        with patch("feature3_private_png_runtime.SupabaseJWTVerifier", Verifier), patch(
                "feature3_private_png_runtime.Feature3RevocablePNGReader", CountingReader):
            verifier = Verifier()
            shop, job = str(uuid4()), str(uuid4())
            scoped = self.build(verifier)(shop, job)
            verifier.rotate_uri = True
            with self.assertRaises(PrivateGeneratedDownloadDenied):
                scoped.read(user_token="synthetic-test-token", shop_id=shop, job_id=job)
        self.assertEqual(CountingReader.calls, 0)


if __name__ == "__main__":
    unittest.main()
