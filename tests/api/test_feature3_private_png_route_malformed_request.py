"""F3-08 synthetic malformed Azure request metadata regressions (not hosted auth)."""
import sys
import unittest
from pathlib import Path
from uuid import uuid4
from unittest.mock import patch
from types import SimpleNamespace

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

    def test_case_sensitive_header_adapter_passes_exact_enumerated_bearer(self):
        # A synthetic case-sensitive mapping is not an Azure hosted identity.
        for key in ("authorization", "AUTHORIZATION", "Authorization"):
            with self.subTest(key=key):
                request = Request()
                request.headers = {key: "Bearer synthetic-not-a-real-jwt"}
                calls = []
                def fake_private_png_http(**kwargs):
                    calls.append(kwargs)
                    return SimpleNamespace(
                        status=404, body=b"",
                        headers={"Cache-Control": "no-store, private"})
                with patch("feature3_private_png_route.private_png_http",
                           side_effect=fake_private_png_http):
                    response = handle_private_png_request(
                        request, reader_factory=lambda *args: None,
                        response_type=Response)
                self.assertEqual(response.status_code, 404)
                self.assertEqual(len(calls), 1)
                self.assertEqual(calls[0]["authorization"],
                                 "Bearer synthetic-not-a-real-jwt")
                self.assertEqual(calls[0]["shop_id"], request.route_params["shop_id"])
                self.assertEqual(calls[0]["job_id"], request.route_params["job_id"])

    def test_missing_or_nonstring_enumerated_authorization_is_denied(self):
        for headers in ({}, {"authorization": None},
                        {"AUTHORIZATION": ["Bearer synthetic"]},
                        {"authorization": ""}):
            with self.subTest(headers=headers):
                request = Request()
                request.headers = headers
                self.assert_denied_before_reader(request)

    def test_duplicate_case_variant_authorization_rejected_before_reader(self):
        class Faulty(Request):
            pass
        request = Faulty()
        request.headers = {
            "Authorization": "Bearer synthetic-not-a-real-jwt",
            "authorization": "Bearer synthetic-different-token",
        }
        self.assert_denied_before_reader(request)

    def test_header_enumeration_outage_denied_before_reader(self):
        class UnreadableKeys:
            def get(self, *args):
                return "Bearer synthetic-not-a-real-jwt"
            def keys(self):
                raise RuntimeError("synthetic header enumeration outage")
        class Faulty(Request):
            pass
        request = Faulty()
        request.headers = UnreadableKeys()
        self.assert_denied_before_reader(request)

    def test_nonstring_header_name_denied_before_reader(self):
        class Faulty(Request):
            pass
        request = Faulty()
        request.headers = {
            "Authorization": "Bearer synthetic-not-a-real-jwt",
            123: "untrusted",
        }
        self.assert_denied_before_reader(request)

    def test_backend_reader_failure_returns_opaque_no_store_503(self):
        # Synthetic failures stand in for a rights authority outage, not
        # proof of real JWT, tenant isolation or hosted Azure behavior.
        for failure in (RuntimeError("synthetic rights provider offline"),
                        PermissionError("synthetic private storage outage")):
            with self.subTest(failure=type(failure).__name__):
                calls = []
                def failing_reader(shop_id, job_id):
                    # Canonical adapter calls a scoped factory after UUID validation.
                    calls.append((shop_id, job_id))
                    raise failure
                response = handle_private_png_request(
                    Request(), reader_factory=failing_reader,
                    response_type=Response)
                self.assertEqual(response.status_code, 503)
                self.assertEqual(response.body, b"")
                self.assertEqual(response.headers["Content-Length"], "0")
                self.assertEqual(response.headers["Cache-Control"], "no-store, private")
                self.assertEqual(response.headers["X-Content-Type-Options"], "nosniff")
                self.assertEqual(calls, [(Request.route_params['shop_id'],
                                          Request.route_params['job_id'])])

    def test_ambiguous_get_framing_denied_before_reader(self):
        # Synthetic request smuggling boundary; no hosted proxy claims.
        cases = (
            {"Authorization": "Bearer synthetic-not-a-real-jwt",
             "Transfer-Encoding": "chunked"},
            {"Authorization": "Bearer synthetic-not-a-real-jwt",
             "Content-Length": "1"},
            {"Authorization": "Bearer synthetic-not-a-real-jwt",
             "Content-Length": "0", "content-length": "0"},
            {"Authorization": "Bearer synthetic-not-a-real-jwt",
             "Content-Length": 0},
        )
        for headers in cases:
            with self.subTest(headers=headers):
                request = Request()
                request.headers = headers
                self.assert_denied_before_reader(request)

    def test_empty_get_with_explicit_zero_length_preserves_auth_denial(self):
        request = Request()
        request.headers = {
            "Authorization": "Bearer synthetic-not-a-real-jwt",
            "Content-Length": "0",
        }
        response = handle_private_png_request(
            request, reader_factory=lambda *args: None,
            response_type=Response)
        # Valid framing reaches the canonical private handler, which must
        # reject the synthetic unverified reader without returning bytes.
        self.assertNotEqual(response.status_code, 400)
        self.assertEqual(response.body, b"")

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
