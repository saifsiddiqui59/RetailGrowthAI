"""Existing real API/store classes retain tenant roles and revocation checks.

The HTTP transport emulates PostgREST responses; these tests never contact
Supabase and do not replace the disposable database RLS suite.
"""
import copy
import json
from pathlib import Path
import sys
import unittest
from urllib.parse import parse_qs, urlsplit
from uuid import uuid4

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "azure-functions/campaign-api"))
from http_api import HTTPAPI
from render_api import RenderAPI
from security import AuthenticationError
from tenant_store import TenantStore

SAMPLE = json.loads((ROOT / "frontend/src/features/campaigns/fixtures/sample-campaign.json").read_text())
CID, SID, DID = SAMPLE["id"], SAMPLE["shop_id"], SAMPLE["days"][0]["id"]
JID, OUTPUT = (str(uuid4()) for _ in range(2))
USERS = {role: str(uuid4()) for role in ("OWNER", "EDITOR", "VIEWER", "ROOT", "FOREIGN")}


class Response:
    def __init__(self, body): self.body = body
    def __enter__(self): return self
    def __exit__(self, *args): return False
    def read(self): return json.dumps(self.body).encode()


class UserTransport:
    def __init__(self):
        self.calls = []
        self.day = copy.deepcopy(SAMPLE["days"][0])
        self.active = True
        self.membership_reads = 0
        self.revoke_after = None

    def __call__(self, req, timeout):
        self.calls.append(req)
        role = req.get_header("Authorization").removeprefix("Bearer ")
        path = urlsplit(req.full_url).path
        query = parse_qs(urlsplit(req.full_url).query)
        if path.endswith("/shop_memberships"):
            self.membership_reads += 1
            assert query["shop_id"] == ["eq." + SID]
            assert query["user_id"] == ["eq." + USERS[role]]
            assert query["active"] == ["eq.true"]
            if (self.revoke_after is not None
                    and self.membership_reads > self.revoke_after):
                self.active = False
            return Response([{"role": role}] if self.active and role in ("OWNER", "EDITOR", "VIEWER") else [])
        if path.endswith("/campaigns"):
            return Response([{"id": CID, "shop_id": SID, "status": "DRAFT"}])
        if path.endswith("/campaign_days"):
            return Response([copy.deepcopy(self.day), *copy.deepcopy(SAMPLE["days"][1:])])
        if path.endswith("/render_jobs"):
            return Response([{"id": JID, "shop_id": SID, "status": "SUCCEEDED",
                              "output_asset_id": OUTPUT, "error_code": None}])
        if path.endswith("/media_assets"):
            identity = query.get("id", [""])[0]
            if identity == "eq." + OUTPUT:
                return Response([{"id": OUTPUT, "shop_id": SID, "storage_bucket": "retailgrowth-media",
                                  "object_path": SID + "/renders/output.mp4", "mime_type": "video/mp4"}])
            ids = identity.removeprefix("in.(").removesuffix(")").split(",")
            return Response([{"id": identity} for identity in ids])
        if path.endswith("/rpc/save_campaign_day"):
            assert self.active and role in ("OWNER", "EDITOR")
            value = json.loads(req.data)
            assert value["p_shop_id"] == SID and value["p_day_id"] == DID
            self.day.update(copy.deepcopy(value["p_changes"]))
            return Response(True)
        if path.startswith("/storage/v1/object/sign/"):
            assert self.active and role in ("OWNER", "EDITOR", "VIEWER")
            return Response({"signedURL": path.removeprefix("/storage/v1") + "?token=offline"})
        raise AssertionError("unexpected transport route")


class Admin:
    def __init__(self): self.jobs = []
    def valid_media(self, *args): return True
    def find_render_job(self, shop, digest):
        return next((row for row in self.jobs if row["shop_id"] == shop
                     and row["idempotency_key"] == digest), None)
    def insert_render_job(self, row): self.jobs.append(copy.deepcopy(row))


def application():
    transport = UserTransport()
    users = TenantStore("https://offline.supabase.test", "public-offline-key", transport)
    admin = Admin()

    def verify(token):
        if token not in USERS: raise AuthenticationError("invalid token")
        return USERS[token]

    render = RenderAPI(users, admin, object(), durable_outbox=True)
    return HTTPAPI(verify, users, object(), render, failure_store=admin,
                   durable_outbox=True), transport, admin


class RoleRegressionTests(unittest.TestCase):
    def test_owner_editor_viewer_reads_and_signed_downloads_remain_available(self):
        for role in ("OWNER", "EDITOR", "VIEWER"):
            with self.subTest(role=role):
                app, transport, _ = application()
                self.assertEqual(app.handle("GET", f"/campaigns/{CID}", "Bearer " + role)[0], 200)
                code, body = app.handle("GET", f"/render-jobs/{JID}/download", "Bearer " + role)
                self.assertEqual(code, 200)
                self.assertIn("/object/sign/retailgrowth-media/" + SID + "/", body["url"])
                self.assertTrue(all(req.get_header("Apikey") == "public-offline-key" for req in transport.calls))

    def test_only_owner_and_editor_can_edit_and_reserve_one_logical_render(self):
        for role in ("OWNER", "EDITOR", "VIEWER"):
            with self.subTest(role=role):
                app, transport, admin = application()
                changes = {key: copy.deepcopy(SAMPLE["days"][0][key])
                           for key in ("topic", "linkedin", "instagram")}
                changes["linkedin"]["post_text"] = "A supplied and reviewed message"
                code, _ = app.handle("PATCH", f"/campaigns/{CID}/days/{DID}", "Bearer " + role, changes)
                self.assertEqual(code, 403 if role == "VIEWER" else 200)
                body = {"day_id": DID, "preset": "instagram_reel_30s"}
                first = app.handle("POST", f"/campaigns/{CID}/renders", "Bearer " + role, body)
                second = app.handle("POST", f"/campaigns/{CID}/renders", "Bearer " + role, body)
                if role == "VIEWER":
                    self.assertEqual(first[0], 403)
                    self.assertFalse(admin.jobs)
                    self.assertFalse(any("save_campaign_day" in req.full_url for req in transport.calls))
                else:
                    self.assertEqual(first[0], 202)
                    self.assertEqual(first, second)
                    self.assertEqual(len(admin.jobs), 1)

    def test_global_root_is_not_an_implicit_shop_membership(self):
        for role in ("ROOT", "FOREIGN"):
            app, transport, admin = application()
            self.assertEqual(app.handle("GET", f"/campaigns/{CID}", "Bearer " + role)[0], 404)
            self.assertEqual(app.handle("POST", f"/campaigns/{CID}/renders", "Bearer " + role,
                                        {"day_id": DID, "preset": "instagram_reel_30s"})[0], 404)
            self.assertEqual(app.handle("GET", f"/render-jobs/{JID}/download", "Bearer " + role)[0], 404)
            self.assertFalse(admin.jobs)
            self.assertFalse(any("/object/sign/" in req.full_url for req in transport.calls))

    def test_membership_revocation_after_previous_success_denies_subsequent_download(self):
        app, transport, _ = application()
        self.assertEqual(app.handle("GET", f"/render-jobs/{JID}/download", "Bearer EDITOR")[0], 200)
        signed_before = sum("/object/sign/" in req.full_url for req in transport.calls)
        transport.active = False
        self.assertEqual(app.handle("GET", f"/render-jobs/{JID}/download", "Bearer EDITOR")[0], 404)
        self.assertEqual(sum("/object/sign/" in req.full_url for req in transport.calls), signed_before)

    def test_write_rechecks_role_after_campaign_read_with_no_cached_membership(self):
        app, transport, admin = application()
        transport.revoke_after = 1
        code, _ = app.handle("POST", f"/campaigns/{CID}/renders", "Bearer OWNER",
                             {"day_id": DID, "preset": "instagram_reel_30s"})
        self.assertEqual(code, 403)
        self.assertEqual(transport.membership_reads, 2)
        self.assertFalse(admin.jobs)


if __name__ == "__main__": unittest.main()
