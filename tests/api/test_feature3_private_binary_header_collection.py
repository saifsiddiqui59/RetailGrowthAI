"""F3-08: malformed HTTP header collections must never create rights readers.

All identities here are synthetic. These tests do not establish hosted JWT/RLS.
"""
import sys
import unittest
from pathlib import Path
from uuid import uuid4

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "azure-functions" / "campaign-api"))
from feature3_private_binary_route import private_png_response


class Request:
    method = "GET"
    def __init__(self, headers):
        self.headers = headers


class HeaderCollectionTests(unittest.TestCase):
    def setUp(self):
        self.shop, self.job = str(uuid4()), str(uuid4())
        self.created = []

    def invoke(self, headers):
        return private_png_response(
            Request(headers), shop_id=self.shop, job_id=self.job,
            enabled=True, reader_factory=lambda: self.created.append("reader"))

    def test_malformed_fields_are_denied_before_reader_construction(self):
        valid = ("Authorization", "Bearer synthetic-fixture-token")
        malformed = [
            [valid, (b"Authorization", "Bearer another-token")],
            [valid, (None, "Bearer another-token")],
            [valid, ("X-Other", b"non-string")],
            [valid, (123, "untrusted")],
            [valid, ("Authorization", ["Bearer duplicate"])],
            [valid, ("X-Other", None)],
        ]
        for fields in malformed:
            with self.subTest(fields=fields):
                code, body, response_headers = self.invoke(dict(fields))
                self.assertEqual((code, body), (401, b""))
                self.assertEqual(response_headers["Cache-Control"],
                                 "no-store, private, max-age=0")
                self.assertNotIn("Location", response_headers)
        self.assertEqual(self.created, [])

    def test_valid_preflight_reaches_factory_but_never_grants_without_reader(self):
        # A factory returning None is NOT authorization; the HTTP adapter
        # must still deny rather than returning any private bytes.
        status, body, headers = self.invoke(
            {"Authorization": "Bearer synthetic-fixture-token", "X-Test": "ok"})
        self.assertEqual(status, 503)
        self.assertEqual(body, b"")
        self.assertEqual(self.created, ["reader"])
        self.assertNotIn("Location", headers)


if __name__ == "__main__":
    unittest.main()
