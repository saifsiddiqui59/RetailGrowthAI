"""HTTP telemetry stays useful under errors without carrying customer data."""
import json
from pathlib import Path
import re
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "azure-functions/campaign-api"))
from request_diagnostics import RequestDiagnostics, retry_advice, route_name

CID = "a1111111-1111-4111-8111-111111111111"
DID = "b2222222-2222-4222-8222-222222222222"


class Capture:
    def __init__(self): self.rows = []
    def info(self, message): self.rows.append(json.loads(message))


class DiagnosticsTests(unittest.TestCase):
    def test_route_names_are_fixed_and_do_not_include_ids_or_queries(self):
        self.assertEqual(route_name("PATCH", f"/api/campaigns/{CID}/days/{DID}"), "campaign.day.save")
        self.assertEqual(route_name("GET", f"/poster-jobs/{CID}/download"), "poster.download")
        self.assertEqual(route_name("GET", f"/api/campaigns/{CID}/days/{DID}/posters"), "poster.list")
        self.assertEqual(route_name("POST", f"/api/poster-drafts/{DID}/select"), "poster.select")
        self.assertEqual(route_name("POST", f"/poster-jobs/{DID}/select"), "unknown")
        self.assertEqual(route_name("GET", f"/campaigns/{CID}/posters"), "unknown")
        for path in ("https://bad.example/a?token=secret", "/campaigns/person@email.test",
                     f"/campaigns/{CID}?token=secret", "/campaigns/../secret", None,
                     "/" + "a" * 513):
            self.assertEqual(route_name("GET", path), "unknown")

    def test_secrets_in_payload_or_path_cannot_reach_log(self):
        logger = Capture()
        clock = iter((10.0, 10.125)).__next__
        item = RequestDiagnostics("GET", "/unknown?token=private", clock=clock, logger=logger)
        headers = item.complete(503, {"error": "email@private.test", "jwt": "Bearer secret",
                                      "url": "https://private.test/?token=secret"})
        self.assertEqual(logger.rows[0]["error_code"], "OTHER")
        self.assertEqual(logger.rows[0]["route"], "unknown")
        self.assertEqual(logger.rows[0]["latency_ms"], 125)
        self.assertNotIn("private", json.dumps(logger.rows))
        self.assertTrue(re.fullmatch("[0-9a-f]{32}", headers["X-Request-ID"]))
        self.assertEqual(headers["Cache-Control"], "no-store")
        self.assertEqual(headers["Access-Control-Expose-Headers"], "X-Request-ID")
        self.assertEqual(headers["Retry-After"], "2")

    def test_malformed_json_denial_and_config_failure_have_safe_headers(self):
        for code, error, outcome in ((400, "INVALID_REQUEST", "failed"),
                                      (401, "UNAUTHORIZED", "denied"),
                                      (503, "SERVICE_NOT_CONFIGURED", "failed")):
            logger = Capture()
            item = RequestDiagnostics("POST", "/campaigns", logger=logger)
            headers = item.complete(code, {"error": error})
            self.assertEqual(logger.rows[0]["status"], outcome)
            self.assertEqual(logger.rows[0]["status_code"], code)
            self.assertEqual(logger.rows[0]["error_code"], error)
            self.assertEqual(headers["X-Content-Type-Options"], "nosniff")
            self.assertNotIn("Retry-After", headers)

    def test_no_automatic_mutation_replay_even_if_server_has_idempotency(self):
        for method in ("POST", "PATCH", "PUT", "DELETE", "OTHER"):
            self.assertEqual(retry_advice(method, 503), "reconcile_first")
        for method in ("GET", "HEAD"):
            for code in (502, 503, 504):
                self.assertEqual(retry_advice(method, code), "bounded_read")
        for code in (200, 400, 401, 403, 409, 429, 500):
            self.assertEqual(retry_advice("GET", code), "none")

    def test_exactly_one_event_even_if_complete_called_twice(self):
        logger = Capture()
        item = RequestDiagnostics("GET", f"/campaigns/{CID}", logger=logger)
        original = item.complete(200, {"days": [{"private": "copy"}]})
        original["X-Request-ID"] = "caller-mutated"
        repeated = item.complete(500, {"error": "INTERNAL_ERROR"})
        self.assertEqual(len(logger.rows), 1)
        self.assertEqual(logger.rows[0]["status_code"], 200)
        self.assertNotEqual(repeated["X-Request-ID"], "caller-mutated")

    def test_negative_or_unbounded_clock_does_not_corrupt_metrics(self):
        for stop, expected in ((-4.0, 0), (float("inf"), 0), (10**20, 86_400_000)):
            logger = Capture()
            item = RequestDiagnostics("GET", "/unknown", logger=logger,
                                      clock=iter((0.0, stop)).__next__)
            item.complete(404)
            self.assertEqual(logger.rows[0]["latency_ms"], expected)

    def test_invalid_status_and_untrusted_method_never_enter_log(self):
        logger = Capture()
        item = RequestDiagnostics("GET\nAuthorization: secret", "/campaigns", logger=logger)
        for value in (True, "503", 0, 999):
            with self.assertRaises(ValueError): item.complete(value)
        self.assertFalse(logger.rows)
        item.complete(404, {"error": {"Authorization": "secret"}})
        self.assertEqual(logger.rows[0]["method"], "OTHER")
        self.assertNotIn("secret", json.dumps(logger.rows))


if __name__ == "__main__": unittest.main()
