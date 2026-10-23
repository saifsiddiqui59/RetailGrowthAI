"""Offline Part 3 premium HTTP boundary tests: no live Azure, DB or Wan calls."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] /
                       "azure-functions" / "campaign-api"))

from premium_http import PremiumHTTPBoundary
from security import AuthenticationError
from tenant_store import StorageUnavailable

UID = "123e4567-e89b-42d3-a456-426614174001"
SID = "123e4567-e89b-42d3-a456-426614174002"
CID = "123e4567-e89b-42d3-a456-426614174003"
JID = "123e4567-e89b-42d3-a456-426614174004"
ASSET = "123e4567-e89b-42d3-a456-426614174005"
LEASE = "123e4567-e89b-42d3-a456-426614174006"
OUTPUT = f"{SID}/renders/{JID}/{LEASE}.mp4"


class Coordinator:
    def __init__(self):
        self.calls = []

    def create(self, token, user, campaign, body):
        self.calls.append(("create", token, user, campaign, body))
        return 202, {"job_id": JID, "status": "QUEUED"}

    def status(self, token, user, job_id):
        self.calls.append(("status", token, user, job_id))
        return 200, {"job_id": JID, "status": "PENDING"}


class Store:
    def __init__(self):
        self.rows = {JID: {"id": JID, "shop_id": SID,
                           "status": "SUCCEEDED", "output_asset_id": ASSET}}
        self.calls = []

    def get_authenticated(self, token, job_id):
        self.calls.append(("job", token, job_id))
        return self.rows.get(job_id)


class Users:
    def __init__(self):
        self.can_read = True
        self.allowed_asset = True
        self.asset_overrides = {}
        self.signs = []

    def member(self, token, user, shop):
        return self.can_read and token == "valid-user-jwt" and user == UID and shop == SID

    def asset(self, token, sid, asset):
        assert token == "valid-user-jwt"
        if not self.allowed_asset:
            return None
        return dict({"id": ASSET, "shop_id": SID,
                     "storage_bucket": "retailgrowth-media",
                     "object_path": OUTPUT, "mime_type": "video/mp4"},
                    **self.asset_overrides)

    def sign_download(self, token, shop_id, object_path):
        self.signs.append((token, shop_id, object_path))
        return "https://signed.test.invalid/storage/v1/object/sign/" + object_path + "?token=mock"


def auth(token):
    if token == "valid-user-jwt":
        return UID
    raise AuthenticationError("Untrusted test bearer")


def fixture(enabled=True):
    users, store, controller = Users(), Store(), Coordinator()
    api = PremiumHTTPBoundary(auth, users, store, controller, enabled=enabled)
    return api, users, store, controller


def test_default_disabled_and_missing_bearer_fail_before_any_job_or_download():
    api, users, store, controller = fixture(enabled=False)
    endpoint = f"/premium-video-jobs/{JID}/download"
    assert api.handle("GET", endpoint, "Bearer valid-user-jwt") == (
        503, {"error": "PREMIUM_VIDEO_DISABLED"})
    for bad in ("", "invalid", "Bearer ", "Bearer forged"):
        assert api.handle("GET", endpoint, bad)[0] == 401
    assert not users.signs and not store.calls and not controller.calls


def test_valid_authenticated_creation_and_status_does_not_leak_task_id():
    api, users, store, controller = fixture()
    body = {"mode": "text", "day_id": CID, "resolution": "720P",
            "duration_seconds": 5, "input_asset_id": None}
    assert api.handle("POST", f"/campaigns/{CID}/premium-videos",
                      "Bearer valid-user-jwt", body) == (
        202, {"job_id": JID, "status": "QUEUED"})
    assert controller.calls[-1] == ("create", "valid-user-jwt", UID, CID, body)
    assert api.handle("GET", f"/premium-video-jobs/{JID}",
                      "Bearer valid-user-jwt") == (
        200, {"job_id": JID, "status": "PENDING"})
    assert not users.signs


def test_private_download_issues_only_rls_scoped_signed_retailgrowth_link():
    api, users, store, controller = fixture()
    assert api.handle("GET", f"/premium-video-jobs/{JID}/download",
                      "Bearer valid-user-jwt") == (
        200, {"url": "https://signed.test.invalid/storage/v1/object/sign/" +
              OUTPUT + "?token=mock"})
    assert users.signs == [("valid-user-jwt", SID, OUTPUT)]
    assert controller.calls == []


def test_foreign_job_or_revoked_shop_role_is_404_and_never_signs():
    api, users, store, controller = fixture()
    users.can_read = False
    assert api.handle("GET", f"/premium-video-jobs/{JID}/download",
                      "Bearer valid-user-jwt") == (404, {"error": "NOT_FOUND"})
    assert not users.signs
    users.can_read = True
    store.rows[JID] = {"id": JID, "shop_id": SID, "status": "SUCCEEDED",
                       "output_asset_id": None}
    assert api.handle("GET", f"/premium-video-jobs/{JID}/download",
                      "Bearer valid-user-jwt")[0] == 409
    assert not users.signs


def test_pending_task_cannot_be_downloaded():
    api, users, store, controller = fixture()
    store.rows[JID]["status"] = "IMPORTING"
    assert api.handle("GET", f"/premium-video-jobs/{JID}/download",
                      "Bearer valid-user-jwt") == (
        409, {"error": "OUTPUT_NOT_READY"})
    assert users.signs == []


def test_foreign_or_malformed_asset_receipt_never_signs():
    changes = [
        {"object_path": SID + "/renders/other-job/" + LEASE + ".mp4"},
        {"object_path": SID + "/renders/" + JID + "/../../other.mp4"},
        {"object_path": OUTPUT + "?evil=true"},
        {"object_path": OUTPUT.replace(".mp4", ".MP4")},
        {"object_path": SID + "/renders/" + JID + "/not-a-uuid.mp4"},
        {"mime_type": "image/png"},
        {"storage_bucket": "public-media"},
        {"shop_id": "123e4567-e89b-42d3-a456-426614174007"},
        {"id": "123e4567-e89b-42d3-a456-426614174007"},
    ]
    for override in changes:
        api, users, store, controller = fixture()
        users.asset_overrides = override
        code, response = api.handle(
            "GET", f"/premium-video-jobs/{JID}/download", "Bearer valid-user-jwt")
        assert code == 404, (override, response)
        assert users.signs == []


def test_no_untrusted_query_or_http_method_can_trigger_creation_or_download():
    api, users, store, controller = fixture()
    for method, path in [
        ("POST", f"/premium-video-jobs/{JID}/download"),
        ("GET", f"/premium-video-jobs/{JID}/download?token=stolen"),
        ("GET", f"/campaigns/{CID}/premium-videos"),
        ("POST", f"/campaigns/{CID}/premium-videos?paid=true"),
        ("GET", f"/premium-video-jobs/{JID}/unknown"),
    ]:
        assert api.handle(method, path, "Bearer valid-user-jwt")[0] == 404
    assert controller.calls == [] and users.signs == []


def test_malformed_identifiers_and_signed_media_store_failure_are_sanitized():
    api, users, store, controller = fixture()
    assert api.handle("GET", "/premium-video-jobs/../../secrets",
                      "Bearer valid-user-jwt")[0] == 404
    assert api.handle("GET", "/premium-video-jobs/not-a-uuid",
                      "Bearer valid-user-jwt")[0] == 400

    def unavailable(*args):
        raise StorageUnavailable("private provider URL and secret")
    users.sign_download = unavailable
    code, payload = api.handle("GET", f"/premium-video-jobs/{JID}/download",
                               "Bearer valid-user-jwt")
    assert code == 503 and payload == {"error": "SERVICE_UNAVAILABLE"}
