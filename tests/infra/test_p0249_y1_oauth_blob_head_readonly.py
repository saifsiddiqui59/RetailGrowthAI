"""Synthetic read-only OAuth HEAD tests, no network, Azure login or secrets."""
from contextlib import redirect_stdout
from email.message import Message
from io import BytesIO, StringIO
from pathlib import Path
import json
import sys
import unittest
import urllib.error
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "ops"))
import p0249_y1_oauth_blob_head_readonly as audit
import p0249_y1_remote_build_mode as mode


class BlobOAuthHeadTests(unittest.TestCase):
    def test_fixed_status_and_header_allowlist(self):
        cases = (
            (200, None, "BLOB_EXISTS_OAUTH_READ_ALLOWED", "NONE"),
            (404, "BlobNotFound", "BLOB_NOT_FOUND_OR_HIDDEN", "BlobNotFound"),
            (403, "AuthorizationPermissionMismatch", "OAUTH_OR_NETWORK_FORBIDDEN",
             "AuthorizationPermissionMismatch"),
            (403, "Unknown https://private/?sig=SECRET", "OAUTH_OR_NETWORK_FORBIDDEN",
             "OTHER_REDACTED"),
            (302, "InvalidAuthenticationInfo", "REDIRECT_DENIED", "InvalidAuthenticationInfo"),
            (503, "ServerBusy", "TRANSIENT_OR_UPSTREAM", "ServerBusy"),
        )
        for status, error, category, label in cases:
            with self.subTest(status=status, error=error):
                self.assertEqual(audit.classify_http(status, error), (category, label))
                self.assertNotIn("SECRET", " ".join(audit.classify_http(status,error)))

    def test_head_to_fixed_host_denies_http_redirect_and_never_leaks_token(self):
        headers = Message()
        headers["Location"] = "https://attacker.invalid/?sig=DO_NOT_VISIT"
        headers["x-ms-error-code"] = "Anything with sig=SECRET"
        redirect = urllib.error.HTTPError(
            "https://attacker.invalid/", 302, "redirect", headers, BytesIO(b"NO"))
        out = StringIO()
        with patch.object(audit._OPENER,"open",side_effect=redirect) as opener, \
             redirect_stdout(out):
            verdict = audit.head_existing_failed_blob("private", "SECRET_BEARER")
        self.assertEqual(verdict, ("REDIRECT_DENIED", "OTHER_REDACTED"))
        self.assertEqual(opener.call_count, 1)
        request = opener.call_args.args[0]
        self.assertEqual(request.get_method(), "HEAD")
        self.assertEqual(request.full_url,
            "https://" + audit.guard.STORAGE + ".blob.core.windows.net/private/" + audit.BLOB)
        self.assertEqual(opener.call_args.kwargs["timeout"],18)
        self.assertIn("SECRET_BEARER", request.get_header("Authorization"))
        self.assertEqual(out.getvalue(),"")

    def test_classifies_forbidden_without_response_body_or_header_reflection(self):
        headers = Message()
        headers["x-ms-error-code"] = "AuthorizationFailure"
        forbidden = urllib.error.HTTPError(
            "https://storage.invalid/private",403,"hidden",headers,BytesIO(b"secret"))
        with patch.object(audit._OPENER,"open",side_effect=forbidden):
            self.assertEqual(
                audit.head_existing_failed_blob("private","SECRET_TOKEN"),
                ("OAUTH_OR_NETWORK_FORBIDDEN","AuthorizationFailure"))

    def test_unverified_original_two_route_never_acquires_storage_token(self):
        with patch.object(audit.guard,"verify",return_value=None), \
             patch.object(audit.mode,"_settings",return_value={}), \
             patch.object(audit.mode,"_index",return_value=mode.TWO), \
             patch.object(audit.pkg,"scoped_baseline",side_effect=RuntimeError("PRIVATE SAS")), \
             patch.object(audit,"acquire_storage_token") as token, \
             patch.object(audit.guard,"probe") as probe, redirect_stdout(StringIO()):
            with self.assertRaises(RuntimeError):
                audit.main()
        token.assert_not_called()
        probe.assert_not_called()

    def test_exact_read_only_workflow_and_source(self):
        code = (ROOT / "ops/p0249_y1_oauth_blob_head_readonly.py").read_text()
        workflow = (ROOT / ".github/workflows/p0249-y1-oauth-blob-head-once.yml").read_text()
        self.assertIn("environment: dev", workflow)
        self.assertIn("id-token: write", workflow)
        self.assertIn("startsWith(github.event.head_commit.message", workflow)
        self.assertIn("p0249_y1_oauth_blob_head_readonly.py", workflow)
        self.assertIn("method=\"HEAD\"", code)
        self.assertIn("NoRedirects", code)
        self.assertIn("pkg.scoped_baseline(settings, indexed)", code)
        self.assertIn("guard.probe()", code)
        for forbidden in ("--account-key", "az storage blob upload", "az storage account keys",
                          "role assignment create", "functionapp config appsettings set",
                          "method=\"POST\"", "method=\"PUT\""):
            self.assertNotIn(forbidden,code)
            self.assertNotIn(forbidden,workflow)
        for key in ("\n  workflow_dispatch:", "\n  schedule:", "\n  pull_request:"):
            self.assertNotIn(key,workflow)


if __name__ == "__main__":
    unittest.main()
