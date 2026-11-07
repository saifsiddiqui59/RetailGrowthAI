"""Synthetic F3-08 HTTP adapter tests; not signed hosted E2E evidence."""
import sys
import unittest
from pathlib import Path
from uuid import uuid4

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "azure-functions" / "campaign-api"))
from feature3_private_png_http import private_png_http
from feature3_private_png_reader import PrivateGeneratedDownloadDenied
from tenant_store import StorageUnavailable


class Reader:
    def __init__(self, shop, job, *, fail=None, tamper=None):
        self.shop, self.job, self.fail, self.tamper = shop, job, fail, tamper
        self.calls = 0

    def read(self, **kwargs):
        self.calls += 1
        if self.fail:
            raise self.fail
        result = dict(shop_id=self.shop, job_id=self.job,
                      image_bytes=b"x" * 100, mime_type="image/png",
                      private=True, signed_url_issued=False)
        if self.tamper:
            result.update(self.tamper)
        return result


class HttpTests(unittest.TestCase):
    def setUp(self):
        self.shop, self.job = str(uuid4()), str(uuid4())
        self.reader = Reader(self.shop, self.job)
        self.factories = []

    def factory(self, shop, job):
        self.factories.append((shop, job))
        return self.reader

    def call(self, **overrides):
        values = dict(authorization="Bearer " + "t" * 30,
                      shop_id=self.shop, job_id=self.job,
                      reader_factory=self.factory)
        values.update(overrides)
        return private_png_http(**values)

    def test_binary_success_no_url_no_cache(self):
        reply = self.call()
        self.assertEqual(reply.status, 200)
        self.assertEqual(reply.body, b"x" * 100)
        self.assertEqual(reply.headers["Content-Type"], "image/png")
        self.assertEqual(reply.headers["Content-Length"], "100")
        self.assertIn("no-store", reply.headers["Cache-Control"])
        self.assertEqual(self.factories, [(self.shop, self.job)])

    def test_invalid_scope_and_credentials_never_construct_reader(self):
        for changes in (dict(shop_id=str(uuid4()).upper()),
                        dict(job_id="not-uuid"),
                        dict(authorization=""),
                        dict(authorization="Bearer sb_secret_badsecret"),
                        dict(authorization="Bearer " + "t" * 9000),
                        dict(authorization="Bearer t\nother"),
                        dict(authorization=object())):
            with self.subTest(changes=repr(changes)):
                self.assertNotEqual(self.call(**changes).status, 200)
        self.assertEqual(self.factories, [])

    def test_denials_and_outages_never_return_private_bytes(self):
        for error, status in ((PrivateGeneratedDownloadDenied("secret"), 404),
                              (StorageUnavailable("secret"), 503),
                              (OSError("secret"), 503),
                              (RuntimeError("secret"), 503)):
            with self.subTest(error=type(error).__name__):
                self.reader.fail = error
                reply = self.call()
                self.assertEqual(reply.status, status)
                self.assertEqual(reply.body, b"")
                self.assertNotIn("secret", repr(reply))

    def test_malformed_reader_result_is_denied(self):
        for tamper in (dict(shop_id=str(uuid4())),
                       dict(job_id=str(uuid4())),
                       dict(image_bytes="not bytes"),
                       dict(image_bytes=b"x"),
                       dict(private=False),
                       dict(signed_url_issued=True),
                       dict(mime_type="text/plain")):
            with self.subTest(tamper=repr(tamper)):
                self.reader.tamper = tamper
                reply = self.call()
                self.assertEqual(reply.status, 404)
                self.assertEqual(reply.body, b"")


if __name__ == "__main__":
    unittest.main()
