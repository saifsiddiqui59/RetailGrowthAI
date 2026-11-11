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

    def test_oversized_backend_png_denied_before_azure_response(self):
        # Synthetic malformed provider response: no hosted authorization.
        # A matching length header must not permit an unbounded allocation.
        png_like = bytes.fromhex("89504e470d0a1a0a") + b"x" * (64 * 1024 * 1024)
        with patch("feature3_private_png_route.private_png_http",
                   return_value=SimpleNamespace(
                       status=200, body=png_like,
                       headers={"Content-Type": "image/png",
                                "Cache-Control": "no-store, private",
                                "Content-Length": str(len(png_like))})):
            response = handle_private_png_request(
                Request(), reader_factory=lambda *args: None,
                response_type=Response)
        self.assertEqual(response.status_code, 503)
        self.assertEqual(response.body, b"")
        self.assertEqual(response.headers["Content-Length"], "0")

    def test_backend_png_above_canonical_reader_limit_denied(self):
        # A synthetic compromised backend must not bypass the reader's
        # 25 MiB cap by returning a self-consistent Content-Length.
        png_like = bytes.fromhex("89504e470d0a1a0a") + b"x" * (25 * 1024 * 1024)
        with patch("feature3_private_png_route.private_png_http",
                   return_value=SimpleNamespace(
                       status=200, body=png_like,
                       headers={"Content-Type": "image/png",
                                "Cache-Control": "no-store, private",
                                "Content-Length": str(len(png_like))})):
            response = handle_private_png_request(
                Request(), reader_factory=lambda *args: None,
                response_type=Response)
        self.assertEqual(response.status_code, 503)
        self.assertEqual(response.body, b"")
        self.assertEqual(response.headers["Content-Length"], "0")

    def test_private_png_backend_transformation_and_duplicate_headers_denied(self):
        # Synthetic compromised backend fixtures; no hosted authorization.
        png_like = bytes.fromhex("89504e470d0a1a0a") + b"synthetic"
        base = {"Content-Type": "image/png",
                "Cache-Control": "no-store, private",
                "Content-Length": str(len(png_like))}
        mutations = (
            {"Content-Encoding": "gzip"},
            {"Transfer-Encoding": "chunked"},
            {"Content-Range": "bytes 0-9/10"},
            {"Set-Cookie": "session=synthetic"},
            {"Location": "https://example.invalid/fixture"},
            {"ETag": "synthetic"},
            {"Last-Modified": "Mon, 01 Jan 2024 00:00:00 GMT"},
            {"content-type": "image/png"},
            {"cache-control": "no-store, private"},
            {"Content-Length\\nInjected": "1"},
        )
        for mutation in mutations:
            with self.subTest(mutation=mutation):
                with patch("feature3_private_png_route.private_png_http",
                           return_value=SimpleNamespace(
                               status=200, body=png_like,
                               headers={**base, **mutation})):
                    response = handle_private_png_request(
                        Request(), reader_factory=lambda *args: None,
                        response_type=Response)
                self.assertEqual(response.status_code, 503)
                self.assertEqual(response.body, b"")
                self.assertEqual(response.headers["Content-Length"], "0")

    def test_private_png_receipt_length_mismatch_fails_closed(self):
        # Synthetic backend replies are not proof of signed hosted access.
        # Even a PNG-looking body must not escape if the trusted adapter
        # reports a missing, inconsistent or noncanonical byte count.
        png_like = bytes.fromhex("89504e470d0a1a0a") + b"synthetic"
        for declared in (None, "0", str(len(png_like) + 1),
                         "0" + str(len(png_like)), len(png_like)):
            with self.subTest(declared=declared):
                request = Request()
                headers = {"Content-Type": "image/png",
                           "Cache-Control": "no-store, private"}
                if declared is not None:
                    headers["Content-Length"] = declared
                with patch("feature3_private_png_route.private_png_http",
                           return_value=SimpleNamespace(
                               status=200, body=png_like, headers=headers)):
                    response = handle_private_png_request(
                        request, reader_factory=lambda *args: None,
                        response_type=Response)
                self.assertEqual(response.status_code, 503)
                self.assertEqual(response.body, b"")
                self.assertEqual(response.headers["Content-Length"], "0")

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

    def test_proxy_rewrite_and_forwarded_authority_denied_before_reader(self):
        # Proxy assertions must never override the signed user or canonical
        # route scope. These are synthetic metadata, not hosted auth tests.
        for name, value in (
            ("Forwarded", "for=192.0.2.1;host=other.example"),
            ("X-Forwarded-Host", "other.example"),
            ("X-Forwarded-Uri", "/shops/foreign/feature3-private-png/other"),
            ("X-Forwarded-Prefix", "/admin"),
            ("X-Original-URL", "/admin"),
            ("X-Rewrite-URL", "/shops/foreign"),
            ("X-Original-Uri", "/shops/foreign"),
            ("X-Envoy-Original-Path", "/shops/foreign"),
            ("X-MS-Original-URL", "/shops/foreign"),
            ("X-MS-Original-Host", "other.example"),
        ):
            with self.subTest(header=name):
                request = Request()
                request.headers = {
                    "Authorization": "Bearer synthetic-not-a-real-jwt",
                    name: value,
                }
                self.assert_denied_before_reader(request)

    def test_invalid_header_name_or_nonascii_value_denied(self):
        for name, value in (
            ("Bad Header", "safe"),
            ("X-Name:", "safe"),
            ("X-Name" + chr(10) + "Injected", "safe"),
            ("X-Nonascii", "caf" + chr(0xe9)),
            ("X-Nonascii", "safe" + chr(0x80)),
            ("X-Nonascii", "safe" + chr(0x2028)),
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

    def test_oversized_bearer_denied_before_body_and_rights(self):
        # Synthetic credential only. A huge bearer cannot force body IO.
        request = Request()
        request.headers = {"Authorization": "Bearer " + "x" * 8194}
        body_calls = []
        def read_body():
            body_calls.append(True)
            raise AssertionError("body should not be materialized")
        request.get_body = read_body
        response = handle_private_png_request(
            request, reader_factory=lambda *args: self.fail("rights reader invoked"),
            response_type=Response)
        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.body, b"")
        self.assertEqual(body_calls, [])

    def test_invalid_bearer_shape_denied_before_body_and_rights(self):
        # Synthetic malformed credentials are never hosted authorization.
        for credential in (
            "Basic synthetic-not-a-jwt",
            "bearer synthetic-not-a-jwt",
            "Bearer ",
            "Bearer sb_secret_" + "x" * 24,
            "Bearer sb_publishable_" + "x" * 24,
            "Bearer token" + chr(127) + "invalid",
        ):
            with self.subTest(credential=repr(credential)):
                request = Request()
                request.headers = {"Authorization": credential}
                reads = []
                request.get_body = lambda: reads.append(True) or b""
                response = handle_private_png_request(
                    request,
                    reader_factory=lambda *args: self.fail("rights invoked"),
                    response_type=Response,
                )
                self.assertEqual(response.status_code, 401)
                self.assertEqual(response.body, b"")
                self.assertEqual(reads, [])

    def test_valid_bearer_shape_reaches_canonical_reader(self):
        request = Request()
        reads = []
        request.get_body = lambda: reads.append(True) or b""
        with patch("feature3_private_png_route.private_png_http",
                   return_value=SimpleNamespace(status=404, body=b"",
                       headers={"Cache-Control": "no-store, private"})) as adapter:
            response = handle_private_png_request(
                request, reader_factory=lambda *args: None,
                response_type=Response)
        self.assertEqual(response.status_code, 404)
        self.assertEqual(reads, [True])
        adapter.assert_called_once()

    def test_header_injection_denied_before_backend(self):
        for token in ("Bearer synthetic" + chr(13) + chr(10) + "X-Admin: true",
                      "Bearer synthetic" + chr(10), "Bearer synthetic" + chr(13)):
            with self.subTest(token=repr(token)):
                request = Request()
                request.headers = {"Authorization": token}
                self.assert_denied_before_reader(request)

    def test_unrelated_header_control_characters_denied_before_reader(self):
        # Synthetic malformed adapter values cannot reach the rights provider.
        for value in ("safe" + chr(13) + chr(10) + "Injected: yes",
                      "nul" + chr(0) + "byte", "tab" + chr(9) + "byte",
                      "delete" + chr(127) + "byte"):
            with self.subTest(value=repr(value)):
                request = Request()
                request.headers = {
                    "Authorization": "Bearer synthetic-not-a-real-jwt",
                    "X-Untrusted": value,
                }
                self.assert_denied_before_reader(request)

    def test_compressed_private_png_negotiation_denied_before_body_or_reader(self):
        # Synthetic transport fixtures: compressed responses would invalidate
        # the exact private PNG byte/digest contract.
        for encoding in ("gzip", "br", "*", "gzip, identity", "identity;q=0",
                         "", "deflate"):
            with self.subTest(encoding=encoding):
                request = Request()
                request.headers = {
                    "Authorization": "Bearer synthetic-not-a-real-jwt",
                    "Accept-Encoding": encoding,
                }
                body_reads = []
                request.get_body = lambda: body_reads.append(True) or b""
                self.assert_denied_before_reader(request)
                self.assertEqual(body_reads, [])

    def test_incompatible_accept_rejected_before_body_or_rights(self):
        # Synthetic transport-only fixtures; no hosted JWT or rights claim.
        for value in ("application/json", "text/html", "image/jpeg",
                      "image/png;q=0", "", "image/png, text/html"):
            with self.subTest(accept=value):
                request = Request()
                request.headers = {
                    "Authorization": "Bearer synthetic-not-a-real-jwt",
                    "Accept": value,
                }
                reads = []
                request.get_body = lambda: reads.append(True) or b""
                response = handle_private_png_request(
                    request, reader_factory=lambda *args: self.fail(
                        "private rights reader invoked"), response_type=Response)
                self.assertEqual(response.status_code, 406)
                self.assertEqual(response.body, b"")
                self.assertEqual(response.headers["Cache-Control"], "no-store, private")
                self.assertEqual(reads, [])

    def test_supported_accept_reaches_canonical_adapter(self):
        for value in ("image/png", "image/*", "*/*"):
            with self.subTest(accept=value):
                request = Request()
                request.headers = {
                    "Authorization": "Bearer synthetic-not-a-real-jwt",
                    "Accept": value,
                }
                with patch("feature3_private_png_route.private_png_http",
                           return_value=SimpleNamespace(
                               status=404, body=b"",
                               headers={"Cache-Control": "no-store, private"})) as adapter:
                    response = handle_private_png_request(
                        request, reader_factory=lambda *args: None,
                        response_type=Response)
                self.assertEqual(response.status_code, 404)
                adapter.assert_called_once()

    def test_explicit_identity_encoding_reaches_binary_adapter(self):
        request = Request()
        request.headers = {
            "Authorization": "Bearer synthetic-not-a-real-jwt",
            "aCcEpT-EnCoDiNg": "IDENTITY",
        }
        with patch("feature3_private_png_route.private_png_http",
                   return_value=SimpleNamespace(status=404, body=b"",
                       headers={"Cache-Control": "no-store, private"})) as adapter:
            response = handle_private_png_request(
                request, reader_factory=lambda *args: None,
                response_type=Response)
        self.assertEqual(response.status_code, 404)
        adapter.assert_called_once()

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

    def test_header_count_exact_boundary_reaches_canonical_adapter(self):
        # Exactly 64 distinct headers (including Authorization) are allowed.
        request = Request()
        request.headers = {"Authorization": "Bearer synthetic", **{
            f"X-Demo-{i}": "fixture" for i in range(63)
        }}
        with patch("feature3_private_png_route.private_png_http",
                   return_value=SimpleNamespace(
                       status=404, body=b"",
                       headers={"Cache-Control": "no-store, private"})) as adapter:
            response = handle_private_png_request(
                request, reader_factory=lambda *args: None,
                response_type=Response)
        self.assertEqual(response.status_code, 404)
        adapter.assert_called_once()

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

    def test_partial_conditional_and_proxy_headers_denied_before_body(self):
        # Synthetic requests: no byte ranges, stale validators, proxy auth,
        # compression or upgrade semantics on private full-image downloads.
        for header, value in (
            ("Range", "bytes=0-99"),
            ("If-Range", "synthetic-etag"),
            ("If-None-Match", "synthetic-etag"),
            ("If-Modified-Since", "Mon, 01 Jan 2024 00:00:00 GMT"),
            ("If-Match", "*"),
            ("If-Unmodified-Since", "Mon, 01 Jan 2024 00:00:00 GMT"),
            ("Content-Encoding", "gzip"),
            ("Expect", "100-continue"),
            ("Upgrade", "websocket"),
            ("Proxy-Authorization", "Basic synthetic"),
        ):
            with self.subTest(header=header):
                request = Request()
                request.headers = {"Authorization": "Bearer synthetic",
                                   header: value}
                body_reads = []
                request.get_body = lambda: body_reads.append(True)
                with patch("feature3_private_png_route.private_png_http") as backend:
                    self.assert_denied_before_reader(request)
                self.assertEqual(body_reads, [])
                backend.assert_not_called()

    def test_hop_by_hop_and_method_override_headers_fail_closed(self):
        # Synthetic requests only: reject proxy-controlled routing and
        # method tunnelling before body, JWT, rights or Storage access.
        for name, value in (
            ("Connection", "keep-alive"),
            ("Keep-Alive", "timeout=5"),
            ("TE", "trailers"),
            ("Trailer", "Authorization"),
            ("Proxy-Connection", "keep-alive"),
            ("Proxy-Authenticate", "Basic realm=fixture"),
            ("X-HTTP-Method-Override", "POST"),
            ("X-Method-Override", "DELETE"),
            ("X-Original-Method", "PATCH"),
        ):
            with self.subTest(name=name):
                request = Request()
                request.headers = {
                    "Authorization": "Bearer synthetic-not-a-real-jwt",
                    name: value,
                }
                body_reads = []
                request.get_body = lambda: body_reads.append(True) or b""
                with patch("feature3_private_png_route.private_png_http") as backend:
                    response = handle_private_png_request(
                        request, reader_factory=lambda *args: self.fail(
                            "rights reader must not be invoked"),
                        response_type=Response)
                self.assertEqual(response.status_code, 400)
                self.assertEqual(response.body, b"")
                self.assertEqual(response.headers["Cache-Control"], "no-store, private")
                self.assertEqual(body_reads, [])
                backend.assert_not_called()

    def test_regular_accept_header_remains_compatible(self):
        request = Request()
        request.headers = {"Authorization": "Bearer synthetic",
                           "Accept": "image/png"}
        with patch("feature3_private_png_route.private_png_http",
                   return_value=SimpleNamespace(status=404, body=b"",
                       headers={"Cache-Control": "no-store, private"})) as backend:
            reply = handle_private_png_request(
                request, reader_factory=lambda *args: None,
                response_type=Response)
        self.assertEqual(reply.status_code, 404)
        backend.assert_called_once()

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

    def test_malformed_headers_do_not_materialize_get_body(self):
        # Synthetic request adapter: a large body should not be read before
        # inexpensive, bounded header validation rejects an invalid request.
        for headers in (
            {"Authorization": "Bearer synthetic", "Transfer-Encoding": "chunked"},
            {"Authorization": "Bearer synthetic", "X-Large": "x" * 16384},
            {"Authorization": "Bearer synthetic", "X-Bad": "nul" + chr(0)},
            {"Authorization": "Bearer synthetic", "Content-Length": "1000000000"},
        ):
            with self.subTest(headers=list(headers)):
                request = Request()
                request.headers = headers
                body_reads = []
                def forbidden_body_read():
                    body_reads.append(True)
                    raise AssertionError("malformed headers must not read body")
                request.get_body = forbidden_body_read
                self.assert_denied_before_reader(request)
                self.assertEqual(body_reads, [])

    def test_proxy_and_method_override_headers_rejected_before_body_io(self):
        # Regression for the complete fail-closed header set. These are
        # synthetic requests; no real JWT or hosted rights are asserted.
        for name in ("Proxy-Authenticate", "TE", "Trailer", "Connection",
                     "Keep-Alive", "Proxy-Connection",
                     "X-HTTP-Method-Override", "X-Method-Override",
                     "X-Original-Method"):
            with self.subTest(header=name):
                request = Request()
                request.headers = {
                    "Authorization": "Bearer synthetic-not-a-real-jwt",
                    name: "synthetic",
                }
                reads = []
                request.get_body = lambda: reads.append(True) or b""
                self.assert_denied_before_reader(request)
                self.assertEqual(reads, [])

    def test_valid_headers_still_check_get_body(self):
        request = Request()
        body_reads = []
        def nonempty_body():
            body_reads.append(True)
            return b"synthetic forbidden GET body"
        request.get_body = nonempty_body
        self.assert_denied_before_reader(request)
        self.assertEqual(body_reads, [True])

    def test_downstream_response_contract_fails_closed(self):
        # Synthetic backend faults are not evidence of hosted authentication.
        for status, body, headers in (
            (200, b"not-png", {"Content-Type": "image/png",
                              "Cache-Control": "no-store, private"}),
            (200, bytes.fromhex("89504e470d0a1a0a"),
             {"Content-Type": "text/html", "Cache-Control": "no-store, private"}),
            (404, b"partial-private-image", {}),
            (302, b"", {"Location": "https://untrusted.invalid"}),
            (True, b"", {}),
            (200, "not-bytes", {}),
            (200, b"", []),
        ):
            with self.subTest(status=status, body=repr(body)):
                with patch("feature3_private_png_route.private_png_http",
                           return_value=SimpleNamespace(
                               status=status, body=body, headers=headers)):
                    response = handle_private_png_request(
                        Request(), reader_factory=lambda *args: None,
                        response_type=Response)
                self.assertEqual(response.status_code, 503)
                self.assertEqual(response.body, b"")
                self.assertNotIn("Location", response.headers)

    def test_canonical_strict_no_cache_policy_is_accepted_without_leaking_headers(self):
        # Actual Feature3PrivateBinaryHTTP returns this exact header; a
        # disagreement between the two adapters previously made every
        # valid private PNG download return opaque HTTP 503.
        png = bytes.fromhex("89504e470d0a1a0a") + b"synthetic"
        reply = SimpleNamespace(
            status=200, body=png,
            headers={"Content-Type": "image/png",
                     "Cache-Control": "no-store, private, max-age=0",
                     "Content-Length": str(len(png)),
                     "X-Feature3-Image-Sha256": "sensitive-not-for-browser",
                     "Set-Cookie": "private-credential"})
        with patch("feature3_private_png_route.private_png_http",
                   return_value=reply):
            response = handle_private_png_request(
                Request(), reader_factory=lambda *args: None,
                response_type=Response)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.body, png)
        self.assertEqual(response.headers["Cache-Control"], "no-store, private")
        self.assertNotIn("Set-Cookie", response.headers)
        self.assertNotIn("X-Feature3-Image-Sha256", response.headers)

    def test_public_or_equality_spoofed_cache_policy_is_denied(self):
        class PretendPrivate:
            def __eq__(self, other):
                return True
        png = bytes.fromhex("89504e470d0a1a0a") + b"synthetic"
        for policy in ("public, max-age=3600", "private, max-age=3600",
                       "no-cache", PretendPrivate(), None):
            with self.subTest(policy=repr(policy)):
                with patch("feature3_private_png_route.private_png_http",
                           return_value=SimpleNamespace(
                               status=200, body=png,
                               headers={"Content-Type": "image/png",
                                        "Cache-Control": policy})):
                    response = handle_private_png_request(
                        Request(), reader_factory=lambda *args: None,
                        response_type=Response)
                self.assertEqual(response.status_code, 503)
                self.assertEqual(response.body, b"")
                self.assertEqual(response.headers["Content-Length"], "0")

    def test_valid_png_reply_strips_untrusted_backend_headers(self):
        # This only tests the Azure adapter; full PNG validation lives inside
        # the independently tested canonical binary handler.
        png = bytes.fromhex("89504e470d0a1a0a") + b"synthetic"
        with patch("feature3_private_png_route.private_png_http",
                   return_value=SimpleNamespace(
                       status=200, body=png,
                       headers={"Content-Type": "image/png",
                                "Cache-Control": "no-store, private",
                                "Content-Length": str(len(png)),
                                "Set-Cookie": "untrusted=1",
                                "Location": "https://untrusted.invalid"})):
            response = handle_private_png_request(
                Request(), reader_factory=lambda *args: None,
                response_type=Response)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.body, png)
        self.assertEqual(response.headers["Content-Length"], str(len(png)))
        self.assertNotIn("Set-Cookie", response.headers)
        self.assertNotIn("Location", response.headers)

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


    def test_proxy_identity_assertions_denied_before_reader(self):
        # Synthetic proxy headers must never substitute for signed user JWT.
        # No private factory, rights lookup or Storage reader may run.
        for header in (
            "X-Forwarded-User", "X-Forwarded-Email",
            "X-Forwarded-Groups", "X-Remote-User",
            "X-Authenticated-User", "X-Authenticated-Email",
            "X-MS-CLIENT-PRINCIPAL", "X-MS-CLIENT-PRINCIPAL-ID",
            "X-MS-CLIENT-PRINCIPAL-NAME",
            "X-MS-CLIENT-PRINCIPAL-IDP",
            "X-Goog-Authenticated-User-Email",
            "X-Goog-Authenticated-User-ID",
            "CF-Access-Authenticated-User-Email",
            "X-Amzn-Oidc-Identity", "X-Amzn-Oidc-Data",
            "X-Amzn-Oidc-Accesstoken",
        ):
            with self.subTest(header=header):
                request = Request()
                request.headers = dict(request.headers)
                request.headers[header] = "synthetic-untrusted-identity"
                self.assert_denied_before_reader(request)


if __name__ == "__main__":
    unittest.main()
