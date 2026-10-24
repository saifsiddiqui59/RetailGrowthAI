"""Exercise the actual Azure HTTP adapter's safe response/telemetry paths."""
import ast
import json
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

import azure.functions as func

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "azure-functions/campaign-api"))
from request_diagnostics import RequestDiagnostics  # noqa: E402

# Test the checked-in dispatch function, without importing unrelated Azure
# queue/blob workers (they have separately tested dependency boundaries).
source = ROOT / "azure-functions/campaign-api/function_app.py"
tree = ast.parse(source.read_text(encoding="utf-8"), filename=str(source))
node = next(item for item in tree.body if isinstance(item, ast.FunctionDef)
            and item.name == "dispatch")
runtime = {"RequestDiagnostics": RequestDiagnostics, "json": json, "func": func}
exec(compile(ast.Module(body=[node], type_ignores=[]), str(source), "exec"), runtime)
dispatch = runtime["dispatch"]


class StubAPI:
    def __init__(self, code=200, payload=None):
        self.code = code
        self.payload = payload or {"status": "ok"}
        self.calls = []

    def handle(self, method, path, auth, body):
        self.calls.append((method, path, auth, body))
        return self.code, self.payload


class HTTPDiagnosticsAdapterTests(unittest.TestCase):
    def request(self, method="GET", body=b"", path="/api/campaigns", auth="Bearer fake"):
        return func.HttpRequest(method=method, url="https://dev.example" + path,
                                headers={"Authorization": auth, "Content-Type": "application/json"},
                                body=body)

    def test_normal_authenticated_response_retains_correlation_header(self):
        api = StubAPI(200, {"campaign": "no-secret"})
        with patch.dict(runtime, {"build_api": lambda: api}):
            response = dispatch(self.request(), "/campaigns")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(api.calls[0][2], "Bearer fake")
        self.assertRegex(response.headers["X-Request-ID"], r"^[a-f0-9]{32}$")
        self.assertEqual(response.headers["Cache-Control"], "no-store")
        self.assertEqual(json.loads(response.get_body())["campaign"], "no-secret")

    def test_malformed_json_denied_without_entering_business_api(self):
        api = StubAPI()
        with patch.dict(runtime, {"build_api": lambda: api}):
            response = dispatch(self.request("POST", b"{broken"), "/campaigns")
        self.assertEqual(response.status_code, 400)
        self.assertEqual(json.loads(response.get_body()), {"error": "INVALID_REQUEST"})
        self.assertEqual(api.calls, [])
        self.assertRegex(response.headers["X-Request-ID"], r"^[a-f0-9]{32}$")

    def test_config_error_returns_safe_503_not_a_stack_trace(self):
        with patch.dict(runtime, {"build_api": lambda: (_ for _ in ()).throw(KeyError("RETAIL_SECRET"))}):
            response = dispatch(self.request("POST", b"{}"), "/campaigns")
        self.assertEqual(response.status_code, 503)
        self.assertEqual(json.loads(response.get_body()), {"error": "SERVICE_NOT_CONFIGURED"})
        self.assertNotIn("Retry-After", response.headers)

    def test_runtime_exception_fails_closed_without_leak(self):
        with patch.dict(runtime, {"build_api": lambda: (_ for _ in ()).throw(RuntimeError("token=do-not-log"))}):
            response = dispatch(self.request(), "/campaigns")
        self.assertEqual(response.status_code, 500)
        self.assertNotIn("token=do-not-log", response.get_body().decode())
        self.assertEqual(json.loads(response.get_body()), {"error": "INTERNAL_ERROR"})

    def test_bounded_retry_advice_only_on_get(self):
        api = StubAPI(503, {"error": "QUEUE_UNAVAILABLE"})
        with patch.dict(runtime, {"build_api": lambda: api}):
            response = dispatch(self.request(), "/campaigns")
        self.assertEqual(response.headers["Retry-After"], "2")
        self.assertEqual(response.headers["X-Content-Type-Options"], "nosniff")
        with patch.dict(runtime, {"build_api": lambda: api}):
            mutation = dispatch(self.request("POST", b"{}"), "/campaigns")
        self.assertNotIn("Retry-After", mutation.headers)


if __name__ == "__main__":
    unittest.main()
