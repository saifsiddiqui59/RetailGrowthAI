"""F3-08 synthetic bounded header enumeration regressions.

No hosted identity, real asset rights or production services are involved.
"""
import sys
import unittest
from pathlib import Path
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

    def __init__(self, headers):
        self.headers = headers
        self.route_params = {"shop_id": str(uuid4()), "job_id": str(uuid4())}
        self.body_reads = 0

    def get_body(self):
        self.body_reads += 1
        return b""


class BoundedHeaders:
    def __init__(self):
        self.yielded = 0
        self.lookups = 0

    def keys(self):
        # Deliberately large, but finite: fail if the route eagerly enumerates.
        for i in range(100000):
            self.yielded += 1
            if self.yielded > 65:
                raise AssertionError("unbounded request-header enumeration")
            yield f"X-Synthetic-{i}"

    def get(self, key):
        self.lookups += 1
        raise AssertionError("header values must not be read after overflow")


class HeaderEnumerationTests(unittest.TestCase):
    def test_large_header_iterator_rejected_before_value_or_body_io(self):
        headers = BoundedHeaders()
        request = Request(headers)
        with patch("feature3_private_png_route.private_png_http") as backend:
            response = handle_private_png_request(
                request, reader_factory=lambda *args: None,
                response_type=Response)
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.body, b"")
        self.assertEqual(response.headers["Cache-Control"], "no-store, private")
        self.assertEqual(headers.yielded, 65)
        self.assertEqual(headers.lookups, 0)
        self.assertEqual(request.body_reads, 0)
        backend.assert_not_called()


if __name__ == "__main__":
    unittest.main()
