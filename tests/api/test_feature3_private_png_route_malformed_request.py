"""F3-08 synthetic malformed Azure request metadata regressions (not hosted auth)."""
import sys
import unittest
from pathlib import Path
from uuid import uuid4

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "azure-functions" / "campaign-api"))
from feature3_private_png_route import handle_private_png_request


class Response:
    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)


class Request:
    method = "GET"
    route_params = {"shop_id": str(uuid4()), "job_id": str(uuid4())}
    headers = {"Authorization": "Bearer synthetic-not-a-real-jwt"}
    params = {}

    def get_body(self):
        return b""


class Broken:
    def __getattr__(self, name):
        raise RuntimeError("synthetic request adapter outage")


class BrokenHeader:
    def get(self, *args):
        raise RuntimeError("synthetic header adapter outage")


class NonStringHeader:
    def get(self, *args):
        return ["Bearer", "synthetic"]


class Tests(unittest.TestCase):
    def assert_denied_before_reader(self, request):
        invoked = []
        def reader():
            invoked.append(True)
            raise AssertionError("private reader must not run")
        response = handle_private_png_request(
            request, reader_factory=reader, response_type=Response)
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.body, b"")
        self.assertEqual(response.headers["Cache-Control"], "no-store, private")
        self.assertEqual(invoked, [])

    def test_unreadable_request_metadata_denied(self):
        self.assert_denied_before_reader(Broken())
        for field in ("route_params", "headers", "params", "get_body"):
            class Faulty(Request):
                def __getattribute__(self, name):
                    if name == field:
                        raise RuntimeError("synthetic metadata outage")
                    return super().__getattribute__(name)
            with self.subTest(field=field):
                self.assert_denied_before_reader(Faulty())

    def test_unreadable_or_nonstring_authorization_denied(self):
        for headers in (BrokenHeader(), NonStringHeader()):
            class Faulty(Request):
                pass
            request = Faulty()
            request.headers = headers
            with self.subTest(headers=type(headers).__name__):
                self.assert_denied_before_reader(request)


if __name__ == "__main__":
    unittest.main()
