#!/usr/bin/env python3
"""Read-only, redacted Azure Y1 private-Blob upload RBAC audit for issue #249.

Never prints principals, access tokens, package URLs, SAS, scopes or raw CLI
errors. RBAC inventory is diagnostic only, not proof of successful data writes.
"""
from __future__ import annotations

import base64
import json
import os
import subprocess
from urllib.parse import urlsplit

import p0249_y1_canary_guard as guard
import p0249_y1_remote_build_mode as mode

WRITE_ROLES = frozenset(("Storage Blob Data Contributor", "Storage Blob Data Owner"))
BACKUP = mode.BACKUP
PACKAGE = "WEBSITE_RUN_FROM_PACKAGE"


def _az_json(*args):
    """Only known, read-only Azure calls; stdout/stderr never printed."""
    allowed = (
        ("account", "get-access-token"),
        ("role", "assignment", "list"),
    )
    if not any(tuple(args[:len(prefix)]) == prefix for prefix in allowed):
        raise RuntimeError("Unapproved read-only Azure diagnostic operation")
    try:
        process = subprocess.run(
            ["az", *args, "--only-show-errors", "-o", "json"],
            capture_output=True, text=True, timeout=95, check=False,
        )
    except (OSError, subprocess.TimeoutExpired):
        raise RuntimeError("Read-only Azure diagnostic unavailable") from None
    if process.returncode:
        raise RuntimeError("Read-only Azure diagnostic denied (redacted)")
    try:
        return json.loads(process.stdout)
    except (TypeError, ValueError):
        raise RuntimeError("Read-only Azure diagnostic response invalid") from None


def _service_principal_oid(access_token, client_id):
    """Read ARM-token claims in memory; never log or persist the bearer token."""
    if not isinstance(access_token, str) or access_token.count(".") != 2:
        raise RuntimeError("ARM token shape unavailable")
    try:
        middle = access_token.split(".")[1]
        claims = json.loads(base64.urlsafe_b64decode(middle + "=" * (-len(middle) % 4)))
    except (ValueError, UnicodeError):
        raise RuntimeError("ARM token claims unreadable") from None
    if not isinstance(claims, dict):
        raise RuntimeError("ARM claims missing")
    appid = claims.get("appid") or claims.get("azp")
    oid = claims.get("oid")
    if appid != client_id or not isinstance(oid, str) or len(oid) != 36:
        raise RuntimeError("OIDC identity differs from protected DEV client")
    return oid


def _scope_and_container(storage_id, original_uri, expected_subscription):
    base = (f"/subscriptions/{expected_subscription}/resourceGroups/{guard.RG}"
            f"/providers/Microsoft.Storage/storageAccounts/{guard.STORAGE}")
    if not isinstance(storage_id, str) or storage_id.lower() != base.lower():
        raise RuntimeError("Storage resource scope mismatch")
    try:
        uri = urlsplit(original_uri)
    except (TypeError, ValueError):
        raise RuntimeError("Original package reference malformed") from None
    if (uri.scheme != "https" or
        uri.hostname != guard.STORAGE + ".blob.core.windows.net" or
        not isinstance(uri.path, str)):
        raise RuntimeError("Original package account differs from protected DEV storage")
    container = uri.path.strip("/").split("/", 1)[0]
    if not container or len(container) > 63 or not all(c.islower() or c.isdigit() or c == "-" for c in container):
        raise RuntimeError("Original package container invalid")
    return base + "/blobServices/default/containers/" + container


def classify_role_list(assignments):
    """Visible builtin data-plane write roles only; custom/deny remain unknown."""
    if not isinstance(assignments, list) or any(not isinstance(v, dict) for v in assignments):
        raise RuntimeError("RBAC inventory invalid")
    names = {row.get("roleDefinitionName") for row in assignments
             if isinstance(row.get("roleDefinitionName"), str)}
    return {
        "visible_blob_data_writer_role": bool(names & WRITE_ROLES),
        "visible_blob_reader_role": "Storage Blob Data Reader" in names,
        "rbac_metadata_only": True,
        "custom_roles_and_deny_assignments_not_verified": True,
    }


def audit():
    guard.verify()  # Protected exact DEV resource, Y1 SKU and original Flex.
    print("P0249_Y1_BLOB_RBAC_STAGE=VERIFIED_RESOURCE_IDENTITY", flush=True)
    settings = mode._settings()
    indexed = mode._index()
    original = settings.get(BACKUP)
    if (indexed != mode.TWO or
        not mode._package_url(original) or
        settings.get(PACKAGE) != original or
        any(name in settings for name in mode.SHADOWS)):
        raise RuntimeError("Y1 original package/2-route recovery not verified")
    print("P0249_Y1_BLOB_RBAC_STAGE=VERIFIED_TWO_ROUTE_BASELINE", flush=True)

    sub = os.environ.get("RGAI_DEV_EXPECTED_SUBSCRIPTION", "")
    client_id = os.environ.get("AZURE_CLIENT_ID", "")
    if not sub or not client_id:
        raise RuntimeError("Protected DEV identity inputs missing")
    # Reuse the already-guarded existing storage only. No new resource.
    account = guard.command("storage", "account", "show",
                            "-g", guard.RG, "-n", guard.STORAGE)
    storage_id = account.get("id") if isinstance(account, dict) else None
    scope = _scope_and_container(storage_id, original, sub)
    print("P0249_Y1_BLOB_RBAC_STAGE=VERIFIED_STORAGE_CONTAINER_SCOPE", flush=True)

    token = _az_json("account", "get-access-token", "--resource-type", "arm")
    oid = _service_principal_oid(token.get("accessToken") if isinstance(token, dict) else None,
                                 client_id)
    print("P0249_Y1_BLOB_RBAC_STAGE=VERIFIED_OIDC_CLIENT_CLAIM", flush=True)
    print("P0249_Y1_BLOB_RBAC_STAGE=QUERYING_READONLY_ROLE_ASSIGNMENTS", flush=True)
    assignments = _az_json("role", "assignment", "list",
                           "--assignee-object-id", oid, "--scope", scope,
                           "--include-inherited", "--all",
                           "--fill-principal-name", "false")
    result = classify_role_list(assignments)
    result["original_two_route_and_package_recovery"] = True
    print("P0249_Y1_REDACTED_BLOB_RBAC_AUDIT=" + json.dumps(result, sort_keys=True),
          flush=True)


if __name__ == "__main__":
    try:
        audit()
    except Exception:
        print("P0249_Y1_REDACTED_BLOB_RBAC_AUDIT=INCONCLUSIVE_NO_AZURE_WRITES",
              flush=True)
        raise SystemExit(2)
