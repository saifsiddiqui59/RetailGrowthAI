"""Offline negative regressions for #249 package publisher OIDC Blob HEAD guard."""
from contextlib import redirect_stdout
from email.message import Message
from io import BytesIO, StringIO
from pathlib import Path
import tempfile
import sys
import unittest
import urllib.error
from unittest.mock import MagicMock, patch

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "ops"))
import p0249_y1_external_private_package as release
import p0249_y1_remote_build_mode as mode

ORIGINAL = ("https://" + release.EXPECTED_URI_HOST
            + "/private/original-two.zip?sv=1&sig=NEVER_LOG_THIS")
TOKEN = "in-memory-token-" + "x" * 150


class OriginalBlobReadGuardTests(unittest.TestCase):
    def test_existing_original_blob_read_passes_without_forwarding_sas(self):
        opener = MagicMock()
        response = MagicMock()
        response.__enter__.return_value.status = 200
        opener.open.return_value = response
        output = StringIO()
        with (
            patch.object(release, "azure", return_value={"accessToken": TOKEN}) as az,
            patch.object(release.urllib.request, "build_opener", return_value=opener) as build,
            redirect_stdout(output),
        ):
            release._oauth_head_original_private_blob(ORIGINAL, "private")
        az.assert_called_once_with("account", "get-access-token",
                                  "--resource", "https://storage.azure.com/")
        self.assertTrue(any(isinstance(h, release._NoBlobRedirect)
                            for h in build.call_args.args))
        req = opener.open.call_args.args[0]
        self.assertEqual(req.get_method(), "HEAD")
        self.assertEqual(
            req.full_url,
            "https://" + release.EXPECTED_URI_HOST + "/private/original-two.zip")
        self.assertEqual(opener.open.call_args.kwargs["timeout"], 18)
        self.assertEqual(req.get_header("Authorization"), "Bearer " + TOKEN)
        self.assertEqual(output.getvalue().strip(),
                         "P0249_Y1_ORIGINAL_BLOB_OAUTH_READ=PASS_NO_WRITES")
        self.assertNotIn("sig=", req.full_url)
        self.assertNotIn(TOKEN, output.getvalue())

    def test_403_does_not_leak_token_sas_or_arbitrary_headers(self):
        headers = Message()
        headers["x-ms-error-code"] = "AuthorizationPermissionMismatch?sig=SECRET"
        headers["Location"] = "https://hostile.invalid/?sig=SECRET"
        response = urllib.error.HTTPError(
            "https://hostile.invalid/", 403, "SECRET", headers,
            BytesIO(b"body SECRET"))
        opener = MagicMock()
        opener.open.side_effect = response
        output = StringIO()
        with (
            patch.object(release, "azure", return_value={"accessToken": TOKEN}),
            patch.object(release.urllib.request, "build_opener", return_value=opener),
            redirect_stdout(output),
        ):
            with self.assertRaisesRegex(RuntimeError, "redacted"):
                release._oauth_head_original_private_blob(ORIGINAL, "private")
        opener.open.assert_called_once()
        self.assertIn("ACCESS_DENIED", output.getvalue())
        for forbidden in ("SECRET", TOKEN, "sig=", "hostile.invalid",
                          release.EXPECTED_URI_HOST):
            self.assertNotIn(forbidden, output.getvalue())
        self.assertEqual(release.CURRENT_STAGE, "BLOB_OAUTH_READ")

    def test_denial_classes_are_fixed_and_never_reflect_untrusted_headers(self):
        classes = (
            (401, "AuthenticationFailed", "ACCESS_DENIED_401_AUTHENTICATION"),
            (403, "AuthorizationPermissionMismatch", "ACCESS_DENIED_403_PERMISSION_MISMATCH"),
            (403, "NetworkAccessDenied", "ACCESS_DENIED_403_NETWORK_POLICY"),
            (403, "AuthenticationFailed", "ACCESS_DENIED_403_AUTHENTICATION"),
            (403, "AuthorizationFailure", "ACCESS_DENIED_403_UNCLASSIFIED"),
            (403, "AuthorizationPermissionMismatch?sig=SECRET", "ACCESS_DENIED_403_UNCLASSIFIED"),
            (302, "Location=https://hostile.invalid/?sig=SECRET", "REDIRECT_DENIED"),
            (404, "BlobNotFound", "NOT_FOUND_OR_HIDDEN"),
            (503, "ServiceUnavailable", "TRANSIENT_OR_UPSTREAM"),
        )
        for status, code, expected in classes:
            with self.subTest(status=status, code=code):
                self.assertEqual(release._original_blob_oauth_http_label(status, code), expected)
                headers = Message()
                headers["x-ms-error-code"] = code
                headers["Location"] = "https://hostile.invalid/?sig=SECRET"
                error = urllib.error.HTTPError(
                    "https://hostile.invalid/?sig=SECRET", status, "SENSITIVE",
                    headers, BytesIO(b"SENSITIVE"))
                opener = MagicMock()
                opener.open.side_effect = error
                output = StringIO()
                with (
                    patch.object(release, "azure", return_value={"accessToken": TOKEN}),
                    patch.object(release.urllib.request, "build_opener", return_value=opener),
                    redirect_stdout(output),
                ):
                    with self.assertRaisesRegex(RuntimeError, "redacted"):
                        release._oauth_head_original_private_blob(ORIGINAL, "private")
                self.assertEqual(
                    output.getvalue().strip(),
                    "P0249_Y1_ORIGINAL_BLOB_OAUTH_READ=" + expected)
                for forbidden in ("SENSITIVE", "SECRET", "hostile.invalid", "sig=", TOKEN):
                    self.assertNotIn(forbidden, output.getvalue())
                opener.open.assert_called_once()

    def test_redirect_is_denied_without_second_origin_request(self):
        headers = Message()
        headers["Location"] = "https://hostile.invalid/steal"
        error = urllib.error.HTTPError(
            "https://example.invalid", 302, "redirect", headers, BytesIO(b""))
        opener = MagicMock()
        opener.open.side_effect = error
        with (
            patch.object(release, "azure", return_value={"accessToken": TOKEN}),
            patch.object(release.urllib.request, "build_opener", return_value=opener),
            redirect_stdout(StringIO()),
        ):
            with self.assertRaises(RuntimeError):
                release._oauth_head_original_private_blob(ORIGINAL, "private")
        opener.open.assert_called_once()
        self.assertIsNone(release._NoBlobRedirect().redirect_request(
            None, None, 302, "redirect", headers, headers["Location"]))

    def test_bad_source_or_opaque_token_fails_before_http(self):
        invalid = (
            "https://evil.invalid/private/old.zip?sig=SECRET",
            "https://" + release.EXPECTED_URI_HOST + "/other/old.zip?sig=SECRET",
            "https://" + release.EXPECTED_URI_HOST + "/private/../file.zip?sig=SECRET",
            "https://" + release.EXPECTED_URI_HOST + "/private/?sig=SECRET",
            "http://" + release.EXPECTED_URI_HOST + "/private/file.zip",
        )
        for url in invalid:
            with self.subTest(url=url):
                with (
                    patch.object(release, "azure") as az,
                    patch.object(release.urllib.request, "build_opener") as builder,
                ):
                    with self.assertRaises(RuntimeError):
                        release._oauth_head_original_private_blob(url, "private")
                    az.assert_not_called()
                    builder.assert_not_called()
        with (
            patch.object(release, "azure", return_value={"accessToken": "short"}),
            patch.object(release.urllib.request, "build_opener") as builder,
        ):
            with self.assertRaisesRegex(RuntimeError, "redacted"):
                release._oauth_head_original_private_blob(ORIGINAL, "private")
            builder.assert_not_called()

    def test_preflight_refuses_upload_and_sas_when_existing_blob_read_denied(self):
        settings = {
            release.BACKUP: ORIGINAL,
            release.PACKAGE_KEY: ORIGINAL,
            release.OLD_OWNER: release.EXPECTED_FAILED_OWNER,
            "SCM_DO_BUILD_DURING_DEPLOYMENT": "true",
        }
        def denied(old, container):
            release.mark_stage("BLOB_OAUTH_READ")
            raise RuntimeError("Original package OAuth HEAD denied (redacted)")
        with tempfile.TemporaryDirectory() as folder:
            zippath = Path(folder) / "five.zip"
            zippath.write_bytes(b"x" * 4000)
            with (
                patch.object(release, "_read_site", return_value=(settings, mode.TWO)),
                patch.object(release, "azure", return_value={"exists": True}) as az,
                patch.object(release, "_oauth_head_original_private_blob",
                             side_effect=denied) as head,
                patch.object(release, "_sas") as sas,
                patch.object(release, "_upload") as upload,
                patch.object(mode, "_set") as change,
            ):
                with self.assertRaisesRegex(RuntimeError, "redacted"):
                    release.preflight(zippath)
                az.assert_called_once()
                head.assert_called_once_with(ORIGINAL, "private")
                sas.assert_not_called()
                upload.assert_not_called()
                change.assert_not_called()
                self.assertEqual(release.CURRENT_STAGE, "BLOB_OAUTH_READ")


if __name__ == "__main__":
    unittest.main()
