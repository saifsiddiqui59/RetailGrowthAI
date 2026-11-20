"""Offline regressions: read-only Y1 RBAC audit stays redacted and bounded."""
import base64
import json
from pathlib import Path
import os
import sys
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "ops"))
import p0249_y1_private_blob_rbac_audit as a

class AuditTests(unittest.TestCase):
    def test_role_labels_are_aggregated_without_leaking_principal(self):
        r = a.classify_role_list([
            {"roleDefinitionName": "Storage Blob Data Contributor",
             "principalId": "SENSITIVE_DO_NOT_LOG"},
            {"roleDefinitionName": "Reader", "scope": "SENSITIVE_SCOPE"},
        ])
        self.assertTrue(r["visible_blob_data_writer_role"])
        self.assertNotIn("SENSITIVE", json.dumps(r))
        self.assertFalse(a.classify_role_list([
            {"roleDefinitionName": "Contributor"},
            {"roleDefinitionName": "Storage Blob Data Reader"}])["visible_blob_data_writer_role"])
        with self.assertRaises(RuntimeError):
            a.classify_role_list({"wrong": "type"})

    def test_token_claims_are_in_memory_and_match_client_identity(self):
        claims = {"appid": "protected-dev-client", "oid": "11111111-1111-4111-8111-111111111111"}
        data = base64.urlsafe_b64encode(json.dumps(claims).encode()).decode().rstrip("=")
        token = "header." + data + ".signature"
        self.assertEqual(a._service_principal_oid(token, "protected-dev-client"), claims["oid"])
        with self.assertRaises(RuntimeError):
            a._service_principal_oid(token, "other-client")
        with self.assertRaises(RuntimeError):
            a._service_principal_oid("bad", "protected-dev-client")

    def test_storage_scope_is_exact_approved_container_only(self):
        sub = "11111111-1111-4111-8111-111111111111"
        rid = (f"/subscriptions/{sub}/resourceGroups/{a.guard.RG}"
               f"/providers/Microsoft.Storage/storageAccounts/{a.guard.STORAGE}")
        uri = f"https://{a.guard.STORAGE}.blob.core.windows.net/private/code.zip?sig=TOPSECRET"
        self.assertEqual(
            a._scope_and_container(rid, uri, sub),
            rid + "/blobServices/default/containers/private")
        with self.assertRaises(RuntimeError):
            a._scope_and_container(rid, uri.replace(a.guard.STORAGE, "otheraccount"), sub)

    def test_cli_failure_category_never_prints_sensitive_error_bytes(self):
        for raw, expected in (
            ("AuthorizationPermissionMismatch https://private/?sig=SECRET", "ACCESS_DENIED"),
            ("error: unrecognized arguments https://private/?sig=SECRET", "CLI_ARGUMENT"),
            ("InvalidScope?sig=SECRET", "INVALID_OR_MISSING_SCOPE"),
            ("unexpected https://private/?sig=SECRET", "OTHER_REDACTED"),
        ):
            value = a._cli_error_class(raw)
            self.assertEqual(value, expected)
            self.assertNotIn("SECRET", value)
            self.assertNotIn("https", value)

    def test_denied_container_metadata_falls_back_only_to_verified_parent(self):
        import io
        from contextlib import redirect_stdout
        import p0249_y1_remote_build_mode as mode
        sub = "11111111-1111-4111-8111-111111111111"
        client = "22222222-2222-4222-8222-222222222222"
        old = f"https://{a.guard.STORAGE}.blob.core.windows.net/private/old.zip?sig=SECRET"
        settings = {mode.BACKUP: old, "WEBSITE_RUN_FROM_PACKAGE": old}
        resource_id = (f"/subscriptions/{sub}/resourceGroups/{a.guard.RG}"
                       f"/providers/Microsoft.Storage/storageAccounts/{a.guard.STORAGE}")
        with patch.object(a.guard, "verify", return_value=None), \
             patch.object(a.guard, "command", return_value={"id":resource_id}), \
             patch.object(a.mode, "_settings", return_value=settings), \
             patch.object(a.mode, "_index", return_value=mode.TWO), \
             patch.object(a, "_service_principal_oid", return_value="33333333-3333-4333-8333-333333333333"), \
             patch.object(a, "_az_json", side_effect=[{"accessToken":"OPAQUE"}, RuntimeError("redacted"), []]) as azure, \
             patch.dict(os.environ, {"RGAI_DEV_EXPECTED_SUBSCRIPTION":sub,"AZURE_CLIENT_ID":client}):
            output = io.StringIO()
            with redirect_stdout(output):
                a.audit()
        self.assertIn("STORAGE_ACCOUNT_METADATA_FALLBACK", output.getvalue())
        self.assertIn('"scope_class": "STORAGE_ACCOUNT_PARENT_ONLY"', output.getvalue())
        self.assertIn('"container_direct_roles_unverified": true', output.getvalue())
        self.assertNotIn("SECRET", output.getvalue())
        calls = azure.call_args_list
        self.assertEqual(len(calls), 3)
        self.assertTrue(any("/blobServices/default/containers/private" in str(v) for v in calls[1].args))
        self.assertFalse(any("/blobServices/default/containers/private" in str(v) for v in calls[2].args))

    def test_read_only_workflow_and_script_exclude_mutations(self):
        code = (ROOT / "ops/p0249_y1_private_blob_rbac_audit.py").read_text()
        wf = (ROOT / ".github/workflows/p0249-y1-storage-role-readonly-once.yml").read_text()
        self.assertIn("environment: dev", wf)
        self.assertIn("startsWith(github.event.head_commit.message", wf)
        self.assertIn("get-access-token", code)
        self.assertIn("--assignee-object-id", code)
        self.assertIn("original_two_route_and_package_recovery", code)
        labels = ["VERIFIED_RESOURCE_IDENTITY", "VERIFIED_TWO_ROUTE_BASELINE",
                  "VERIFIED_STORAGE_CONTAINER_SCOPE", "VERIFIED_OIDC_CLIENT_CLAIM",
                  "QUERYING_READONLY_ROLE_ASSIGNMENTS"]
        markers = ["P0249_Y1_BLOB_RBAC_STAGE=" + label for label in labels]
        for marker in markers:
            self.assertIn(marker, code)
        self.assertEqual([code.index(marker) for marker in markers],
                         sorted(code.index(marker) for marker in markers))
        self.assertNotIn("print(token)", code)
        self.assertNotIn("print(assignments)", code)
        for unsafe in ("_set(", "blob\", \"upload", "role\", \"assignment\", \"create",
                       "functionapp\", \"config\", \"appsettings\", \"set",
                       "az storage account keys list"):
            self.assertNotIn(unsafe, code)
        for bad in ("workflow_dispatch:", "az functionapp", "az storage blob upload",
                    "run: az role assignment create"):
            self.assertNotIn(bad, wf)

if __name__ == "__main__":
    unittest.main()
