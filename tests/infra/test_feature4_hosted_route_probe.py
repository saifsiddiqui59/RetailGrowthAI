"""Offline tests for the separate F4 live route acceptance probe."""
import importlib.util
import io
from pathlib import Path
import unittest
from urllib.error import HTTPError

ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location(
    "f4_hosted_probe", ROOT / "scripts/deploy/probe_feature4_hosted_routes.py")
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)


class FakeResponse:
    def __init__(self, code=401, body=b'{"error":"UNAUTHORIZED"}',
                 headers=None):
        self.code, self.body = code, body
        self.headers = {"X-Request-ID": "a" * 32} if headers is None else headers

    def getcode(self):
        return self.code

    def read(self, limit):
        return self.body[:limit]

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False


class FakeOpener:
    def __init__(self, response):
        self.response, self.requests = response, []

    def open(self, req, timeout):
        self.requests.append(req)
        assert timeout == 25
        return self.response


class F4HostedRoutes(unittest.TestCase):
    def test_all_seven_marked_401_only(self):
        o = FakeOpener(FakeResponse())
        result = m.verify("isolated-y1", o)
        self.assertEqual(len(result), 7)
        self.assertEqual(set(result.values()), {"marked_401"})
        self.assertEqual(len(o.requests), 7)
        self.assertEqual(sum(req.get_method() == "POST" for req in o.requests), 4)
        for req in o.requests:
            self.assertTrue(req.full_url.startswith(m.ORIGINS["isolated-y1"] + "/api/"))
            self.assertIsNone(req.get_header("Authorization"))
            self.assertEqual(req.data, b"{}" if req.get_method() == "POST" else None)

    def test_unmarked_wrong_body_redirect_and_unavailable_not_accepted(self):
        for response in (
            FakeResponse(headers={}), FakeResponse(body=b'{"error":"OTHER"}'),
            FakeResponse(code=302), FakeResponse(code=404), FakeResponse(code=503),
        ):
            with self.subTest(code=response.code, headers=response.headers):
                result = m.verify("original-flex", FakeOpener(response))
                self.assertEqual(len(result), 7)
                self.assertNotIn("marked_401", result.values())

    def test_unexpected_success_aborts_without_more_requests(self):
        o = FakeOpener(FakeResponse(code=202))
        self.assertEqual(list(m.verify("isolated-y1", o).values()), ["unexpected_success"])
        self.assertEqual(len(o.requests), 1)

    def test_real_http_error_response_is_inspected_and_not_replayed(self):
        class ErrorOpener:
            calls = 0
            def open(self, req, timeout):
                self.calls += 1
                raise HTTPError(req.full_url, 401, "Unauthorized",
                                {"X-Request-ID": "b" * 32},
                                io.BytesIO(b'{"error":"UNAUTHORIZED"}'))
        o = ErrorOpener()
        self.assertEqual(set(m.verify("isolated-y1", o).values()), {"marked_401"})
        self.assertEqual(o.calls, 7)

    def test_foreign_target_and_redirect_denied(self):
        with self.assertRaises(ValueError):
            m.verify("https://foreign.example", FakeOpener(FakeResponse()))
        self.assertIsNone(m.NoRedirects().redirect_request(None, None, 302, "", {}, "https://foreign.example"))


if __name__ == "__main__":
    unittest.main()
