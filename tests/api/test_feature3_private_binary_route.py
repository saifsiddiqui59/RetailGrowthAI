"""F3-08 Azure boundary: synthetic two-shop denial, fail-closed injection."""
import sys
import unittest
from pathlib import Path
from uuid import uuid4

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "azure-functions" / "campaign-api"))
from feature3_private_binary_route import private_png_response
from feature3_private_png_reader import PrivateGeneratedDownloadDenied
from test_feature3_private_binary_http import AuthorizedReader


class Request:
    method = "GET"
    headers = {"Authorization": "Bearer signed-retailer-test"}


class RouteTests(unittest.TestCase):
    def setUp(self):
        self.shop, self.job = str(uuid4()), str(uuid4())
        self.reader = AuthorizedReader(self.shop, self.job)

    def invoke(self, factory=None, enabled=True, shop=None, job=None):
        return private_png_response(
            Request(), shop_id=shop or self.shop, job_id=job or self.job,
            reader_factory=factory, enabled=enabled)

    def test_disabled_or_unconfigured_never_reads_private_bytes(self):
        for enabled, factory, expected in (
            (False, lambda: self.reader, 404),
            (True, None, 503),
            (True, lambda: (_ for _ in ()).throw(RuntimeError("secret")), 503),
            (True, lambda: object(), 503),
        ):
            code, body, headers = self.invoke(factory, enabled)
            self.assertEqual((code, body), (expected, b""))
            self.assertEqual(headers["Cache-Control"], "no-store, private, max-age=0")
        self.assertEqual(self.reader.calls, [])

    def test_mock_current_rights_allow_and_foreign_tenant_denial(self):
        code, data, headers = self.invoke(lambda: self.reader)
        self.assertEqual(code, 200)
        self.assertEqual(data, self.reader.png)
        self.assertNotIn("Location", headers)
        self.assertNotIn("Access-Control-Allow-Origin", headers)
        # The actual reader is required to deny foreign shop; this mock
        # intentionally simulates a current-rights failure, NOT hosted RLS.
        self.reader.fail = PrivateGeneratedDownloadDenied("foreign shop")
        code, data, headers = self.invoke(lambda: self.reader, shop=str(uuid4()))
        self.assertEqual((code, data), (404, b""))
        self.assertNotIn("object_path", str(headers).lower())

    def test_revoked_and_reader_outage_never_fall_back(self):
        self.reader.fail = PrivateGeneratedDownloadDenied("revoked")
        self.assertEqual(self.invoke(lambda: self.reader)[:2], (404, b""))
        self.reader.fail = TimeoutError("backend unavailable")
        self.assertEqual(self.invoke(lambda: self.reader)[:2], (503, b""))
        self.reader.fail = None
        self.assertEqual(self.invoke(lambda: self.reader)[0], 200)

    def test_preflight_denies_without_constructing_reader(self):
        calls = []
        def factory():
            calls.append("constructed")
            return self.reader
        for method, auth, expected in (
            ("POST", "Bearer signed-retailer-test", 405),
            ("HEAD", "Bearer signed-retailer-test", 405),
            ("GET", "", 401),
            ("GET", "Bearer sb_publishable_fixture", 401),
            ("GET", "Bearer bad" + chr(13) + chr(10) + "Injected", 401),
            ("GET", "Bearer unicode-" + chr(0x2603), 401),
            ("GET", "Bearer " + "x" * 8200, 401),
        ):
            req = Request()
            req.method = method
            req.headers = {"Authorization": auth}
            with self.subTest(method=method, auth=repr(auth[:24])):
                code, data, headers = private_png_response(
                    req, shop_id=self.shop, job_id=self.job,
                    reader_factory=factory, enabled=True)
                self.assertEqual((code, data), (expected, b""))
                self.assertEqual(headers["Cache-Control"],
                                 "no-store, private, max-age=0")
                self.assertNotIn("Location", headers)
        self.assertEqual(calls, [])
        self.assertEqual(self.reader.calls, [])

    def test_factory_cannot_swap_authorization_after_preflight(self):
        # Synthetic mutable request: trusted factory may not cause the route
        # to use a second, unvalidated bearer value after preflight.
        req = Request()
        req.headers = {"Authorization": "Bearer signed-retailer-test"}
        def factory():
            req.headers["Authorization"] = "Bearer sb_secret_injected"
            return self.reader
        code, data, headers = private_png_response(
            req, shop_id=self.shop, job_id=self.job,
            reader_factory=factory, enabled=True)
        self.assertEqual(code, 200)
        self.assertEqual(data, self.reader.png)
        self.assertEqual(self.reader.calls, [("signed-retailer-test", self.shop, self.job)])
        self.assertNotIn("Location", headers)

    def test_malformed_and_noncanonical_route_ids_fail_before_reader(self):
        calls = []
        def factory():
            calls.append("constructed")
            return self.reader
        invalid = (
            "", "not-a-uuid", "../private", self.shop.upper(),
            self.shop.replace("-", ""), str(uuid4()) + "/",
            None, 123, "00000000-0000-0000-0000-000000000000",
        )
        for value in invalid:
            for field in ("shop_id", "job_id"):
                with self.subTest(value=repr(value), field=field):
                    params = {"shop_id": self.shop, "job_id": self.job}
                    params[field] = value
                    status, data, headers = private_png_response(
                        Request(), reader_factory=factory, enabled=True, **params)
                    self.assertEqual((status, data), (404, b""))
                    self.assertEqual(headers["Cache-Control"],
                                     "no-store, private, max-age=0")
        self.assertEqual(calls, [])
        self.assertEqual(self.reader.calls, [])
        self.assertEqual(self.invoke(factory)[0], 200)

    def test_malformed_request_header_mapping_fails_closed(self):
        # A hostile/malformed adapter must never instantiate the privileged
        # rights provider, nor expose any exception detail in the response.
        calls = []
        def factory():
            calls.append("constructed")
            return self.reader

        class RaisingHeaders:
            def get(self, *_args):
                raise RuntimeError("secret backend detail")

        class BrokenRequest:
            method = "GET"
            headers = RaisingHeaders()

        code, body, headers = private_png_response(
            BrokenRequest(), shop_id=self.shop, job_id=self.job,
            reader_factory=factory, enabled=True)
        self.assertEqual((code, body), (401, b""))
        self.assertEqual(calls, [])
        self.assertEqual(self.reader.calls, [])
        self.assertNotIn("secret", repr(headers).lower())

    def test_uuid_v1_and_wrong_type_are_denied_before_factory(self):
        from uuid import uuid1
        calls = []
        def factory():
            calls.append("constructed")
            return self.reader
        for invalid in (str(uuid1()), b"not-a-uuid", True, [], {}):
            with self.subTest(invalid=repr(invalid)):
                code, body, _ = private_png_response(
                    Request(), shop_id=invalid, job_id=self.job,
                    reader_factory=factory, enabled=True)
                self.assertEqual((code, body), (404, b""))
        self.assertEqual(calls, [])

    def test_malformed_method_denied_without_constructing_rights_reader(self):
        calls = []
        def factory():
            calls.append("constructed")
            return self.reader
        for invalid in (None, b"GET", 1, [], {}, "POST", "get"):
            with self.subTest(method=repr(invalid)):
                class MalformedRequest:
                    method = invalid
                    headers = {"Authorization": "Bearer signed-retailer-test"}
                code, body, headers = private_png_response(
                    MalformedRequest(), shop_id=self.shop, job_id=self.job,
                    reader_factory=factory, enabled=True)
                self.assertEqual((code, body), (405, b""))
                self.assertEqual(headers["Allow"], "GET")
                self.assertEqual(headers["Cache-Control"], "no-store, private, max-age=0")
        self.assertEqual(calls, [])
        self.assertEqual(self.reader.calls, [])

    def test_factory_preflight_is_executable_and_never_calls_noncallables(self):
        # Regression: a literal escaped newline previously commented out the
        # callable guard, leaving it dead code. Verify both source and behavior.
        import ast
        import inspect
        import feature3_private_binary_route as module
        tree = ast.parse(inspect.getsource(module.private_png_response))
        guards = [node for node in ast.walk(tree)
                  if isinstance(node, ast.If)
                  and isinstance(node.test, ast.UnaryOp)
                  and isinstance(node.test.operand, ast.Call)
                  and isinstance(node.test.operand.func, ast.Name)
                  and node.test.operand.func.id == "callable"]
        self.assertEqual(len(guards), 1)
        for factory in (None, False, 123, "fake-reader", {}, []):
            with self.subTest(factory=repr(factory)):
                code, body, headers = self.invoke(factory)
                self.assertEqual((code, body), (503, b""))
                self.assertEqual(headers["Cache-Control"],
                                 "no-store, private, max-age=0")
                self.assertNotIn("Location", headers)
        self.assertEqual(self.reader.calls, [])
        self.assertEqual(self.invoke(lambda: self.reader)[0], 200)

    def test_ambiguous_bearer_credentials_rejected_before_factory(self):
        # Simulate proxy-folded duplicate Authorization headers. Never let
        # downstream JWT verifier choose a different credential from preflight.
        calls = []
        def factory():
            calls.append("constructed")
            return self.reader
        for auth in (
            "Bearer signed-retailer-test, Bearer attacker-token",
            "Bearer signed-retailer-test,Bearer attacker-token",
            "Bearer signed-retailer-test\\\\Bearer attacker-token",
            "Bearer signed-retailer-test Bearer attacker-token",
            "Bearer signed-retailer-test, Basic attacker",
        ):
            with self.subTest(auth=auth):
                req = Request()
                req.headers = {"Authorization": auth}
                status, body, headers = private_png_response(
                    req, shop_id=self.shop, job_id=self.job,
                    reader_factory=factory, enabled=True)
                self.assertEqual((status, body), (401, b""))
                self.assertEqual(headers["Cache-Control"],
                                 "no-store, private, max-age=0")
        self.assertEqual(calls, [])
        self.assertEqual(self.reader.calls, [])
        self.assertEqual(self.invoke(factory)[0], 200)

    def test_bad_token_denied_before_reader(self):
        req = Request()
        req.headers = {"Authorization": "Bearer sb_secret_invalid"}
        code, body, _ = private_png_response(
            req, shop_id=self.shop, job_id=self.job,
            reader_factory=lambda: self.reader, enabled=True)
        self.assertEqual((code, body), (401, b""))
        self.assertEqual(self.reader.calls, [])


if __name__ == "__main__":
    unittest.main()
