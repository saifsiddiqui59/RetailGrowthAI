"""CPU F2-approved plan render: JWT, RLS, immutable SHA, download gates.

All stores here are SIMULATED. Live DB/source/queue correctness comes only
after isolated SQL tests and deployed two-shop signed DEV E2E acceptance.
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "azure-functions" / "campaign-api"))
sys.path.insert(0, str(ROOT / "video-engine"))
from feature4_plan_review_api import Feature4CpuRenderAPI  # noqa: E402
from http_api import HTTPAPI  # noqa: E402
from security import AuthenticationError  # noqa: E402
from tenant_store import StorageUnavailable, SubscriptionDenied  # noqa: E402

SHOP = "11111111-1111-4111-8111-111111111111"
FOREIGN = "44444444-4444-4444-8444-444444444444"
USER = "77777777-7777-4777-8777-777777777777"
CAMPAIGN = "22222222-2222-4222-8222-222222222222"
PLAN = "99999999-9999-4999-8999-999999999999"
JOB = "33333333-3333-4333-8333-333333333333"
LEASE = "55555555-5555-4555-8555-555555555555"
ASSET = "66666666-6666-4666-8666-666666666666"
MEDIA = "aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa"
HASH = "a" * 64


class FakeRLS:
    def __init__(self):
        self.accept = True
        self.editor = True
        self.revoked = False
        self.rights_revoked = False
        self.quota_denied = False
        self.jobs = 0
        self.signs = []
        self.plan = {
            "id": PLAN, "shop_id": SHOP, "campaign_id": CAMPAIGN,
            "state": "APPROVED", "review_sha256": HASH,
            "media_snapshot": [{
                "id": MEDIA, "shop_id": SHOP, "path": f"{SHOP}/uploads/{MEDIA}.png",
                "mime": "image/png", "source": "UPLOAD", "license": "owned"
            }],
        }
        self.job = {
            "id": JOB, "shop_id": SHOP, "campaign_id": CAMPAIGN,
            "plan_id": PLAN, "approved_review_sha256": HASH,
            "status": "QUEUED", "output_asset_id": None,
        }

    def campaign(self, token, user_id, campaign_id):
        if token == "shop-user" and user_id == USER and campaign_id == CAMPAIGN:
            return {"id": CAMPAIGN, "shop_id": SHOP}
        return None

    def member(self, token, user_id, shop_id, *, write=False):
        return (token == "shop-user" and user_id == USER
                and shop_id == SHOP and self.accept
                and (not write or self.editor))

    def feature4_creative_plan(self, token, user_id, plan_id):
        if plan_id != PLAN or not self.member(token, user_id, SHOP):
            return None
        return {**self.plan, "state": "REVOKED" if self.revoked else "APPROVED"}

    def feature4_submit_cpu_render(self, token, plan_id, digest):
        if self.quota_denied:
            raise SubscriptionDenied("RG002")
        if self.rights_revoked:
            return None
        if token != "shop-user" or plan_id != PLAN or digest != HASH:
            return None
        self.jobs += 1
        return {"id": JOB, "job_id": JOB, "shop_id": SHOP, "status": "QUEUED"}

    def feature4_job(self, token, user_id, job_id):
        if job_id != JOB or not self.member(token, user_id, SHOP):
            return None
        return self.job

    def feature4_media(self, token, shop_id, asset_id):
        if token != "shop-user" or shop_id != SHOP:
            return None
        if asset_id == MEDIA:
            return {
                "shop_id": SHOP, "storage_bucket": "retailgrowth-media",
                "object_path": f"{SHOP}/uploads/{MEDIA}.png",
                "mime_type": "image/png", "source": "UPLOAD",
                "license_name": "unlicensed" if self.rights_revoked else "owned",
            }
        if asset_id == ASSET:
            return {
                "shop_id": SHOP, "storage_bucket": "retailgrowth-media",
                "object_path": f"{SHOP}/renders/{JOB}/{LEASE}.mp4",
                "mime_type": "video/mp4", "source": "GENERATED",
                "license_name": "owned",
            }
        return None

    def sign_download(self, token, shop_id, key):
        self.signs.append((token, shop_id, key))
        return "https://example.supabase.co/storage/v1/object/sign/retailgrowth-media/" + key + "?token=private"


def verify(token):
    if token == "shop-user":
        return USER
    if token == "shop-foreign":
        return FOREIGN
    raise AuthenticationError("bad signature")


def setup():
    user = FakeRLS()
    return HTTPAPI(verify, user, feature4_api=Feature4CpuRenderAPI(user)), user


def request():
    return {"plan_id": PLAN, "expected_review_hash": HASH}


def test_real_http_boundary_for_approved_plan_cpu_job_then_rls_status():
    api, user = setup()
    url = f"/campaigns/{CAMPAIGN}/feature4-renders"
    status, receipt = api.handle("POST", url, "Bearer shop-user", request())
    assert status == 202 and receipt == {
        "shop_id": SHOP, "job_id": JOB, "status": "QUEUED"}
    assert user.jobs == 1
    assert api.handle("GET", f"/feature4-render-jobs/{JOB}",
                      "Bearer shop-user") == (200, receipt)
    assert api.handle("GET", f"/feature4-render-jobs/{JOB}/download",
                      "Bearer shop-user") == (409, {"error": "OUTPUT_NOT_READY"})


def test_no_browser_script_approval_foreign_jwt_or_viewer_spending():
    api, user = setup()
    url = f"/campaigns/{CAMPAIGN}/feature4-renders"
    assert api.handle("POST", url, "Bearer forged", request())[0] == 401
    assert api.handle("POST", url, "Bearer shop-foreign", request())[0] == 404
    assert api.handle("POST", url, "Bearer shop-user", {
        **request(), "draft": {"approved": True}})[0] == 400
    assert api.handle("POST", url, "Bearer shop-user", {
        **request(), "expected_review_hash": "0"*64})[0] == 409
    user.editor = False
    assert api.handle("POST", url, "Bearer shop-user", request())[0] == 409
    user.editor = True
    user.accept = False
    assert api.handle("POST", url, "Bearer shop-user", request())[0] == 404
    assert user.jobs == 0 and not user.signs


def test_current_plan_revoke_quota_and_source_rights_fail_before_job():
    api, user = setup()
    url = f"/campaigns/{CAMPAIGN}/feature4-renders"
    user.revoked = True
    assert api.handle("POST", url, "Bearer shop-user", request())[0] == 409
    user.revoked = False
    user.rights_revoked = True
    assert api.handle("POST", url, "Bearer shop-user", request())[0] == 409
    user.rights_revoked = False
    user.quota_denied = True
    assert api.handle("POST", url, "Bearer shop-user", request()) == (
        429, {"error": "QUOTA_EXCEEDED"})
    assert user.jobs == 0


def test_private_mp4_rechecks_current_source_and_reviewer_after_completion():
    api, user = setup()
    user.job["status"] = "SUCCEEDED"
    user.job["output_asset_id"] = ASSET
    url = f"/feature4-render-jobs/{JOB}/download"
    status, signed = api.handle("GET", url, "Bearer shop-user")
    assert status == 200
    assert signed["job_id"] == JOB and signed["shop_id"] == SHOP
    assert signed["url"].endswith("?token=private")
    assert len(user.signs) == 1
    user.revoked = True
    assert api.handle("GET", url, "Bearer shop-user")[0] == 404
    user.revoked = False
    user.rights_revoked = True
    assert api.handle("GET", url, "Bearer shop-user") == (
        404, {"error": "SOURCE_RIGHTS_REVOKED"})
    user.rights_revoked = False
    user.job["approved_review_sha256"] = "0"*64
    assert api.handle("GET", url, "Bearer shop-user")[0] == 404
    assert len(user.signs) == 1


def test_unregistered_api_never_bills_and_pending_worker_remains_off():
    api = HTTPAPI(verify, FakeRLS())
    assert api.handle("POST", f"/campaigns/{CAMPAIGN}/feature4-renders",
                      "Bearer shop-user", request()) == (
        503, {"error": "FEATURE4_V2_DISABLED"})
    assert api.handle("GET", f"/feature4-render-jobs/{JOB}",
                      "Bearer shop-user") == (
        503, {"error": "FEATURE4_V2_DISABLED"})
