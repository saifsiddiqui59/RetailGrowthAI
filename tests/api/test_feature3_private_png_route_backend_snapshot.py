"""F3-08 synthetic adversarial backend-envelope snapshot tests.

No real JWT, rights, hosted authorization, or customer imagery.
"""
import sys
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
from uuid import uuid4

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "azure-functions" / "campaign-api"))
from feature3_private_png_route import handle_private_png_request


class Response:
    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)


class Request:
    method = "GET"
    params = {}

    def __init__(self):
        self.route_params = {"shop_id": str(uuid4()), "job_id": str(uuid4())}
        self.headers = {"Authorization": "Bearer synthetic-not-a-real-jwt"}
        self.reads = 0

    def get_body(self):
        self.reads += 1
        return b""


class ChangingEnvelope:
    def __init__(self, first, second):
        self.first = first
        self.second = second
        self.body_reads = 0

    @property
    def status(self):
        return 200

    @property
    def body(self):
        self.body_reads += 1
        return self.first if self.body_reads == 1 else self.second

    @property
    def headers(self):
        return {}


class BackendSnapshotTests(unittest.TestCase):
    def test_backend_body_read_once_even_when_stateful(self):
        request = Request()
        envelope = ChangingEnvelope(b"not-a-png", b"synthetic-private-leak")
        with patch("feature3_private_png_route.private_png_http", return_value=envelope):
            response = handle_private_png_request(
                request, reader_factory=lambda *args: None, response_type=Response)
        self.assertEqual(request.reads, 1)
        self.assertEqual(envelope.body_reads, 1)
        self.assertEqual(response.status_code, 503)
        self.assertEqual(response.body, b"")
        self.assertNotIn(b"synthetic-private-leak", response.body)

    def test_hostile_envelope_property_raises_fail_closed(self):
        request = Request()

        class ExplodingEnvelope:
            status = 200
            body = b"synthetic"
            @property
            def headers(self):
                raise RuntimeError("synthetic secret")

        with patch("feature3_private_png_route.private_png_http", return_value=ExplodingEnvelope()):
            response = handle_private_png_request(
                request, reader_factory=lambda *args: None, response_type=Response)
        self.assertEqual(response.status_code, 503)
        self.assertEqual(response.body, b"")

    def test_malformed_snapshot_never_releases_bytes(self):
        request = Request()
        with patch("feature3_private_png_route.private_png_http", return_value=SimpleNamespace(
                status=200, body=b"synthetic-private-data", headers={})):
            response = handle_private_png_request(
                request, reader_factory=lambda *args: None, response_type=Response)
        self.assertEqual(response.status_code, 503)
        self.assertEqual(response.body, b"")


if __name__ == "__main__":
    unittest.main()
