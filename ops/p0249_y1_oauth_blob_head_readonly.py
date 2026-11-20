#!/usr/bin/env python3
"""Issue #249: authenticated, read-only private Blob HEAD without Azure CLI blob parsing.

Only existing isolated DEV Y1, restored original package, exact 2 indexed GETs,
and a unique failed-run Blob path. Never print the token, request URL, SAS,
response bodies, arbitrary response headers, Azure CLI output or identities.
"""
from __future__ import annotations

from email.utils import formatdate
import json
import subprocess
import urllib.error
import urllib.parse
import urllib.request

import p0249_y1_canary_guard as guard
import p0249_y1_remote_build_mode as mode
import p0249_y1_external_private_package as pkg

FAILED_RUN = "44670935079"
BLOB = "p0249-y1-trial/" + FAILED_RUN + "/five-readonly.zip"
STORAGE_AUDIENCE = "https://storage.azure.com/"
VERSION = "2023-11-03"
ERROR_CODES = frozenset((
    "AuthorizationPermissionMismatch", "AuthorizationFailure",
    "AuthenticationFailed", "InvalidAuthenticationInfo",
    "NoAuthenticationInformation", "BlobNotFound", "ContainerNotFound",
    "ResourceNotFound", "PublicAccessNotPermitted", "NetworkAccessDenied",
    "AccountIsDisabled", "ServerBusy", "OperationTimedOut",
))

class NoRedirects(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None

_OPENER = urllib.request.build_opener(NoRedirects())


def acquire_storage_token():
    """OIDC Azure CLI access token, received only in memory."""
    try:
        result = subprocess.run(
            ["az", "account", "get-access-token", "--resource", STORAGE_AUDIENCE,
             "--only-show-errors", "-o", "json"],
            capture_output=True, text=True, check=False, timeout=60,
        )
    except (OSError, subprocess.TimeoutExpired):
        raise RuntimeError("OIDC storage token request unavailable") from None
    if result.returncode:
        raise RuntimeError("OIDC storage token denied (redacted)")
    try:
        payload = json.loads(result.stdout)
    except (TypeError, ValueError):
        raise RuntimeError("OIDC storage token response invalid") from None
    token = payload.get("accessToken") if isinstance(payload, dict) else None
    if not isinstance(token, str) or not 100 < len(token) < 30000:
        raise RuntimeError("No valid OIDC storage token")
    return token


def classify_http(status, error_code=None):
    """Only fixed category names; no arbitrary HTTP headers ever logged."""
    known_code = error_code if error_code in ERROR_CODES else "OTHER_REDACTED"
    if status == 200:
        return "BLOB_EXISTS_OAUTH_READ_ALLOWED", "NONE"
    if status in (301, 302, 303, 307, 308):
        return "REDIRECT_DENIED", known_code
    if status == 404:
        return "BLOB_NOT_FOUND_OR_HIDDEN", known_code
    if status == 403:
        return "OAUTH_OR_NETWORK_FORBIDDEN", known_code
    if status == 401:
        return "OAUTH_UNAUTHENTICATED", known_code
    if status in (408, 429, 500, 502, 503, 504):
        return "TRANSIENT_OR_UPSTREAM", known_code
    return "OTHER_HTTP_STATUS", known_code


def head_existing_failed_blob(container, token):
    """HEAD only to a constant account and failed-run path, never follow 30x."""
    if not isinstance(container, str) or not container or len(container) > 63:
        raise RuntimeError("Original private container invalid")
    if not all(x.islower() or x.isdigit() or x == "-" for x in container):
        raise RuntimeError("Original private container not canonical")
    if not isinstance(token, str) or not token:
        raise RuntimeError("Missing in-memory OIDC token")
    address = ("https://" + guard.STORAGE + ".blob.core.windows.net/"
               + container + "/" + urllib.parse.quote(BLOB, safe="/"))
    request = urllib.request.Request(
        address, method="HEAD",
        headers={"Authorization": "Bearer " + token,
                 "x-ms-date": formatdate(usegmt=True),
                 "x-ms-version": VERSION,
                 "Cache-Control": "no-store"},
    )
    try:
        with _OPENER.open(request, timeout=18) as response:
            return classify_http(response.status, response.headers.get("x-ms-error-code"))
    except urllib.error.HTTPError as exc:
        try:
            return classify_http(exc.code, exc.headers.get("x-ms-error-code"))
        finally:
            exc.close()
    except (urllib.error.URLError, TimeoutError, OSError):
        return "NETWORK_UNAVAILABLE", "NONE"


def main():
    guard.verify()  # Exact DEV Y1, FC1 original unaffected
    print("P0249_OAUTH_BLOB_STAGE=ISOLATED_RESOURCE_VERIFIED", flush=True)
    settings, indexed = mode._settings(), mode._index()
    old, container = pkg.scoped_baseline(settings, indexed)
    if indexed != mode.TWO or settings.get("WEBSITE_RUN_FROM_PACKAGE") != old:
        raise RuntimeError("Original two-route package was not restored")
    print("P0249_OAUTH_BLOB_STAGE=ORIGINAL_PACKAGE_TWO_INDEX_CONFIRMED", flush=True)
    token = acquire_storage_token()
    print("P0249_OAUTH_BLOB_STAGE=STORAGE_OIDC_TOKEN_IN_MEMORY", flush=True)
    outcome, error = head_existing_failed_blob(container, token)
    print("P0249_OAUTH_BLOB_HEAD_RESULT=" + outcome + " CODE=" + error, flush=True)
    guard.probe()  # 20 real original health + unknown requests
    print("P0249_OAUTH_BLOB_ORIGINAL_20OF20=PASS", flush=True)


if __name__ == "__main__":
    try:
        main()
    except Exception:
        print("P0249_OAUTH_BLOB_AUDIT=FAILED_REDACTED_NO_WRITES", flush=True)
        raise SystemExit(2)
