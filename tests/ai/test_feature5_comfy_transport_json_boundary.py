"""CPU-only ComfyUI loopback JSON boundary tests; no network or GPU."""
import unittest
from unittest.mock import patch

from feature5_motion.wan22_comfy_execution import LoopbackComfyTransport
from feature5_motion.wan22_motion_adapter import WanCompatibilityError


class _Response:
    status = 200

    def __init__(self, payload):
        self.payload = payload

    def read(self, maximum):
        return self.payload[:maximum]


class _Connection:
    def __init__(self, payload):
        self.payload = payload
        self.requests = []
        self.closed = False

    def request(self, method, path, body=None, headers=None):
        self.requests.append((method, path, body, headers))

    def getresponse(self):
        return _Response(self.payload)

    def close(self):
        self.closed = True


class ComfyStrictResponseTests(unittest.TestCase):
    def _read(self, payload, method="GET", path="/object_info", body=None):
        conn = _Connection(payload)
        with patch(
            "feature5_motion.wan22_comfy_execution.http.client.HTTPConnection",
            return_value=conn,
        ) as factory:
            try:
                result = LoopbackComfyTransport()(method, path, body)
                return result
            finally:
                self.assertTrue(conn.closed)
                factory.assert_called_once_with("127.0.0.1", 8188, timeout=5)
                self.assertEqual(len(conn.requests), 1)

    def test_valid_strict_json_still_supports_object_info_and_ack(self):
        self.assertEqual(
            self._read(b'{"LoadImage":{"input":{"required":{"image":["STRING",{}]}}}}'),
            {"LoadImage": {"input": {"required": {"image": ["STRING", {}]}}}},
        )
        self.assertEqual(
            self._read(
                b'{"prompt_id":"safe","number":1,"node_errors":{}}',
                "POST", "/prompt", {"prompt": {}, "prompt_id": "safe"},
            ),
            {"prompt_id": "safe", "number": 1, "node_errors": {}},
        )

    def test_duplicate_fields_are_denied_at_any_depth(self):
        for payload in (
            b'{"prompt_id":"valid","prompt_id":"forged"}',
            b'{"LoadImage":{"input":{"required":{},"required":{"image":[]}}}}',
            b'{"x":{"a":1,"a":2}}',
        ):
            with self.subTest(payload=payload), self.assertRaises(WanCompatibilityError):
                self._read(payload)

    def test_nonstandard_and_overflow_numbers_are_denied(self):
        for payload in (
            b'{"number":NaN}', b'{"number":Infinity}',
            b'{"number":-Infinity}', b'{"number":1e999}',
            b'{"number":-1e999}',
        ):
            with self.subTest(payload=payload), self.assertRaises(WanCompatibilityError):
                self._read(payload)

    def test_deep_or_excessively_complex_payloads_are_denied(self):
        nested = b'{"x":' + b"[" * 70 + b"0" + b"]" * 70 + b"}"
        wide = b'{"x":[' + b"0," * 100000 + b"0]}"
        for payload in (nested, wide):
            with self.subTest(size=len(payload)), self.assertRaises(WanCompatibilityError):
                self._read(payload)

    def test_malformed_bytes_and_non_object_roots_are_denied(self):
        for payload in (b"\xff", b"[]", b"null", b'{"x":'):
            with self.subTest(payload=payload), self.assertRaises(WanCompatibilityError):
                self._read(payload)


if __name__ == "__main__":
    unittest.main()
