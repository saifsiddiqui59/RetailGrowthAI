"""Offline safety and evidence tests for recent #249 Azure Flex host correlation."""
from __future__ import annotations

from contextlib import redirect_stdout
import io
import json
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "ops"))
import p0_249_recent_http_platform_readonly as incident


class IncidentCorrelationTests(unittest.TestCase):
    def test_queries_are_fixed_to_approved_dev_app_and_exact_incidents(self):
        self.assertEqual(len(incident.WINDOWS), 4)
        for label, start, end in incident.WINDOWS:
            for kind in incident.KINDS:
                q = incident.build_query(label, kind)
                self.assertIn(start, q)
                self.assertIn(end, q)
                self.assertEqual(q.count(" | take 80"), 1)
                self.assertIn("rgai-dev-functions-d4e5ddbd", q)
                if kind == "activity":
                    self.assertIn("AzureActivity", q)
                    self.assertIn("rg-retailgrowth-dev", q)
                else:
                    self.assertIn(incident.APP_SCOPE, q)
                    self.assertIn("instance=", q)
                    self.assertIn(" | where ", q)
                self.assertNotIn("Authorization", q)
                self.assertNotIn("token", q)
        host = incident.build_query("nov08_1755", "host")
        for signal in ("drainmode", "worker process exited", "worker process started",
                       "pendingitem.ontimeout", "specializeasync"):
            self.assertIn(signal, host)
        for bad in ("", "tomorrow", "nov08_1755;print('secret')"):
            with self.assertRaises(ValueError):
                incident.build_query(bad, "host")
        for bad in ("", "AppTraces | project Message", "secrets"):
            with self.assertRaises(ValueError):
                incident.build_query("nov08_1755", bad)

    def test_sanitizer_retains_only_approved_minute_counts_and_hashed_instance(self):
        raw = {"bucket": "2026-11-08T17:55:00.0000000Z", "events": "3",
               "event": "drain_mode", "instance": "private-platform-worker-id",
               "Message": "JWT: PRIVATE_TOKEN", "Url": "https://secret.invalid/a",
               "tenant_id": "private-shop"}
        rows = incident.safe_rows([raw], window="nov08_1755", kind="host")
        self.assertEqual(len(rows), 1)
        row = rows[0]
        self.assertEqual(row["events"], 3)
        self.assertEqual(row["event"], "drain_mode")
        self.assertEqual(len(row["host_hash"]), 12)
        self.assertEqual(row["bucket"], raw["bucket"])
        self.assertNotIn("private-", json.dumps(row))
        self.assertNotIn("PRIVATE_TOKEN", json.dumps(row))
        self.assertNotIn("Url", row)
        self.assertNotIn("tenant_id", row)
        self.assertEqual(incident.safe_rows([raw], window="nov06_1952", kind="host"), [])
        self.assertEqual(incident.safe_rows([dict(raw, event=["unhashable"])],
                                            window="nov08_1755", kind="host"), [])

    def test_date_parser_rejects_wrong_or_untrusted_bucket(self):
        bad_buckets = (
            "2026-11-08T17:55:01Z", "2026-11-08T17:55:00.0000001Z",
            "2026-11-08T17:55:00.00000000Z", "2026-11-08T17:55:00+01:00",
            "2026-11-08T19:55:00Z", "2026-11-09T17:55:00Z",
            "2026-11-08T17:55:00Z JWT=PRIVATE", None, {}, [],
        )
        for bad in bad_buckets:
            with self.subTest(bucket=repr(bad)):
                got = incident.safe_rows(
                    [{"bucket": bad, "events": 1, "event": "worker_start"}],
                    window="nov08_1755", kind="host",
                )
                self.assertEqual(got, [])

    def test_count_validation_and_no_worker_identity_leaks(self):
        baseline = {"bucket": "2026-11-08T17:55:00Z", "events": "2",
                    "app_401": "1", "reported_503": "0",
                    "internal_or_missing": "1", "instance": "raw-PROTECTED-abc"}
        out = incident.safe_rows({"value": [baseline]}, window="nov08_1755",
                                 kind="requests")
        self.assertEqual(out[0]["app_401"], 1)
        self.assertEqual(out[0]["reported_503"], 0)
        self.assertNotIn("raw-PROTECTED", json.dumps(out))
        for bad in (True, -1, 1.5, "Infinity", "99999999", ["x"]):
            with self.subTest(value=repr(bad)):
                sample = dict(baseline, events=bad)
                self.assertEqual(incident.safe_rows(
                    [sample], window="nov08_1755", kind="requests"), [])
        with self.assertRaises(ValueError):
            incident.safe_rows([baseline], window="invalid", kind="requests")

    def test_collect_only_reads_existing_dev_and_never_prints_raw_azure(self):
        calls = []
        scope_checks = []
        def fake_scope():
            scope_checks.append(True)
            return "/validated/DEV/resource"
        def fake_azure(*args):
            calls.append(args)
            if args[2:5] == ("workspace", "show", "-g"):
                return {"customerId": "private-workspace-id"}
            self.assertEqual(args[:3], ("monitor", "log-analytics", "query"))
            query = args[-1]
            window = next((w for w in incident.WINDOWS if w[1] in query), None)
            self.assertIsNotNone(window)
            bucket = window[1]
            if query.startswith("AppTraces"):
                return [{"bucket": bucket, "events": "1",
                         "event": "drain_mode", "instance": "PRIVATE_INSTANCE",
                         "Message": "SECRET_JWT", "Url": "https://private.invalid"}]
            if query.startswith("AppRequests"):
                return [{"bucket": bucket, "events": "2", "app_401": "1",
                         "reported_503": "0", "internal_or_missing": "1",
                         "instance": "PRIVATE_INSTANCE", "Message": "SECRET_JWT"}]
            self.assertTrue(query.startswith("AzureActivity"))
            return [{"bucket": bucket, "events": "1", "operation": "PRIVATE_RESOURCE"}]
        out = io.StringIO()
        with patch.object(incident, "audit_scope", fake_scope), \
                patch.object(incident, "azure", fake_azure), \
                redirect_stdout(out):
            self.assertEqual(incident.collect(), 0)
        printed = out.getvalue()
        self.assertEqual(len(scope_checks), 1)
        self.assertEqual(len(calls), 1 + len(incident.WINDOWS) * len(incident.KINDS))
        self.assertEqual(printed.count("P0249_INCIDENT="), 12)
        for secret in ("PRIVATE_INSTANCE", "SECRET_JWT", "PRIVATE_RESOURCE",
                       "private-workspace-id"):
            self.assertNotIn(secret, printed)
        self.assertIn("P0249_NO_HTTP_REQUEST_TO_INSTANCE_CAUSAL_PROOF=true", printed)
        self.assertIn("P0249_READ_ONLY_NO_CONFIG_WRITES_NO_NEW_RESOURCES=true", printed)


if __name__ == "__main__":
    unittest.main()
