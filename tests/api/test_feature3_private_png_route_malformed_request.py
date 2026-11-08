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

    def test_noncanonical_route_scope_denied_before_reader(self):
        # Synthetic scopes must not invoke JWT, rights or storage adapters.
        shop = Request.route_params["shop_id"]
        job = Request.route_params["job_id"]
        class Spoof:
            def __eq__(self, other):
                return True
        for scope in (
            {"shop_id": shop.upper(), "job_id": job},
            {"shop_id": Spoof(), "job_id": job},
            {"shop_id": shop, "job_id": job + "/extra"},
            {"shop_id": shop, "job_id": None},
            {"shop_id": shop, "job_id": job.upper()},
        ):
            with self.subTest(scope=repr(scope)):
                request = Request()
                request.route_params = scope
                self.assert_denied_before_reader(request)

    def test_invalid_header_name_or_nonascii_value_denied(self):
        for name, value in (
            ("Bad Header", "safe"),
            ("X-Name:", "safe"),
            ("X-Name\\nInjected", "safe"),
            ("X-Nonascii", "caf\\u00e9"),
            ("X-Nonascii", "safe\\u0080"),
            ("X-Nonascii", "safe\\u2028"),
        ):
            with self.subTest(name=name, value=value):
                request = Request()
                request.headers = {
                    "Authorization": "Bearer synthetic-not-a-real-jwt",
                    name: value,
                }
                self.assert_denied_before_reader(request)

    def test_valid_header_token_and_canonical_scope_reach_adapter(self):
        request = Request()
        request.headers = {
            "authorization": "Bearer synthetic-not-a-real-jwt",
            "X-Correlation_Id": "synthetic-123",
        }
        with patch("feature3_private_png_route.private_png_http",
                   return_value=SimpleNamespace(status=404, body=b"",
                       headers={"Cache-Control": "no-store, private"})) as adapter:
            response = handle_private_png_request(
                request, reader_factory=lambda *args: None, response_type=Response)
        self.assertEqual(response.status_code, 404)
        adapter.assert_called_once()
        self.assertEqual(adapter.call_args.kwargs["shop_id"], request.route_params["shop_id"])
        self.assertEqual(adapter.call_args.kwargs["job_id"], request.route_params["job_id"])

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
                        {"AUTHORIZATION": ["Bearer synthetic"]}):
            with self.subTest(headers=headers):
                request = Request()
                request.headers = headers
                self.assert_denied_before_reader(request)

    def test_empty_bearer_is_401_without_backend_access(self):
        request = Request()
        request.headers = {"Authorization": ""}
        response = handle_private_png_request(
            request, reader_factory=lambda *args: self.fail("reader invoked"),
            response_type=Response)
        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.body, b"")
        self.assertEqual(response.headers["Content-Length"], "0")

    def test_header_injection_denied_before_backend(self):
        for token in ("Bearer synthetic" + chr(13) + chr(10) + "X-Admin: true",
                      "Bearer synthetic" + chr(10), "Bearer synthetic" + chr(13)):
            with self.subTest(token=repr(token)):
                request = Request()
                request.headers = {"Authorization": token}
                self.assert_denied_before_reader(request)

    def test_unrelated_header_control_characters_denied_before_reader(self):
        # Synthetic malformed adapter values cannot reach the rights provider.
        for value in ("safe\r\nInjected: yes", "nul\x00byte",
                      "tab\tbyte", "delete\x7fbyte"):
            with self.subTest(value=repr(value)):
                request = Request()
                request.headers = {
                    "Authorization": "Bearer synthetic-not-a-real-jwt",
                    "X-Untrusted": value,
                }
                self.assert_denied_before_reader(request)

    def test_header_metadata_limits_denied_before_reader(self):
        # Large untrusted headers must never trigger JWT/rights/storage IO.
        for headers in (
            {"Authorization": "Bearer synthetic", **{
                f"X-Demo-{i}": "fixture" for i in range(64)
            }},
            {"Authorization": "Bearer synthetic", "X-Large": "x" * 16384},
        ):
            with self.subTest(header_count=len(headers)):
                request = Request()
                request.headers = headers
                self.assert_denied_before_reader(request)

    def test_header_metadata_limit_boundary_passes_to_canonical_adapter(self):
        request = Request()
        request.headers = {"Authorization": "Bearer synthetic", "X-Large": "x" * 1000}
        with patch("feature3_private_png_route.private_png_http",
                   return_value=SimpleNamespace(status=404, body=b"",
                       headers={"Cache-Control": "no-store, private"})) as adapter:
            response = handle_private_png_request(
                request, reader_factory=lambda *args: None, response_type=Response)
        self.assertEqual(response.status_code, 404)
        adapter.assert_called_once()

    def test_unrelated_header_nonstring_denied_before_reader(self):
        for value in (None, ["synthetic"], 0):
            with self.subTest(value=repr(value)):
                request = Request()
                request.headers = {
                    "Authorization": "Bearer synthetic-not-a-real-jwt",
                    "X-Untrusted": value,
                }
                self.assert_denied_before_reader(request)

    def test_duplicate_case_folded_non_auth_headers_denied_before_reader(self):
        # Different framework adapters may choose first or last header value.
        # Reject ambiguous non-auth metadata before reaching the private reader.
        for pair in (
            ("X-Tenant", "x-tenant"),
            ("Content-Type", "content-type"),
            ("X-Request-Id", "X-REQUEST-ID"),
        ):
            with self.subTest(pair=pair):
                request = Request()
                request.headers = {
                    "Authorization": "Bearer synthetic-not-a-real-jwt",
                    pair[0]: "fixture-first",
                    pair[1]: "fixture-second",
                }
                self.assert_denied_before_reader(request)

    def test_distinct_header_names_remain_accepted(self):
        request = Request()
        request.headers = {
            "Authorization": "Bearer synthetic-not-a-real-jwt",
            "X-Request-Id": "synthetic-1",
            "X-Tenant-Hint": "untrusted-but-well-formed",
        }
        with patch("feature3_private_png_route.private_png_http",
                   return_value=SimpleNamespace(status=404, body=b"",
                       headers={"Cache-Control": "no-store, private"})) as adapter:
            response = handle_private_png_request(
                request, reader_factory=lambda *args: None,
                response_type=Response)
        self.assertEqual(response.status_code, 404)
        adapter.assert_called_once()

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
